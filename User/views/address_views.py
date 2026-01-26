from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from django.template.loader import render_to_string
from User.models import Address
from User.forms import AddressForm

@login_required
def manage_addresses(request):
    """Render manage addresses page"""
    addresses = Address.objects.filter(user=request.user).order_by('-is_default', '-id')
    form = AddressForm()
    
    context = {
        'addresses': addresses,
        'form': form
    }
    return render(request, 'manage_addresses.html', context)

@login_required
@require_http_methods(["POST"])
def add_address(request):
    """Add new address via AJAX"""
    form = AddressForm(request.POST)
    
    if form.is_valid():
        try:
            address = form.save(commit=False)
            address.user = request.user
            
            if address.is_default:
                Address.objects.filter(user=request.user, is_default=True).update(is_default=False)
                
            address.save()
            return JsonResponse({'success': True, 'message': 'Address added successfully!'})
            
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
            
    return JsonResponse({'success': False, 'message': 'Invalid form data', 'errors': form.errors})

@login_required
def get_address(request, address_id):
    """Get address details for editing"""
    try:
        address = Address.objects.get(id=address_id, user=request.user)
        data = {
            'id': address.id,
            'name': address.name,
            'mobile': address.mobile,
            'street_address': address.street_address,
            'city': address.city,
            'state': address.state,
            'pincode': address.pincode,
            'address_type': address.address_type,
            'is_default': address.is_default
        }
        return JsonResponse({'success': True, 'address': data})
    except Address.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Address not found'})

@login_required
@require_http_methods(["POST"])
def edit_address(request, address_id):
    """Edit address via AJAX"""
    address = get_object_or_404(Address, id=address_id, user=request.user)
    form = AddressForm(request.POST, instance=address)
    
    if form.is_valid():
        try:
            # Handle default address logic
            if form.cleaned_data.get('is_default'):
                Address.objects.filter(user=request.user, is_default=True).exclude(id=address.id).update(is_default=False)
                
            form.save()
            return JsonResponse({'success': True, 'message': 'Address updated successfully!'})
            
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
            
    return JsonResponse({'success': False, 'message': 'Invalid form data', 'errors': form.errors})

@login_required
@require_http_methods(["POST"])
def delete_address(request, address_id):
    """Delete address via AJAX"""
    try:
        address = Address.objects.get(id=address_id, user=request.user)
        address.delete()
        return JsonResponse({'success': True, 'message': 'Address deleted successfully!'})
    except Address.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Address not found'})
