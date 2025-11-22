from .common_importers import *
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db.models import Q

logger = logging.getLogger('django') 

def customers(request):
    try:
        query = request.GET.get('q', '').strip()
        
        # Base queryset - Latest first
        users_list = CustomUser.objects.all().order_by('-id')

        # Search filter
        if query:
            users_list = users_list.filter(
                Q(first_name__icontains=query) | 
                Q(last_name__icontains=query) | 
                Q(email__icontains=query)
            )

        # Initialize paginator (7 users per page)
        paginator = Paginator(users_list, 7)
        page_number = request.GET.get('page')

        # Handle pagination edge cases
        try:
            users = paginator.page(page_number)
        except PageNotAnInteger:
            users = paginator.page(1)  # Default to first page
        except EmptyPage:
            users = paginator.page(paginator.num_pages)  # Default to last page

        return render(request, 'customers.html', {'users': users, 'query': query})

    except Exception as e:
        logger.exception(f"Unexpected error in customers view: {e}")
        return render(request, 'error.html', {
            'message': 'Something went wrong. Please try again later.'
        })

@require_POST
def toggle_user(request, user_id):
    try:
        user = CustomUser.objects.get(id=user_id)
        user.is_active = not user.is_active
        user.save()
        return JsonResponse({'success': True, 'is_active': user.is_active})
    except CustomUser.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'User not found'}, status=404)
    except Exception as e:
        logger.error(f"Error toggling user {user_id}: {e}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)