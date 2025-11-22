from .common_imports import *
from Admin.models import Product
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger


@never_cache
@login_required
def home(request):
    # Fetch all non-deleted products, ordered by newest first
    products = Product.objects.filter(is_deleted=False).order_by('-created_at')
    
    # Pagination - 12 products per page
    paginator = Paginator(products, 12)
    page_number = request.GET.get('page')
    
    try:
        page_obj = paginator.page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)
    
    context = {
        'best_sellers': page_obj
    }
    return render(request, 'home.html', context)