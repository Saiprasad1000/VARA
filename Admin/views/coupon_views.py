from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from User.models import Coupon
from Admin.models import Product, Category, Variant

def make_local_time_aware(date_str):
    if not date_str:
        return None
    dt = parse_datetime(date_str)
    if dt and timezone.is_naive(dt):
        return timezone.make_aware(dt)
    return dt

@staff_member_required
def coupon_list(request):
    coupons = Coupon.objects.all().order_by('-created_at')
    return render(request, 'admin_coupons.html', {'coupons': coupons})

@staff_member_required
def add_coupon(request):
    if request.method == 'POST':
        code = request.POST.get('code').strip().upper()
        discount_type = request.POST.get('discount_type')
        discount_value = request.POST.get('discount_value')
        min_order_amount = request.POST.get('min_order_amount') or 0
        max_discount = request.POST.get('max_discount') or None
        valid_from = make_local_time_aware(request.POST.get('valid_from'))
        valid_to = make_local_time_aware(request.POST.get('valid_to'))
        usage_limit = request.POST.get('usage_limit') or 0
        per_user_limit = request.POST.get('per_user_limit') or 1
        
        # Validation for uniqueness
        if Coupon.objects.filter(code=code).exists():
            messages.error(request, 'Coupon with this code already exists.')
            return redirect('add_coupon')
            
        try:
            coupon = Coupon.objects.create(
                code=code,
                discount_type=discount_type,
                discount_value=discount_value,
                min_order_amount=min_order_amount,
                max_discount=max_discount,
                valid_from=valid_from,
                valid_to=valid_to,
                usage_limit=usage_limit,
                per_user_limit=per_user_limit,
                is_active=True
            )
            
            # Scoping
            product_ids = request.POST.getlist('products')
            category_ids = request.POST.getlist('categories')
            variant_ids = request.POST.getlist('variants')
            
            if product_ids:
                coupon.applicable_products.set(Product.objects.filter(id__in=product_ids))
            if category_ids:
                coupon.applicable_categories.set(Category.objects.filter(id__in=category_ids))
            if variant_ids:
                coupon.applicable_variants.set(Variant.objects.filter(id__in=variant_ids))
                
            messages.success(request, 'Coupon added successfully.')
            return redirect('coupons')
        except Exception as e:
            messages.error(request, f'Error adding coupon: {str(e)}')
            return redirect('add_coupon')
            
    # GET request
    products = Product.objects.filter(is_deleted=False)
    categories = Category.objects.filter(is_deleted=False)
    variants = Variant.objects.filter(isListed=True)
    return render(request, 'admin_coupon_form.html', {
        'products': products,
        'categories': categories,
        'variants': variants,
        'action': 'Add'
    })

@staff_member_required
def edit_coupon(request, coupon_id):
    coupon = get_object_or_404(Coupon, id=coupon_id)
    
    if request.method == 'POST':
        code = request.POST.get('code').strip().upper()
        
        if Coupon.objects.filter(code=code).exclude(id=coupon.id).exists():
            messages.error(request, 'Coupon with this code already exists.')
            return redirect('edit_coupon', coupon_id=coupon.id)
            
        try:
            coupon.code = code
            coupon.discount_type = request.POST.get('discount_type')
            coupon.discount_value = request.POST.get('discount_value')
            coupon.min_order_amount = request.POST.get('min_order_amount') or 0
            coupon.max_discount = request.POST.get('max_discount') or None
            
            valid_from = make_local_time_aware(request.POST.get('valid_from'))
            valid_to = make_local_time_aware(request.POST.get('valid_to'))
            if valid_from:
                coupon.valid_from = valid_from
            if valid_to:
                coupon.valid_to = valid_to
                
            coupon.usage_limit = request.POST.get('usage_limit') or 0
            coupon.per_user_limit = request.POST.get('per_user_limit') or 1
            
            coupon.save()
            
            # Scoping
            product_ids = request.POST.getlist('products')
            category_ids = request.POST.getlist('categories')
            variant_ids = request.POST.getlist('variants')
            
            coupon.applicable_products.set(Product.objects.filter(id__in=product_ids))
            coupon.applicable_categories.set(Category.objects.filter(id__in=category_ids))
            coupon.applicable_variants.set(Variant.objects.filter(id__in=variant_ids))
            
            messages.success(request, 'Coupon updated successfully.')
            return redirect('coupons')
        except Exception as e:
            messages.error(request, f'Error updating coupon: {str(e)}')
            return redirect('edit_coupon', coupon_id=coupon.id)

    # GET request
    products = Product.objects.filter(is_deleted=False)
    categories = Category.objects.filter(is_deleted=False)
    variants = Variant.objects.filter(isListed=True)
    
    context = {
        'coupon': coupon,
        'products': products,
        'categories': categories,
        'variants': variants,
        'action': 'Edit',
        'selected_products': coupon.applicable_products.values_list('id', flat=True),
        'selected_categories': coupon.applicable_categories.values_list('id', flat=True),
        'selected_variants': coupon.applicable_variants.values_list('id', flat=True),
    }
    return render(request, 'admin_coupon_form.html', context)

@staff_member_required
def toggle_coupon_status(request, coupon_id):
    coupon = get_object_or_404(Coupon, id=coupon_id)
    coupon.is_active = not coupon.is_active
    coupon.save()
    status = "activated" if coupon.is_active else "deactivated"
    messages.success(request, f'Coupon {coupon.code} successfully {status}.')
    return redirect('coupons')
