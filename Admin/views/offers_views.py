from .common_importers import *
from ..models import Offer, Product, Category, Variant
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.utils.dateparse import parse_datetime
from django.http import JsonResponse
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404

@admin_required
def offers(request):
    # Get all offers, ordered by creation date (newest first)
    offers_list = Offer.objects.all().order_by('-created_at')
    
    # Pagination - 7 items per page
    paginator = Paginator(offers_list, 7)
    page_number = request.GET.get('page')
    
    try:
        page_obj = paginator.page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)
    
    return render(request, 'offers.html', {'offers': page_obj})

@admin_required
def add_offer(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        offer_type = request.POST.get('offer_type')
        value = request.POST.get('value')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        is_active = request.POST.get('is_active') == 'on'

        product_ids = request.POST.getlist('products')
        category_ids = request.POST.getlist('categories')
        variant_ids = request.POST.getlist('variants')

        # Validation
        if not name or not value or not start_date or not end_date:
            messages.error(request, "All core fields are required.")
            return redirect('add_offer')
            
        if not (product_ids or category_ids or variant_ids):
            messages.error(request, "At least one scope (Product, Category, or Variant) must be selected.")
            return redirect('add_offer')

        try:
            parsed_start = parse_datetime(start_date)
            parsed_end = parse_datetime(end_date)
            
            if parsed_end <= parsed_start:
                messages.error(request, "End date must be after start date.")
                return redirect('add_offer')

            offer = Offer.objects.create(
                name=name,
                offer_type=offer_type,
                value=value,
                start_date=parsed_start,
                end_date=parsed_end,
                is_active=is_active
            )
            
            if product_ids:
                offer.products.set(Product.objects.filter(id__in=product_ids))
            if category_ids:
                offer.categories.set(Category.objects.filter(id__in=category_ids))
            if variant_ids:
                offer.variants.set(Variant.objects.filter(id__in=variant_ids))

            messages.success(request, "Offer created successfully.")
            return redirect('offers')
        except Exception as e:
            messages.error(request, f"Error creating offer: {str(e)}")
            return redirect('add_offer')

    context = {
        'products': Product.objects.filter(is_deleted=False),
        'categories': Category.objects.filter(is_deleted=False),
        'variants': Variant.objects.all(),
    }
    return render(request, 'add_offer.html', context)

@admin_required
def edit_offer(request, offer_id):
    offer = get_object_or_404(Offer, id=offer_id)
    
    if request.method == 'POST':
        name = request.POST.get('name')
        offer_type = request.POST.get('offer_type')
        value = request.POST.get('value')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        is_active = request.POST.get('is_active') == 'on'

        product_ids = request.POST.getlist('products')
        category_ids = request.POST.getlist('categories')
        variant_ids = request.POST.getlist('variants')

        # Validation
        if not name or not value or not start_date or not end_date:
            messages.error(request, "All core fields are required.")
            return redirect('edit_offer', offer_id=offer.id)
            
        if not (product_ids or category_ids or variant_ids):
            messages.error(request, "At least one scope (Product, Category, or Variant) must be selected.")
            return redirect('edit_offer', offer_id=offer.id)

        try:
            parsed_start = parse_datetime(start_date)
            parsed_end = parse_datetime(end_date)
            
            if parsed_end <= parsed_start:
                messages.error(request, "End date must be after start date.")
                return redirect('edit_offer', offer_id=offer.id)

            offer.name = name
            offer.offer_type = offer_type
            offer.value = value
            offer.start_date = parsed_start
            offer.end_date = parsed_end
            offer.is_active = is_active
            offer.save()
            
            offer.products.set(Product.objects.filter(id__in=product_ids))
            offer.categories.set(Category.objects.filter(id__in=category_ids))
            offer.variants.set(Variant.objects.filter(id__in=variant_ids))

            messages.success(request, "Offer updated successfully.")
            return redirect('offers')
        except Exception as e:
            messages.error(request, f"Error updating offer: {str(e)}")
            return redirect('edit_offer', offer_id=offer.id)

    context = {
        'offer': offer,
        'products': Product.objects.filter(is_deleted=False),
        'categories': Category.objects.filter(is_deleted=False),
        'variants': Variant.objects.all(),
        'selected_products': offer.products.values_list('id', flat=True),
        'selected_categories': offer.categories.values_list('id', flat=True),
        'selected_variants': offer.variants.values_list('id', flat=True),
    }
    return render(request, 'edit_offer.html', context)

@admin_required
def toggle_offer(request, offer_id):
    if request.method == "POST":
        offer = get_object_or_404(Offer, id=offer_id)
        offer.is_active = not offer.is_active
        offer.save()
        return JsonResponse({"success": True, "is_active": offer.is_active})
    return JsonResponse({"success": False, "error": "Invalid request method"})

@admin_required
def delete_offer(request, offer_id):
    if request.method == "POST":
        offer = get_object_or_404(Offer, id=offer_id)
        offer.delete()
        return JsonResponse({"success": True})
    return JsonResponse({"success": False, "error": "Invalid request method"})
