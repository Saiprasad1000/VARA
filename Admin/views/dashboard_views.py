from django.shortcuts import render
from django.db.models import Sum, Count, F
from django.db.models.functions import TruncDay, TruncMonth, TruncYear
from django.utils import timezone
import json
from datetime import timedelta
from .common_importers import admin_required
from User.models import Order, OrderItem, CustomUser
from .sales_report_views import _apply_date_filter


@admin_required
def admin_dashboard(request):
    """
    Admin dashboard with live stats, Chart.js sales chart, and top-10 lists.
    """
    now = timezone.now()

    period = request.GET.get('period', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')

    # ── Filter Base QuerySets ────────────────────────────────────────────────
    base_orders = Order.objects.all()
    filtered_orders = _apply_date_filter(base_orders, period, date_from, date_to)

    # ── Stats cards ──────────────────────────────────────────────────────────
    total_users = CustomUser.objects.filter(is_staff=False, is_superuser=False).count()
    total_orders = filtered_orders.count()

    valid_orders = filtered_orders.exclude(status__in=['Cancelled', 'Returned'])
    total_revenue = valid_orders.aggregate(s=Sum('total_amount'))['s'] or 0

    # Previous-month comparison for users
    first_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    prev_month_end = first_of_month - timedelta(seconds=1)
    prev_month_start = prev_month_end.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    users_this_month = CustomUser.objects.filter(
        is_staff=False, is_superuser=False, created_at__gte=first_of_month
    ).count()
    users_last_month = CustomUser.objects.filter(
        is_staff=False, is_superuser=False,
        created_at__gte=prev_month_start, created_at__lt=first_of_month
    ).count()

    # ── Chart data ────────────────────────────────────────────────────────────
    # Group by appropriate interval based on period
    if period in ['daily', 'weekly', 'monthly'] or (period == 'custom' and date_from and date_to):
        qs = (
            valid_orders
            .annotate(chart_period=TruncDay('created_at'))
            .values('chart_period')
            .annotate(revenue=Sum('total_amount'), orders=Count('id'))
            .order_by('chart_period')
        )
        fmt = '%b %d'
    else:  # 'yearly' or 'all time'
        qs = (
            valid_orders
            .annotate(chart_period=TruncMonth('created_at'))
            .values('chart_period')
            .annotate(revenue=Sum('total_amount'), orders=Count('id'))
            .order_by('chart_period')
        )
        fmt = '%b %Y'

    chart_labels = []
    chart_revenue = []
    chart_orders = []
    for row in qs:
        chart_labels.append(row['chart_period'].strftime(fmt))
        chart_revenue.append(float(row['revenue'] or 0))
        chart_orders.append(row['orders'])

    # ── Top 10 Products ───────────────────────────────────────────────────────
    valid_order_ids = valid_orders.values_list('id', flat=True)

    top_products = (
        OrderItem.objects.filter(order__in=valid_order_ids)
        .values('product__title')
        .annotate(qty_sold=Sum('quantity'))
        .order_by('-qty_sold')[:10]
    )

    # ── Top 10 Categories ─────────────────────────────────────────────────────
    top_categories = (
        OrderItem.objects.filter(order__in=valid_order_ids)
        .values('product__category__name')
        .annotate(qty_sold=Sum('quantity'))
        .order_by('-qty_sold')[:10]
    )

    # ── Top 10 Artists ────────────────────────────────────────────────────────
    top_artists = (
        OrderItem.objects.filter(order__in=valid_order_ids)
        .values('product__artist_name')
        .annotate(qty_sold=Sum('quantity'))
        .order_by('-qty_sold')[:10]
    )

    context = {
        # Stats
        'total_users': total_users,
        'total_orders': total_orders,
        'total_revenue': total_revenue,
        'users_this_month': users_this_month,
        'users_last_month': users_last_month,
        # Chart
        'period': period,
        'date_from': date_from,
        'date_to': date_to,
        'chart_labels': json.dumps(chart_labels),
        'chart_revenue': json.dumps(chart_revenue),
        'chart_orders': json.dumps(chart_orders),
        # Top 10
        'top_products': list(top_products),
        'top_categories': list(top_categories),
        'top_artists': list(top_artists),
    }
    return render(request, 'admin_home.html', context)
