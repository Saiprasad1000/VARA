from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods
from django.db import transaction
from django.conf import settings
from User.models import Cart, CartItems, Address, Order, OrderItem, Coupon, CouponUsage
from django.db.models import Sum
from decimal import Decimal
from django.utils import timezone
from User.forms import AddressForm
import razorpay
import json


# Initialize Razorpay client
razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

def calculate_coupon_discount(coupon_code, user, cart_items, total_amount):
    print(f"\n--- COUPON APPLICATION TRACE ---")
    print(f"1. Attempting to apply coupon: '{coupon_code}'")
    
    # 1. Existence check
    try:
        coupon = Coupon.objects.get(code=coupon_code)
        print(f"   -> Found coupon in database: {coupon.code}")
    except Coupon.DoesNotExist:
        print(f"   -> FAILED: Coupon '{coupon_code}' does not exist (Remember: codes are case-sensitive).")
        return False, "Invalid coupon code.", Decimal('0.00'), None
        
    # 2. Active status check
    print(f"2. Checking active status...")
    if not coupon.is_active:
        print(f"   -> FAILED: Coupon {coupon.code} is marked as inactive.")
        return False, "This coupon is no longer active.", Decimal('0.00'), None
        
    # 3. Date check
    now = timezone.now()
    print(f"3. Checking dates... Server Time: {now} | Valid From: {coupon.valid_from} | Valid To: {coupon.valid_to}")
    if now < coupon.valid_from or now > coupon.valid_to:
        print(f"   -> FAILED: Current time falls outside of the valid from/to range.")
        return False, "This coupon is expired or not yet valid.", Decimal('0.00'), None
        
    # 4. Global limits
    print("4. Checking global usage limits...")
    if coupon.usage_limit > 0:
        total_uses = CouponUsage.objects.filter(coupon=coupon).aggregate(Sum('usage_count'))['usage_count__sum'] or 0
        print(f"   -> Global Uses: {total_uses} / Limit: {coupon.usage_limit}")
        if total_uses >= coupon.usage_limit:
            print("   -> FAILED: Global usage limit reached.")
            return False, "Coupon usage limit reached.", Decimal('0.00'), None
            
    # 5. User limits
    print("5. Checking per-user limits...")
    usage = CouponUsage.objects.filter(user=user, coupon=coupon).first()
    user_uses = usage.usage_count if usage else 0
    print(f"   -> User '{user.email}' Uses: {user_uses} / Limit: {coupon.per_user_limit}")
    if user_uses >= coupon.per_user_limit:
        print("   -> FAILED: User limit reached.")
        return False, "You have reached the maximum usage limit for this coupon.", Decimal('0.00'), None
        
    # 6. Min amount check
    total_amount_dec = Decimal(str(total_amount))
    print(f"6. Checking min order amount... Cart Total: {total_amount_dec} | Required: {coupon.min_order_amount}")
    if total_amount_dec < coupon.min_order_amount:
        print("   -> FAILED: Min order amount not met.")
        return False, f"Minimum order amount of ₹{coupon.min_order_amount} required.", Decimal('0.00'), None
        
    # 7. Scope Check
    print("7. Checking category/product scoping...")
        
    applicable_products = list(coupon.applicable_products.values_list('id', flat=True))
    applicable_categories = list(coupon.applicable_categories.values_list('id', flat=True))
    applicable_variants = list(coupon.applicable_variants.values_list('id', flat=True))
    
    is_global = not (applicable_products or applicable_categories or applicable_variants)
    
    eligible_subtotal = Decimal('0.00')
    has_eligible_item = False
    
    for item in cart_items:
        is_eligible = False
        if is_global:
            is_eligible = True
        else:
            if applicable_products and item.product.id in applicable_products:
                is_eligible = True
            elif applicable_categories and item.product.category.id in applicable_categories:
                is_eligible = True
            elif applicable_variants and item.varient and item.varient.id in applicable_variants:
                is_eligible = True
                
        if is_eligible:
            has_eligible_item = True
            item_subtotal = Decimal(str(item.get_subtotal()))
            eligible_subtotal += item_subtotal
            print(f"   -> [ELIGIBLE] Item: {item.product.title} (₹{item_subtotal})")
        else:
            print(f"   -> [INELIGIBLE] Item: {item.product.title}")
            
    print(f"   -> Total eligible amount for discount: ₹{eligible_subtotal}")
    if not has_eligible_item:
        print("   -> FAILED: No items in cart matched the coupon scopes.")
        return False, "This coupon is not applicable to any items in your cart.", Decimal('0.00'), None
        
    discount = Decimal('0.00')
    if coupon.discount_type == 'Percentage':
        discount = (eligible_subtotal * coupon.discount_value) / Decimal('100')
        print(f"8. Discount Calculation (Percentage): {eligible_subtotal} * {coupon.discount_value}% = {discount}")
        if coupon.max_discount:
            discount = min(discount, coupon.max_discount)
            print(f"   -> Apply max discount cap: {discount}")
    else:
        discount = min(coupon.discount_value, eligible_subtotal)
        print(f"8. Discount Calculation (Fixed): min({coupon.discount_value}, {eligible_subtotal}) = {discount}")
        
    discount = min(discount, total_amount_dec)
    print(f"   -> Final Discount Amount to Apply: ₹{discount}\n--- TRACE END ---\n")
        
    return True, "Coupon applied successfully!", discount, coupon

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
    
    subtotal = Decimal(str(cart.get_total()))
    discount_amount = Decimal('0.00')
    applied_coupon_code = None
    
    coupon_id = request.session.get('applied_coupon_id')
    if coupon_id:
        try:
            coupon = Coupon.objects.get(id=coupon_id)
            is_valid, msg, calculated_discount, _ = calculate_coupon_discount(coupon.code, request.user, cart_items, subtotal)
            if is_valid:
                discount_amount = calculated_discount
                applied_coupon_code = coupon.code
            else:
                del request.session['applied_coupon_id']
                if 'discount_amount' in request.session:
                    del request.session['discount_amount']
                messages.warning(request, f"Applied coupon removed: {msg}")
        except Coupon.DoesNotExist:
            del request.session['applied_coupon_id']
            
    final_total = subtotal - discount_amount

    # Find an available referral coupon for this user (unused and still valid)
    from django.utils import timezone as tz
    from django.db.models import Sum
    available_referral_coupon = None
    referral_coupons = Coupon.objects.filter(
        created_for_user=request.user,
        is_referral_coupon=True,
        is_active=True,
        valid_to__gt=tz.now(),
    )
    for rc in referral_coupons:
        # Check it hasn't been globally exhausted (usage_limit=1)
        total_uses = rc.usages.aggregate(Sum('usage_count'))['usage_count__sum'] or 0
        if total_uses < rc.usage_limit:
            available_referral_coupon = rc
            break
    
    context = {
        'cart': cart,
        'cart_items': cart_items,
        'subtotal': subtotal,
        'discount_amount': discount_amount,
        'applied_coupon_code': applied_coupon_code,
        'total': final_total,
        'addresses': addresses,
        'form': form,
        'razorpay_key_id': settings.RAZORPAY_KEY_ID,
        'wallet': wallet,
        'available_referral_coupon': available_referral_coupon,
    }
    return render(request, 'checkout.html', context)

@login_required
@never_cache
@require_http_methods(["POST"])
def apply_coupon(request):
    try:
        data = json.loads(request.body)
        code = data.get('code')
    except:
        code = request.POST.get('code')
        
    if not code:
        return JsonResponse({'success': False, 'message': 'Coupon code is required'})
        
    try:
        cart = Cart.objects.get(user=request.user)
        cart_items = cart.items.select_related('product', 'product__category', 'varient').all()
        if not cart_items:
            return JsonResponse({'success': False, 'message': 'Your cart is empty'})
    except Cart.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Cart not found'})
        
    subtotal = Decimal(str(cart.get_total()))
    is_valid, message, discount, coupon = calculate_coupon_discount(code.strip().upper(), request.user, cart_items, subtotal)
    
    if is_valid:
        request.session['applied_coupon_id'] = coupon.id
        request.session['discount_amount'] = str(discount)
        final_total = subtotal - discount
        return JsonResponse({
            'success': True, 
            'message': message, 
            'discount': str(discount),
            'final_total': str(final_total),
            'code': coupon.code,
            'subtotal': str(subtotal)
        })
    else:
        if 'applied_coupon_id' in request.session:
            del request.session['applied_coupon_id']
        return JsonResponse({'success': False, 'message': message})

@login_required
@never_cache
@require_http_methods(["POST"])
def remove_coupon(request):
    if 'applied_coupon_id' in request.session:
        del request.session['applied_coupon_id']
    if 'discount_amount' in request.session:
        del request.session['discount_amount']
    
    try:
        cart = Cart.objects.get(user=request.user)
        total = cart.get_total()
        return JsonResponse({'success': True, 'message': 'Coupon removed', 'total': str(total), 'subtotal': str(total)})
    except:
        return JsonResponse({'success': False, 'message': 'Cart not found'})


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
            subtotal = Decimal(str(cart.get_total()))
            discount_amount = Decimal('0.00')
            applied_coupon = None
            
            coupon_id = request.session.get('applied_coupon_id')
            if coupon_id:
                try:
                    coupon = Coupon.objects.get(id=coupon_id)
                    is_valid, _, calc_discount, _ = calculate_coupon_discount(coupon.code, request.user, cart_items, subtotal)
                    if is_valid:
                        discount_amount = calc_discount
                        applied_coupon = coupon
                except Coupon.DoesNotExist:
                    pass
                    
            total_amount = subtotal - discount_amount
            
            # Create Order
            order = Order.objects.create(
                user=request.user,
                address=address,
                total_amount=total_amount,
                payment_method='COD',
                payment_status='Pending',
                status='Pending',
                coupon=applied_coupon,
                discount_amount=discount_amount
            )
            
            if applied_coupon:
                usage, _ = CouponUsage.objects.get_or_create(user=request.user, coupon=applied_coupon)
                usage.usage_count += 1
                usage.save()
            
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
            if 'applied_coupon_id' in request.session:
                del request.session['applied_coupon_id']
            if 'discount_amount' in request.session:
                del request.session['discount_amount']
        
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
            subtotal = Decimal(str(cart.get_total()))
            discount_amount = Decimal('0.00')
            applied_coupon = None
            
            coupon_id = request.session.get('applied_coupon_id')
            if coupon_id:
                try:
                    coupon = Coupon.objects.get(id=coupon_id)
                    is_valid, _, calc_discount, _ = calculate_coupon_discount(coupon.code, request.user, cart_items, subtotal)
                    if is_valid:
                        discount_amount = calc_discount
                        applied_coupon = coupon
                except Coupon.DoesNotExist:
                    pass
                    
            total_amount = subtotal - discount_amount
            
            # Create Order with Payment Pending status
            order = Order.objects.create(
                user=request.user,
                address=address,
                total_amount=total_amount,
                payment_method='Razorpay',
                payment_status='Payment Pending',
                status='Pending',
                coupon=applied_coupon,
                discount_amount=discount_amount
            )
            
            if applied_coupon:
                usage, _ = CouponUsage.objects.get_or_create(user=request.user, coupon=applied_coupon)
                usage.usage_count += 1
                usage.save()
            
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
            if 'applied_coupon_id' in request.session:
                del request.session['applied_coupon_id']
            if 'discount_amount' in request.session:
                del request.session['discount_amount']
        
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
            subtotal = Decimal(str(cart.get_total()))
            discount_amount = Decimal('0.00')
            applied_coupon = None
            
            coupon_id = request.session.get('applied_coupon_id')
            if coupon_id:
                try:
                    coupon = Coupon.objects.get(id=coupon_id)
                    is_valid, _, calc_discount, _ = calculate_coupon_discount(coupon.code, request.user, cart_items, subtotal)
                    if is_valid:
                        discount_amount = calc_discount
                        applied_coupon = coupon
                except Coupon.DoesNotExist:
                    pass
                    
            total_amount = subtotal - discount_amount
            
            # Verify wallet balance again for the final total
            if wallet.balance < total_amount:
                raise Exception("Insufficient Wallet Balance")

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
                status='Pending',
                coupon=applied_coupon,
                discount_amount=discount_amount
            )
            
            if applied_coupon:
                usage, _ = CouponUsage.objects.get_or_create(user=request.user, coupon=applied_coupon)
                usage.usage_count += 1
                usage.save()
            
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
            if 'applied_coupon_id' in request.session:
                del request.session['applied_coupon_id']
            if 'discount_amount' in request.session:
                del request.session['discount_amount']
        
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