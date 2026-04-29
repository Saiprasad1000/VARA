from django.shortcuts import render
from django.core.paginator import Paginator
from .common_importers import admin_required
from User.models import WalletTransaction


@admin_required
def wallet_transactions(request):
    """
    Admin view to list all wallet transactions with filtering, sorting, and pagination.
    """
    transactions = WalletTransaction.objects.all().select_related(
        'wallet__user', 'order'
    ).order_by('-created_at')

    # --- Filter by transaction type ---
    type_filter = request.GET.get('type', '')
    if type_filter in ('Credit', 'Debit'):
        transactions = transactions.filter(transaction_type=type_filter)

    # --- Sorting ---
    sort_by = request.GET.get('sort', 'newest')
    if sort_by == 'oldest':
        transactions = transactions.order_by('created_at')
    else:
        # Default: newest first
        transactions = transactions.order_by('-created_at')

    # --- Pagination ---
    paginator = Paginator(transactions, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'transactions': page_obj,
        'type_filter': type_filter,
        'sort_by': sort_by,
    }
    return render(request, 'wallet_transactions.html', context)
