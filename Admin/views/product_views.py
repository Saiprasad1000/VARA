from .common_importers import *
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from PIL import Image
import io
import json
from django.shortcuts import redirect
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from Admin.models import Product, Category

logger = logging.getLogger('django')

def product_list(request):
    try:
        query = request.GET.get('q', '').strip()
        
        # Base queryset - Latest first, not deleted
        products = Product.objects.filter(is_deleted=False).select_related('category').order_by('-id')

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

        try:
            category = Category.objects.get(id=category_id)
            
            product.title = title
            product.category = category
            product.price = price
            product.available_quantity = quantity
            product.description = description
            product.artist_name = artist_name
            product.publishing_date = publishing_date

            if images:
                if len(images) < 3:
                     messages.error(request, "Please upload at least 3 images if you are updating them.")
                     return render(request, 'edit_product.html', {'product': product, 'categories': categories})
                
                # Process new images
                image_urls = []
                for img in images:
                    image = Image.open(img)
                    image.thumbnail((800, 800))
                    img_io = io.BytesIO()
                    image_format = img.content_type.split('/')[-1].upper()
                    if image_format == 'JPG': image_format = 'JPEG'
                    image.save(img_io, format=image_format)
                    filename = f"products/{title}_{img.name}"
                    path = default_storage.save(filename, ContentFile(img_io.getvalue()))
                    image_urls.append(path)
                product.product_imgs = image_urls

            product.save()
            messages.success(request, "Product updated successfully.")
            return redirect('products')
        except Exception as e:
            logger.exception(f"Error updating product: {e}")
            messages.error(request, "Error updating product.")
            return render(request, 'edit_product.html', {'product': product, 'categories': categories})

    return render(request, 'edit_product.html', {'product': product, 'categories': categories})

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
