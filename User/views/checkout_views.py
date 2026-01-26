from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods
from django.db import transaction
from User.models import Cart, CartItems, Address, Order, OrderItem
from User.forms import AddressForm


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
    
    context = {
        'cart': cart,
        'cart_items': cart_items,
        'total': cart.get_total(),
        'addresses': addresses,
        'form': form
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
                product_name = item.product.title  # Using title as per Product model
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