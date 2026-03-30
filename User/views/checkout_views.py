from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods
from django.db import transaction
from django.conf import settings
from User.models import Cart, CartItems, Address, Order, OrderItem
from User.forms import AddressForm
import razorpay
import json


# Initialize Razorpay client
razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))


@login_required
@never_cache
def checkout(request):
    """Render checkout page with addresses and cart summary"""
    try:
        cart = Cart.objects.get(user=request.user)
        cart_items = cart.items.select_related('product', 'varient').all()
        
        if not cart_items.exists():
            messages.warning(request, "Your cart is empty")
            return redirect('cart')
            
    except Cart.DoesNotExist:
        messages.warning(request, "Your cart is empty")
        return redirect('cart')

    # Get user addresses ordered by default status
    addresses = Address.objects.filter(user=request.user).order_by('-is_default', '-id')
    form = AddressForm()
    
    # Get or create wallet
    from User.models import Wallet
    wallet, _ = Wallet.objects.get_or_create(user=request.user)
    
    context = {
        'cart': cart,
        'cart_items': cart_items,
        'total': cart.get_total(),
        'addresses': addresses,
        'form': form,
        'razorpay_key_id': settings.RAZORPAY_KEY_ID,
        'wallet': wallet,
    }
    return render(request, 'checkout.html', context)


@login_required
@never_cache
@require_http_methods(["POST"])
def add_address(request):
    """Add new address via AJAX"""
    form = AddressForm(request.POST)
    
    if form.is_valid():
        try:
            address = form.save(commit=False)
            address.user = request.user
            
            # If this is set as default, unset other defaults
            if address.is_default:
                Address.objects.filter(user=request.user, is_default=True).update(is_default=False)
            
            address.save()
            
            return JsonResponse({
                'success': True, 
                'message': 'Address added successfully',
                'address_id': address.id
            })
        except Exception as e:
            return JsonResponse({
                'success': False, 
                'message': f'Error saving address: {str(e)}'
            }, status=500)
    else:
        # Format errors for better display
        errors = {}
        for field, error_list in form.errors.items():
            errors[field] = [str(error) for error in error_list]
        
        return JsonResponse({
            'success': False, 
            'message': 'Please correct the errors below',
            'errors': errors
        }, status=400)


@login_required
@never_cache
@require_http_methods(["POST"])
def place_order(request):
    """Place order with COD"""
    address_id = request.POST.get('address_id')
    
    if not address_id:
        return JsonResponse({
            'success': False, 
            'message': 'Please select a delivery address'
        }, status=400)
    
    try:
        # Validate address belongs to user
        address = get_object_or_404(Address, id=address_id, user=request.user)
        
        # Get cart with items
        cart = Cart.objects.select_related('user').prefetch_related(
            'items__product', 
            'items__varient'
        ).get(user=request.user)
        
        cart_items = cart.items.all()
        
        if not cart_items.exists():
            return JsonResponse({
                'success': False, 
                'message': 'Your cart is empty'
            }, status=400)
        
        # Validate stock availability before placing order
        for item in cart_items:
            available_stock = item.varient.stock if item.varient else item.product.available_quantity
            
            if available_stock < item.quantity:
                product_name = item.product.title
                variant_info = f" ({item.varient.variant_type})" if item.varient else ""
                return JsonResponse({
                    'success': False, 
                    'message': f'Insufficient stock for {product_name}{variant_info}. Only {available_stock} available.'
                }, status=400)
        
        # Use transaction to ensure atomicity
        with transaction.atomic():
            # Calculate total
            total_amount = cart.get_total()
            
            # Create Order
            order = Order.objects.create(
                user=request.user,
                address=address,
                total_amount=total_amount,
                payment_method='COD',
                payment_status='Pending',
                status='Pending'
            )
            
            # Create Order Items and Update Stock
            for item in cart_items:
                price = item.get_price()
                
                # Create order item
                OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    variant=item.varient,
                    quantity=item.quantity,
                    price=price
                )
                
                # Decrease stock atomically
                if item.varient:
                    item.varient.stock -= item.quantity
                    item.varient.save(update_fields=['stock'])
                else:
                    item.product.available_quantity -= item.quantity
                    item.product.save(update_fields=['available_quantity'])
            
            # Clear cart after successful order
            cart_items.delete()
        
        return JsonResponse({
            'success': True, 
            'message': 'Order placed successfully!',
            'order_id': order.id
        })
        
    except Cart.DoesNotExist:
        return JsonResponse({
            'success': False, 
            'message': 'Cart not found'
        }, status=404)
        
    except Address.DoesNotExist:
        return JsonResponse({
            'success': False, 
            'message': 'Invalid address selected'
        }, status=404)
        
    except Exception as e:
        return JsonResponse({
            'success': False, 
            'message': f'An error occurred while placing your order: {str(e)}'
        }, status=500)


@login_required
@never_cache
@require_http_methods(["POST"])
def create_razorpay_order(request):
    """Create a Razorpay order and a pending Order in DB"""
    try:
        data = json.loads(request.body)
        address_id = data.get('address_id')
    except (json.JSONDecodeError, AttributeError):
        address_id = request.POST.get('address_id')
    
    if not address_id:
        return JsonResponse({
            'success': False, 
            'message': 'Please select a delivery address'
        }, status=400)
    
    try:
        # Validate address belongs to user
        address = get_object_or_404(Address, id=address_id, user=request.user)
        
        # Get cart with items
        cart = Cart.objects.select_related('user').prefetch_related(
            'items__product', 
            'items__varient'
        ).get(user=request.user)
        
        cart_items = cart.items.all()
        
        if not cart_items.exists():
            return JsonResponse({
                'success': False, 
                'message': 'Your cart is empty'
            }, status=400)
        
        # Validate stock availability
        for item in cart_items:
            available_stock = item.varient.stock if item.varient else item.product.available_quantity
            
            if available_stock < item.quantity:
                product_name = item.product.title
                variant_info = f" ({item.varient.variant_type})" if item.varient else ""
                return JsonResponse({
                    'success': False, 
                    'message': f'Insufficient stock for {product_name}{variant_info}. Only {available_stock} available.'
                }, status=400)
        
        # Create Order + OrderItems + deduct stock inside a transaction
        with transaction.atomic():
            total_amount = cart.get_total()
            
            # Create Order with Payment Pending status
            order = Order.objects.create(
                user=request.user,
                address=address,
                total_amount=total_amount,
                payment_method='Razorpay',
                payment_status='Payment Pending',
                status='Pending'
            )
            
            # Create Order Items and deduct stock
            for item in cart_items:
                price = item.get_price()
                
                OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    variant=item.varient,
                    quantity=item.quantity,
                    price=price
                )
                
                if item.varient:
                    item.varient.stock -= item.quantity
                    item.varient.save(update_fields=['stock'])
                else:
                    item.product.available_quantity -= item.quantity
                    item.product.save(update_fields=['available_quantity'])
            
            # Clear cart
            cart_items.delete()
        
        # Create Razorpay order
        amount_in_paise = int(total_amount * 100)
        razorpay_order = razorpay_client.order.create({
            'amount': amount_in_paise,
            'currency': 'INR',
            'receipt': f'order_{order.id}',
        })
        
        # Save Razorpay order ID on our Order
        order.razorpay_order_id = razorpay_order['id']
        order.save(update_fields=['razorpay_order_id'])
        
        return JsonResponse({
            'success': True,
            'razorpay_order_id': razorpay_order['id'],
            'amount': amount_in_paise,
            'currency': 'INR',
            'key_id': settings.RAZORPAY_KEY_ID,
            'order_id': order.id,
            'user_name': f'{request.user.first_name} {request.user.last_name}',
            'user_email': request.user.email,
            'user_phone': request.user.mobile or '',
        })
        
    except Cart.DoesNotExist:
        return JsonResponse({
            'success': False, 
            'message': 'Cart not found'
        }, status=404)
        
    except Exception as e:
        return JsonResponse({
            'success': False, 
            'message': f'Error creating order: {str(e)}'
        }, status=500)


@login_required
@never_cache
@require_http_methods(["POST"])
def place_wallet_order(request):
    """Place an order and pay directly from user's internal Wallet"""
    address_id = request.POST.get('address_id')
    
    if not address_id:
        return JsonResponse({
            'success': False, 
            'message': 'Please select a delivery address'
        }, status=400)
    
    try:
        from User.models import Wallet
        # Validate address belongs to user
        address = get_object_or_404(Address, id=address_id, user=request.user)
        
        # Get cart with items
        cart = Cart.objects.select_related('user').prefetch_related(
            'items__product', 
            'items__varient'
        ).get(user=request.user)
        
        cart_items = cart.items.all()
        
        if not cart_items.exists():
            return JsonResponse({'success': False, 'message': 'Your cart is empty'}, status=400)
            
        total_amount = cart.get_total()
        
        # Verify wallet balance
        wallet, _ = Wallet.objects.get_or_create(user=request.user)
        if wallet.balance < total_amount:
            return JsonResponse({
                'success': False, 
                'message': 'Insufficient Wallet Balance'
            }, status=400)
        
        # Validate stock availability
        for item in cart_items:
            available_stock = item.varient.stock if item.varient else item.product.available_quantity
            
            if available_stock < item.quantity:
                product_name = item.product.title
                variant_info = f" ({item.varient.variant_type})" if item.varient else ""
                return JsonResponse({
                    'success': False, 
                    'message': f'Insufficient stock for {product_name}{variant_info}. Only {available_stock} available.'
                }, status=400)
        
        # Use transaction to ensure atomicity
        with transaction.atomic():
            # Deduct from Wallet
            wallet_success = wallet.debit(total_amount, "Order Payment via Wallet")
            if not wallet_success:
                raise Exception("Failed to deduct from wallet balance.")
                
            # Create Order
            order = Order.objects.create(
                user=request.user,
                address=address,
                total_amount=total_amount,
                payment_method='Wallet',
                payment_status='Paid',
                status='Pending'
            )
            
            # Label the transaction with order
            wallet_tx = wallet.transactions.last()
            if wallet_tx:
                wallet_tx.order = order
                wallet_tx.save()
            
            # Create Order Items and Update Stock
            for item in cart_items:
                price = item.get_price()
                
                # Create order item
                OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    variant=item.varient,
                    quantity=item.quantity,
                    price=price
                )
                
                # Decrease stock atomically
                if item.varient:
                    item.varient.stock -= item.quantity
                    item.varient.save(update_fields=['stock'])
                else:
                    item.product.available_quantity -= item.quantity
                    item.product.save(update_fields=['available_quantity'])
            
            # Clear cart after successful order
            cart_items.delete()
        
        return JsonResponse({
            'success': True, 
            'message': 'Order successfully placed using Wallet!',
            'order_id': order.id
        })
        
    except Cart.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Cart not found'}, status=404)
        
    except Address.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Invalid address selected'}, status=404)
        
    except Exception as e:
        return JsonResponse({
            'success': False, 
            'message': f'An error occurred: {str(e)}'
        }, status=500)


@login_required
@never_cache
@require_http_methods(["POST"])
def verify_razorpay_payment(request):
    """Verify Razorpay payment signature and update order status"""
    try:
        data = json.loads(request.body)
        razorpay_order_id = data.get('razorpay_order_id')
        razorpay_payment_id = data.get('razorpay_payment_id')
        razorpay_signature = data.get('razorpay_signature')
        order_id = data.get('order_id')
    except (json.JSONDecodeError, AttributeError):
        return JsonResponse({
            'success': False,
            'message': 'Invalid request data'
        }, status=400)
    
    if not all([razorpay_order_id, razorpay_payment_id, razorpay_signature, order_id]):
        return JsonResponse({
            'success': False,
            'message': 'Missing payment details'
        }, status=400)
    
    try:
        # Fetch the order
        order = get_object_or_404(Order, id=order_id, user=request.user)
        
        # Verify payment signature
        params_dict = {
            'razorpay_order_id': razorpay_order_id,
            'razorpay_payment_id': razorpay_payment_id,
            'razorpay_signature': razorpay_signature,
        }
        
        razorpay_client.utility.verify_payment_signature(params_dict)
        
        # Signature verified — update the order
        order.razorpay_payment_id = razorpay_payment_id
        order.razorpay_signature = razorpay_signature
        order.payment_status = 'Paid'
        order.save(update_fields=['razorpay_payment_id', 'razorpay_signature', 'payment_status'])
        
        return JsonResponse({
            'success': True,
            'message': 'Payment verified successfully!',
            'order_id': order.id
        })
        
    except razorpay.errors.SignatureVerificationError:
        # Signature verification failed
        if order_id:
            try:
                order = Order.objects.get(id=order_id, user=request.user)
                order.payment_status = 'Failed'
                order.save(update_fields=['payment_status'])
            except Order.DoesNotExist:
                pass
        
        return JsonResponse({
            'success': False,
            'message': 'Payment verification failed. Please try again.'
        }, status=400)
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error verifying payment: {str(e)}'
        }, status=500)


@login_required
@never_cache
@require_http_methods(["POST"])
def retry_payment(request, order_id):
    """Return existing Razorpay order details for payment retry"""
    try:
        order = get_object_or_404(
            Order, 
            id=order_id, 
            user=request.user, 
            payment_method='Razorpay'
        )
        
        # Only allow retry for Payment Pending or Failed orders
        if order.payment_status not in ['Payment Pending', 'Failed']:
            return JsonResponse({
                'success': False,
                'message': 'Payment retry is not available for this order.'
            }, status=400)
        
        if not order.razorpay_order_id:
            return JsonResponse({
                'success': False,
                'message': 'No Razorpay order found. Please contact support.'
            }, status=400)
        
        # Return the same Razorpay order ID for retry
        amount_in_paise = int(order.total_amount * 100)
        
        return JsonResponse({
            'success': True,
            'razorpay_order_id': order.razorpay_order_id,
            'amount': amount_in_paise,
            'currency': 'INR',
            'key_id': settings.RAZORPAY_KEY_ID,
            'order_id': order.id,
            'user_name': f'{request.user.first_name} {request.user.last_name}',
            'user_email': request.user.email,
            'user_phone': request.user.mobile or '',
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error: {str(e)}'
        }, status=500)


@login_required
@never_cache
def order_success(request, order_id):
    """Render order success page"""
    order = get_object_or_404(
        Order.objects.select_related('address', 'user').prefetch_related('items__product', 'items__variant'),
        id=order_id, 
        user=request.user
    )
    
    context = {
        'order': order,
        'order_items': order.items.all()
    }
    
    return render(request, 'order_success.html', context)