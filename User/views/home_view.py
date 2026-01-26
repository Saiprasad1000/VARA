from .common_imports import *
from Admin.models import Product, Category
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q


@never_cache
@user_required
def home(request):
    # Base queryset: all non-deleted products
    products = Product.objects.filter(is_deleted=False, category__isListed=True)

    # Read search, filter and sort parameters from query string
    search_query = request.GET.get('q') or request.GET.get('search') or ''
    selected_categories = request.GET.getlist('category')
    sort_option = request.GET.get('sort', '').strip()

    # Apply text search
    if search_query:
        products = products.filter(
            Q(title__icontains=search_query)
            | Q(artist_name__icontains=search_query)
            | Q(category__name__icontains=search_query)
        )

    # Apply category filtering (expects category names matching these values)
    if selected_categories:
        products = products.filter(category__name__in=selected_categories)

    # Apply sorting
    order_by_field = '-created_at'
    if sort_option == 'a-z':
        order_by_field = 'title'
    elif sort_option == 'z-a':
        order_by_field = '-title'
    elif sort_option == 'price-low-high':
        order_by_field = 'price'
    elif sort_option == 'price-high-low':
        order_by_field = '-price'
    elif sort_option == 'date-new-old':
        order_by_field = '-created_at'
    elif sort_option == 'date-old-new':
        order_by_field = 'created_at'

    products = products.order_by(order_by_field)

    # Pagination - 12 products per page
    paginator = Paginator(products, 12)
    page_number = request.GET.get('page')
    
    try:
        page_obj = paginator.page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)

    # Build base querystring without page for pagination links
    params = request.GET.copy()
    if 'page' in params:
        del params['page']
    base_querystring = params.urlencode()
    
    # Fetch all active categories for filter sidebar
    categories = Category.objects.filter(is_deleted=False, isListed=True).order_by('name')

    context = {
        'best_sellers': page_obj,
        'selected_categories': selected_categories,
        'selected_sort': sort_option,
        'base_querystring': base_querystring,
        'categories': categories,
        'search_query': search_query,
    }
    return render(request, 'home.html', context)


@never_cache
@user_required
def about_us(request):
    return render(request, 'about_us.html')

