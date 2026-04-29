from .common_importers import *
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from User.models import Order

# Dashboard and sales_report are in their own view files.
# This file keeps: banner_management stub + admin invoice download.

@admin_required
def banner_management(request):
    return render(request, 'admin_home.html')   # safe stub – URL kept, sidebar removed


@admin_required
def download_order_invoice(request, order_id):
    """Admin: download invoice PDF for any order."""
    from Admin.services.invoice_service import generate_invoice_pdf
    order = get_object_or_404(Order, id=order_id)
    buffer = generate_invoice_pdf(order)
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = (
        f'attachment; filename="vara_invoice_order_{order.id}.pdf"'
    )
    return response

