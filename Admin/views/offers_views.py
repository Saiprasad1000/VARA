from .common_importers import *
from ..models import Offer
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage

def offers(request):
    # Get all offers, ordered by creation date (newest first)
    offers_list = Offer.objects.all().order_by('-created_at')
    
    # Pagination - 7 items per page (matching products page)
    paginator = Paginator(offers_list, 7)
    page_number = request.GET.get('page')
    
    try:
        page_obj = paginator.page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)
    
    return render(request, 'offers.html', {'offers': page_obj})

def add_offer(request):
    if request.method == 'POST':
        product_name = request.POST.get('product')
        category_name = request.POST.get('category')
        discount = request.POST.get('offer_percentage')
        
        Offer.objects.create(
            product_name=product_name,
            category_name=category_name,
            discount=discount
        )
        return redirect('offers')
    return render(request, 'add_offer.html')

def edit_offer(request):
    return render(request, 'edit_offer.html')
