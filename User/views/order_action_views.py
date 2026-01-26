from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_POST
from ..models import Order, OrderItem
from Admin.models import Variant
from .common_imports import *

@user_required
@never_cache
def order_detail(request, order_id):
    from django.conf import settings
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'order_detail.html', {
        'order': order,
        'MEDIA_URL': settings.MEDIA_URL
    })

@user_required
@require_POST
def cancel_order(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    if order.status in ['Delivered', 'Cancelled', 'Returned']:
        messages.error(request, "Cannot cancel this order.")
        return redirect('user_order_detail', order_id=order.id)
        
    # Cancel all eligible items
    items_cancelled = False
    for item in order.items.all():
        if item.status not in ['Cancelled', 'Returned']:
            # Increment Stock
            if item.variant:
                item.variant.stock += item.quantity
                item.variant.save()
            else:
                item.product.available_quantity += item.quantity
                item.product.save()
            
            item.status = 'Cancelled'
            item.save()
            items_cancelled = True
            
    if items_cancelled:
        order.status = 'Cancelled'
        order.save()
        messages.success(request, "Order cancelled successfully.")
    
    return redirect('user_order_detail', order_id=order.id)

@user_required
@require_POST
def cancel_order_item(request, item_id):
    item = get_object_or_404(OrderItem, id=item_id, order__user=request.user)
    order = item.order
    
    if item.status in ['Cancelled', 'Returned', 'Delivered']: # Individual item usually follows order status or track, assuming item level status
        messages.error(request, "Cannot cancel this item.")
        return redirect('user_order_detail', order_id=order.id)
    
    # Increment Stock
    if item.variant:
        item.variant.stock += item.quantity
        item.variant.save()
    else:
        item.product.available_quantity += item.quantity
        item.product.save()
        
    item.status = 'Cancelled'
    item.save()
    
    # Check if all items are cancelled
    if not order.items.exclude(status='Cancelled').exists():
        order.status = 'Cancelled'
        order.save()
        
    messages.success(request, "Item cancelled successfully.")
    return redirect('user_order_detail', order_id=order.id)

@user_required
@require_POST
def return_order_item(request, item_id):
    item = get_object_or_404(OrderItem, id=item_id, order__user=request.user)
    order = item.order
    
    reason = request.POST.get('reason')
    if not reason:
         messages.error(request, "Return reason is required.")
         return redirect('user_order_detail', order_id=order.id)

    if order.status != 'Delivered':
         messages.error(request, "Order must be delivered to return items.")
         return redirect('user_order_detail', order_id=order.id)
         
    item.status = 'Returned'
    item.return_reason = reason
    item.save()
    
    messages.success(request, "Return initiated successfully.")
    return redirect('user_order_detail', order_id=order.id)
    
