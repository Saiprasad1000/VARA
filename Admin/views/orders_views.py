from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator
from django.db.models import Q
from django.contrib import messages
from .common_importers import *
from User.models import Order, OrderItem

@admin_required
def order_list(request):
    """
    View to list all orders with search, filter, sort, and pagination.
    """
    orders = Order.objects.all().select_related('user').order_by('-created_at')

    # Search
    search_query = request.GET.get('search', '')
    if search_query:
        orders = orders.filter(
            Q(id__icontains=search_query) |
            Q(user__email__icontains=search_query) |
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query)
        )

    # Filter by Status
    status_filter = request.GET.get('status', '')
    if status_filter:
        orders = orders.filter(status=status_filter)

    # Sort
    sort_by = request.GET.get('sort', 'created_at') # Default sort
    if sort_by == 'amount_asc':
        orders = orders.order_by('total_amount')
    elif sort_by == 'amount_desc':
        orders = orders.order_by('-total_amount')
    elif sort_by == 'date_asc':
        orders = orders.order_by('created_at')
    elif sort_by == 'date_desc':
        orders = orders.order_by('-created_at')

    # Pagination
    paginator = Paginator(orders, 10) # 10 orders per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'orders': page_obj,
        'search_query': search_query,
        'status_filter': status_filter,
        'sort_by': sort_by,
        'status_choices': Order.STATUS_CHOICES,
    }
    return render(request, 'orders.html', context)

@admin_required
def order_detail(request, order_id):
    """
    View to show order details and update status (order-level or item-level).
    """
    from django.conf import settings
    order = get_object_or_404(Order, id=order_id)
    
    if request.method == 'POST':
        # Check if updating individual item status
        item_id = request.POST.get('item_id')
        if item_id:
            item_status = request.POST.get('item_status')
            if item_status:
                order_item = get_object_or_404(OrderItem, id=item_id, order=order)
                order_item.status = item_status
                order_item.save()
                messages.success(request, f"Item status updated to {item_status}.")
                return redirect('vara_admin_order_detail_test', order_id=order.id)
        else:
            # Update order-level status
            new_status = request.POST.get('status')
            if new_status:
                order.status = new_status
                order.save()
                messages.success(request, f"Order #{order.id} status updated to {new_status}.")
                return redirect('vara_admin_order_detail_test', order_id=order.id)

    context = {
        'order': order,
        'status_choices': Order.STATUS_CHOICES,
        'MEDIA_URL': settings.MEDIA_URL,
    }
    return render(request, 'admin_order_detail.html', context)
