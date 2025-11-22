from .common_imports import *
from Admin.models import Product, Variant
from django.shortcuts import get_object_or_404


@never_cache
@login_required
def product_detail(request, product_id):
    """Display detailed information about a specific product"""
    try:
        # Fetch product, return 404 if not found or deleted
        product = get_object_or_404(Product, id=product_id, is_deleted=False)
        
        # Fetch all available variants
        variants = Variant.objects.filter(isListed=True)
        
        context = {
            'product': product,
            'variants': variants
        }
        return render(request, 'product_detail.html', context)
    except Exception as e:
        logger.exception(f"Error in product_detail: {e}")
        return render(request, 'error.html', {'message': 'Error loading product details'})
