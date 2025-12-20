from .common_importers import *
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from PIL import Image
import io
import json
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from Admin.models import Product, Category, Variant

logger = logging.getLogger('django')

@admin_required
def product_list(request):
    try:
        query = request.GET.get('q', '').strip()
        
        # Base queryset Show all products (active and blocked)
        products = Product.objects.all().select_related('category').order_by('-id')

        if query:
            products = products.filter(title__icontains=query)

        paginator = Paginator(products, 7)
        page_number = request.GET.get('page')

        try:
            page_obj = paginator.page(page_number)
        except PageNotAnInteger:
            page_obj = paginator.page(1)
        except EmptyPage:
            page_obj = paginator.page(paginator.num_pages)

        return render(request, 'products.html', {'products': page_obj, 'query': query})
    except Exception as e:
        logger.exception(f"Error in product_list: {e}")
        return render(request, 'error.html', {'message': 'Error fetching products'})

@admin_required
def add_product(request):
    categories = Category.objects.filter(is_deleted=False, isListed=True)
    print(f"DEBUG: Found {categories.count()} categories")  # Debug line
    for cat in categories:
        print(f"  - {cat.name} (ID: {cat.id}, Listed: {cat.isListed}, Deleted: {cat.is_deleted})")
    
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        category_id = request.POST.get('category')
        price = request.POST.get('price')
        quantity = request.POST.get('quantity')
        description = request.POST.get('description', '').strip()
        artist_name = request.POST.get('artist_name', '').strip()
        publishing_date = request.POST.get('publishing_date')
        images = request.FILES.getlist('images')

        # Validation
        errors = []
        if not title:
            errors.append("Title is required.")
        if not category_id:
            errors.append("Category is required.")
        if not price:
            errors.append("Price is required.")
        if not quantity:
            errors.append("Quantity is required.")
        if not artist_name:
            errors.append("Artist name is required.")
        if not publishing_date:
            errors.append("Publishing date is required.")
        if len(images) < 3:
            errors.append("Please upload at least 3 images.")

        if errors:
            for error in errors:
                messages.error(request, error)
            return render(request, 'add_product.html', {'categories': categories})

        try:
            category = Category.objects.get(id=category_id)
            
            # Process images
            image_urls = []
            for img in images:
                try:
                    # Open image using Pillow
                    image = Image.open(img)
                    
                    # Convert to RGB (handles PNG with transparency)
                    if image.mode in ('RGBA', 'LA', 'P'):
                        # Create white background
                        background = Image.new('RGB', image.size, (255, 255, 255))
                        if image.mode == 'P':
                            image = image.convert('RGBA')
                        background.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
                        image = background
                    elif image.mode != 'RGB':
                        image = image.convert('RGB')
                    
                    # Get original dimensions
                    width, height = image.size
                    
                    # Crop to square (center crop)
                    if width > height:
                        # Landscape - crop width
                        left = (width - height) // 2
                        right = left + height
                        image = image.crop((left, 0, right, height))
                    elif height > width:
                        # Portrait - crop height
                        top = (height - width) // 2
                        bottom = top + width
                        image = image.crop((0, top, width, bottom))
                    
                    # Resize to 800x800
                    image = image.resize((800, 800), Image.Resampling.LANCZOS)
                    
                    # Save processed image to memory with optimization
                    img_io = io.BytesIO()
                    image.save(img_io, format='JPEG', quality=85, optimize=True)
                    img_io.seek(0)
                    
                    # Save to storage
                    filename = f"products/{title}_{img.name.split('.')[0]}.jpg"
                    path = default_storage.save(filename, ContentFile(img_io.getvalue()))
                    image_urls.append(path)
                    
                except Exception as img_error:
                    logger.exception(f"Error processing image {img.name}: {img_error}")
                    messages.error(request, f"Error processing image {img.name}")
                    return render(request, 'add_product.html', {'categories': categories})

            Product.objects.create(
                title=title,
                category=category,
                price=price,
                available_quantity=quantity,
                description=description,
                artist_name=artist_name,
                publishing_date=publishing_date,
                product_imgs=image_urls
            )
            messages.success(request, "Product added successfully.")
            return redirect('products')
            
        except Exception as e:
            logger.exception(f"Error adding product: {e}")
            messages.error(request, f"Error adding product: {e}")
            return render(request, 'add_product.html', {'categories': categories})


    return render(request, 'add_product.html', {'categories': categories})

@admin_required
def edit_product(request, product_id):
    try:
        product = Product.objects.get(id=product_id)
    except Product.DoesNotExist:
        messages.error(request, "Product not found.")
        return redirect('products')

    categories = Category.objects.filter(is_deleted=False, isListed=True)

    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        category_id = request.POST.get('category')
        price = request.POST.get('price')
        quantity = request.POST.get('quantity')
        description = request.POST.get('description', '').strip()
        artist_name = request.POST.get('artist_name', '').strip()
        publishing_date = request.POST.get('publishing_date')
        images = request.FILES.getlist('images')
        reordered_images = request.POST.get('reordered_images')

        try:
            category = Category.objects.get(id=category_id)
            
            product.title = title
            product.category = category
            product.price = price
            product.available_quantity = quantity
            product.description = description
            product.artist_name = artist_name
            product.publishing_date = publishing_date

            # If new images are uploaded, append them to existing images instead of replacing
            if images:
                # Start with existing images (if any)
                existing_images = product.product_imgs or []
                image_urls = list(existing_images)

                # Process and append new images
                for img in images:
                    image = Image.open(img)
                    image.thumbnail((800, 800))
                    img_io = io.BytesIO()
                    image_format = img.content_type.split('/')[-1].upper()
                    if image_format == 'JPG':
                        image_format = 'JPEG'
                    image.save(img_io, format=image_format)
                    filename = f"products/{title}_{img.name}"
                    path = default_storage.save(filename, ContentFile(img_io.getvalue()))
                    image_urls.append(path)

                product.product_imgs = image_urls
            elif reordered_images:
                # Update image order if reordered (no new images uploaded)
                try:
                    reordered_list = json.loads(reordered_images)
                    product.product_imgs = reordered_list
                except json.JSONDecodeError:
                    pass  # Keep existing order if JSON is invalid

            product.save()
            messages.success(request, "Product updated successfully.")
            return redirect('products')
        except Exception as e:
            logger.exception(f"Error updating product: {e}")
            messages.error(request, "Error updating product.")
            return render(request, 'edit_product.html', {'product': product, 'categories': categories})

    return render(request, 'edit_product.html', {'product': product, 'categories': categories})

@admin_required
@require_POST
def delete_product(request, product_id):
    try:
        product = Product.objects.get(id=product_id)
        product.is_deleted = True
        product.save()
        messages.success(request, "Product deleted successfully.")
        return JsonResponse({'success': True})
    except Product.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Product not found'})
    except Exception as e:
        logger.exception(f"Error deleting product: {e}")
        return JsonResponse({'success': False, 'error': str(e)})

@admin_required
@require_POST
def toggle_product_status(request, product_id):
    try:
        import json
        data = json.loads(request.body)
        is_active = data.get('isActive', True)
        
        product = Product.objects.get(id=product_id)
        # Active = is_deleted False, Blocked = is_deleted True
        product.is_deleted = not is_active
        product.save()
        
        return JsonResponse({'success': True})
    except Product.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Product not found'})
    except Exception as e:
        logger.exception(f"Error toggling product status: {e}")
        return JsonResponse({'success': False, 'error': str(e)})

@admin_required
def manage_variants(request, product_id):
    """Display and manage variants for a specific product"""
    try:
        product = get_object_or_404(Product, id=product_id)
        variants = Variant.objects.filter(product=product).order_by('variant_type')
        
        context = {
            'product': product,
            'variants': variants
        }
        return render(request, 'manage_variants.html', context)
    except Exception as e:
        logger.exception(f"Error in manage_variants: {e}")
        messages.error(request, 'Error loading variants')
        return redirect('products')

@admin_required
def add_variant(request, product_id):
    """Add a new variant to a product"""
    if request.method == 'POST':
        try:
            product = get_object_or_404(Product, id=product_id)
            variant_type = request.POST.get('variant_type')
            price = request.POST.get('price')
            stock = request.POST.get('stock')
            
            # Check if variant already exists
            if Variant.objects.filter(product=product, variant_type=variant_type).exists():
                messages.error(request, f'{variant_type.title()} variant already exists for this product')
                return redirect('manage_variants', product_id=product_id)
            
            Variant.objects.create(
                product=product,
                variant_type=variant_type,
                price=price,
                stock=stock,
                isListed=True
            )
            messages.success(request, f'{variant_type.title()} variant added successfully')
            return redirect('manage_variants', product_id=product_id)
        except Exception as e:
            logger.exception(f"Error adding variant: {e}")
            messages.error(request, 'Error adding variant')
            return redirect('manage_variants', product_id=product_id)
    return redirect('products')

@admin_required
@require_POST
def remove_variant(request, variant_id):
    """Remove a variant"""
    try:
        variant = get_object_or_404(Variant, id=variant_id)
        variant.delete()
        return JsonResponse({'success': True})
    except Exception as e:
        logger.exception(f"Error removing variant: {e}")
        return JsonResponse({'success': False, 'error': str(e)})
