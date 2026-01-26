from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from User.models import Order

@login_required
def my_orders(request):
    """Display user's order history"""
    orders = Order.objects.filter(user=request.user).prefetch_related(
        'items__product', 
        'items__variant'
    ).order_by('-created_at')
    
    context = {
        'orders': orders
    }
    return render(request, 'my_orders.html', context)
