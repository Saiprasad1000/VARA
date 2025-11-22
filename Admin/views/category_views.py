from .common_importers import *
from django.db.models import Q
from django.views.decorators.http import require_POST

logger = logging.getLogger('django')

def category_list(request):
    try:
        query = request.GET.get('q', '').strip()
        
        # Base queryset - Latest first, not deleted
        categories = Category.objects.filter(is_deleted=False).order_by('-id')

        if query:
            categories = categories.filter(name__icontains=query)

        paginator = Paginator(categories, 7)
        page_number = request.GET.get('page')

        try:
            page_obj = paginator.page(page_number)
        except PageNotAnInteger:
            page_obj = paginator.page(1)
        except EmptyPage:
            page_obj = paginator.page(paginator.num_pages)

        return render(request, 'category.html', {'categories': page_obj, 'query': query})
    except Exception as e:
        logger.exception(f"Error in category_list: {e}")
        return render(request, 'error.html', {'message': 'Error fetching categories'})

def add_category(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        
        if not name:
            messages.error(request, "Category name is required.")
            return render(request, 'add_category.html')
            
        if Category.objects.filter(name__iexact=name, is_deleted=False).exists():
            messages.error(request, "Category with this name already exists.")
            return render(request, 'add_category.html', {'name': name, 'description': description})

        try:
            Category.objects.create(name=name, description=description)
            messages.success(request, "Category added successfully.")
            return redirect('category')
        except Exception as e:
            logger.exception(f"Error adding category: {e}")
            messages.error(request, "Error adding category.")
            return render(request, 'add_category.html', {'name': name, 'description': description})

    return render(request, 'add_category.html')

def edit_category(request, category_id):
    try:
        category = Category.objects.get(id=category_id)
    except Category.DoesNotExist:
        messages.error(request, "Category not found.")
        return redirect('category')

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()

        if not name:
            messages.error(request, "Category name is required.")
            return render(request, 'edit_category.html', {'category': category})

        if Category.objects.filter(name__iexact=name, is_deleted=False).exclude(id=category_id).exists():
            messages.error(request, "Category with this name already exists.")
            return render(request, 'edit_category.html', {'category': category})

        try:
            category.name = name
            category.description = description
            category.save()
            messages.success(request, "Category updated successfully.")
            return redirect('category')
        except Exception as e:
            logger.exception(f"Error updating category: {e}")
            messages.error(request, "Error updating category.")
            return render(request, 'edit_category.html', {'category': category})

    return render(request, 'edit_category.html', {'category': category})

@require_POST
def delete_category(request, category_id):
    try:
        category = Category.objects.get(id=category_id)
        category.is_deleted = True
        category.save()
        messages.success(request, "Category deleted successfully.")
        return JsonResponse({'success': True})
    except Category.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Category not found'})
    except Exception as e:
        logger.exception(f"Error deleting category: {e}")
        return JsonResponse({'success': False, 'error': str(e)})
