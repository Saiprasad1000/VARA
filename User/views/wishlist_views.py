from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.cache import never_cache
from Admin.models import Product, Variant
from User.models import Wishlist, WishlistItems, Cart, CartItems

def get_or_create_wishlist(request):
    """Helper function to get or create wishlist for user or session"""
    if request.user.is_authenticated:
        wishlist, created = Wishlist.objects.get_or_create(user=request.user)
    else:
        session_key = request.session.session_key
        if not session_key:
            request.session.create()
            session_key = request.session.session_key
        wishlist, created = Wishlist.objects.get_or_create(session_key=session_key)
    return wishlist

@never_cache
def add_to_wishlist(request):
    """Add product to wishlist via AJAX"""
    if request.method == 'POST':
        product_id = request.POST.get('product_id')
        variant_id = request.POST.get('variant_id')
        
        product = get_object_or_404(Product, id=product_id, is_deleted=False, category__isListed=True)
        
        variant = None
        if variant_id:
            variant = get_object_or_404(Variant, id=variant_id)
        
        wishlist = get_or_create_wishlist(request)
        
        # Check if already in wishlist
        wishlist_item, created = WishlistItems.objects.get_or_create(
            wishlist=wishlist,
            product=product,
            varient=variant
        )
        
        if created:
            return JsonResponse({
                'success': True,
                'message': 'Added to wishlist',
                'wishlist_count': wishlist.get_item_count()
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Already in wishlist'
            })
    
    return JsonResponse({'success': False, 'message': 'Invalid request'})

@never_cache
def view_wishlist(request):
    """Display wishlist page"""
    from django.conf import settings
    wishlist = get_or_create_wishlist(request)
    wishlist_items = wishlist.items.all()
    
    context = {
        'wishlist': wishlist,
        'wishlist_items': wishlist_items,
        'MEDIA_URL': settings.MEDIA_URL
    }
    return render(request, 'wishlist.html', context)

@never_cache
def remove_from_wishlist(request):
    """Remove item from wishlist via AJAX"""
    if request.method == 'POST':
        wishlist_item_id = request.POST.get('wishlist_item_id')
        wishlist_item = get_object_or_404(WishlistItems, id=wishlist_item_id)
        wishlist = wishlist_item.wishlist
        wishlist_item.delete()
        
        return JsonResponse({
            'success': True,
            'message': 'Removed from wishlist',
            'wishlist_count': wishlist.get_item_count()
        })
    
    return JsonResponse({'success': False, 'message': 'Invalid request'})

@never_cache
def get_wishlist_count(request):
    """Get wishlist item count for navbar badge"""
    wishlist = get_or_create_wishlist(request)
    return JsonResponse({'wishlist_count': wishlist.get_item_count()})

@never_cache
def move_to_cart(request):
    """Move item from wishlist to cart"""
    if request.method == 'POST':
        wishlist_item_id = request.POST.get('wishlist_item_id')
        wishlist_item = get_object_or_404(WishlistItems, id=wishlist_item_id)
        
        # Get or create cart
        from .cart_views import get_or_create_cart
        cart = get_or_create_cart(request)
        
        # Add to cart
        cart_item, created = CartItems.objects.get_or_create(
            cart=cart,
            product=wishlist_item.product,
            varient=wishlist_item.varient,
            defaults={'quantity': 1}
        )
        
        if not created:
            cart_item.quantity += 1
            cart_item.save()
        
        # Remove from wishlist
        wishlist = wishlist_item.wishlist
        wishlist_item.delete()
        
        return JsonResponse({
            'success': True,
            'message': 'Moved to cart',
            'cart_count': cart.get_item_count(),
            'wishlist_count': wishlist.get_item_count()
        })
    
    return JsonResponse({'success': False, 'message': 'Invalid request'})