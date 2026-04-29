from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_POST
from ..models import Order, OrderItem, Wallet
from Admin.models import Variant
from .common_imports import *

@user_required
@never_cache
def order_detail(request, order_id):
    from django.conf import settings
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'order_detail.html', {
        'order': order,
        'MEDIA_URL': settings.MEDIA_URL,
        'razorpay_key_id': settings.RAZORPAY_KEY_ID,
    })

@user_required
@require_POST
def cancel_order(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    if order.status in ['Shipped', 'Delivered', 'Cancelled', 'Returned', 'Cancel Requested', 'Return Requested']:
        messages.error(request, "Cannot cancel this order.")
        return redirect('user_order_detail', order_id=order.id)
        
    items_cancelled = False
    
    for item in order.items.all():
        if item.status in ['Pending', 'Confirmed']:
            item.status = 'Cancel Requested'
            item.save()
            items_cancelled = True
            
    if items_cancelled:
        messages.success(request, "Order cancellation requested. Awaiting admin approval.")
        order.sync_status_from_items()
    else:
        messages.error(request, "No eligible items found to cancel.")
    
    return redirect('user_order_detail', order_id=order.id)

@user_required
@require_POST
def cancel_order_item(request, item_id):
    item = get_object_or_404(OrderItem, id=item_id, order__user=request.user)
    order = item.order
    
    if item.status not in ['Pending', 'Confirmed']:
        messages.error(request, "Item cannot be cancelled at this stage.")
        return redirect('user_order_detail', order_id=order.id)
        
    item.status = 'Cancel Requested'
    item.save()
    
    messages.success(request, "Item cancellation requested. Awaiting admin approval.")
    
    order.sync_status_from_items()
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

    if item.status != 'Delivered':
         messages.error(request, "Item must be delivered to initiate a return.")
         return redirect('user_order_detail', order_id=order.id)
         
    item.status = 'Return Requested'
    item.return_reason = reason
    item.save()
    
    order.sync_status_from_items()
    
    messages.success(request, "Return requested successfully. Awaiting admin approval.")
    return redirect('user_order_detail', order_id=order.id)

@user_required
def download_user_invoice(request, order_id):
    """User: secure download of their own invoice."""
    from Admin.services.invoice_service import generate_invoice_pdf
    from django.http import HttpResponse
    
    order = get_object_or_404(Order, id=order_id, user=request.user)
    buffer = generate_invoice_pdf(order)
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="vara_invoice_order_{order.id}.pdf"'
    return response
