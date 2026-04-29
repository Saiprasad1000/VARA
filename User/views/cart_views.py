
from .common_imports import *
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from Admin.models import Product, Variant
from User.models import Cart, CartItems
from django.db.models import Q
from User.models import Wishlist, WishlistItems

def get_or_create_cart(request):
    """Helper function to get or create cart for user or session"""
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user)
    else:
        # For guest users, use session
        session_key = request.session.session_key
        if not session_key:
            request.session.create()
            session_key = request.session.session_key
        cart, created = Cart.objects.get_or_create(session_key=session_key)
    return cart

@never_cache
def add_to_cart(request):
    """Add product to cart via AJAX"""
    if request.method == 'POST':
        product_id = request.POST.get('product_id')
        variant_id = request.POST.get('variant_id')
        quantity = int(request.POST.get('quantity', 1))
        
        # Get product
        product = get_object_or_404(Product, id=product_id, is_deleted=False, category__isListed=True)
        
        # Get variant if provided
        variant = None
        if variant_id:
            variant = get_object_or_404(Variant, id=variant_id)
        
        # Check stock availability
        available_stock = variant.stock if variant else product.available_quantity
        if available_stock <= 0:
            return JsonResponse({
                'success': False,
                'message': 'Product is currently out of stock'
            })
        
        if quantity > available_stock:
            return JsonResponse({
                'success': False,
                'message': f'Only {available_stock} items available in stock'
            })
        
        # Get or create cart
        cart = get_or_create_cart(request)
        
        # Check if item already exists in cart
        cart_item, created = CartItems.objects.get_or_create(
            cart=cart,
            product=product,
            varient=variant,
            defaults={'quantity': quantity}
        )
        
        if not created:
            # Update quantity if item already exists
            new_quantity = cart_item.quantity + quantity
            if new_quantity > available_stock:
                return JsonResponse({
                    'success': False,
                    'message': f'Cannot add more. Only {available_stock} items available'
                })
            cart_item.quantity = new_quantity
            cart_item.save()
        
        # Remove from wishlist if exists
        wishlist = None
        if request.user.is_authenticated:
            try:
                wishlist = Wishlist.objects.get(user=request.user)
            except Wishlist.DoesNotExist:
                pass
        else:
            session_key = request.session.session_key
            if session_key:
                try:
                    wishlist = Wishlist.objects.get(session_key=session_key)
                except Wishlist.DoesNotExist:
                    pass

        if wishlist:
            WishlistItems.objects.filter(
                wishlist=wishlist,
                product=product,
                varient=variant
            ).delete()
        
        return JsonResponse({
            'success': True,
            'message': 'Product added to cart successfully',
            'cart_count': cart.get_item_count(),
            'wishlist_count': wishlist.get_item_count() if wishlist else 0
        })
    
    return JsonResponse({'success': False, 'message': 'Invalid request'})

@never_cache
def view_cart(request):
    """Display cart page"""
    from django.conf import settings
    cart = get_or_create_cart(request)
    cart_items = cart.items.all()
    
    context = {
        'cart': cart,
        'cart_items': cart_items,
        'total': cart.get_total(),
        'original_total': cart.get_original_total(),
        'total_discount': cart.get_total_discount(),
        'MEDIA_URL': settings.MEDIA_URL
    }
    return render(request, 'cart.html', context)

@never_cache
def update_cart(request):
    """Update cart item quantity via AJAX"""
    if request.method == 'POST':
        cart_item_id = request.POST.get('cart_item_id')
        quantity = int(request.POST.get('quantity', 1))
        
        cart_item = get_object_or_404(CartItems, id=cart_item_id)
        
        # Check stock
        available_stock = cart_item.varient.stock if cart_item.varient else cart_item.product.available_quantity
        if available_stock <= 0 and quantity > 0:
            return JsonResponse({
                'success': False,
                'message': 'Product is currently out of stock'
            })
            
        if quantity > available_stock:
            return JsonResponse({
                'success': False,
                'message': f'Only {available_stock} items available'
            })
        
        if quantity <= 0:
            cart_item.delete()
            message = 'Item removed from cart'
        else:
            cart_item.quantity = quantity
            cart_item.save()
            message = 'Cart updated successfully'
        
        cart = cart_item.cart
        return JsonResponse({
            'success': True,
            'message': message,
            'subtotal': float(cart_item.get_subtotal()) if quantity > 0 else 0,
            'original_subtotal': float(cart_item.get_original_subtotal()) if quantity > 0 else 0,
            'item_discount': float(cart_item.get_discount_amount()) if quantity > 0 else 0,
            'cart_total': float(cart.get_total()),
            'cart_original_total': float(cart.get_original_total()),
            'cart_total_discount': float(cart.get_total_discount()),
            'cart_count': cart.get_item_count()
        })
    
    return JsonResponse({'success': False, 'message': 'Invalid request'})

@never_cache
def remove_from_cart(request):
    """Remove item from cart via AJAX"""
    if request.method == 'POST':
        cart_item_id = request.POST.get('cart_item_id')
        cart_item = get_object_or_404(CartItems, id=cart_item_id)
        cart = cart_item.cart
        cart_item.delete()
        
        return JsonResponse({
            'success': True,
            'message': 'Item removed from cart',
            'cart_total': float(cart.get_total()),
            'cart_original_total': float(cart.get_original_total()),
            'cart_total_discount': float(cart.get_total_discount()),
            'cart_count': cart.get_item_count()
        })
    
    return JsonResponse({'success': False, 'message': 'Invalid request'})

@never_cache
def get_cart_count(request):
    """Get cart item count for navbar badge"""
    cart = get_or_create_cart(request)
    return JsonResponse({'cart_count': cart.get_item_count()})