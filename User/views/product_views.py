from .common_imports import *
from Admin.models import Product, Variant
from django.shortcuts import get_object_or_404
from django.conf import settings


@never_cache
@user_required
def product_detail(request, product_id):
    """Display detailed information about a specific product"""
    # Fetch product, return 404 if not found or deleted
    product = get_object_or_404(Product, id=product_id, is_deleted=False,)
    
    # Fetch variants specific to this product
    variants = Variant.objects.filter(product=product, isListed=True)
    context = {
        'product': product,
        'variants': variants,
        'MEDIA_URL': settings.MEDIA_URL
    }
    return render(request, 'product_detail.html', context)
