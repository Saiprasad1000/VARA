from django import forms
from .models import Address

class AddressForm(forms.ModelForm):
    class Meta:
        model = Address
        fields = ['name', 'mobile', 'street_address', 'city', 'state', 'pincode', 'address_type', 'is_default']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'w-full px-4 py-2 border rounded-lg focus:ring-orange-500 focus:border-orange-500', 'placeholder': 'Full Name'}),
            'mobile': forms.TextInput(attrs={'class': 'w-full px-4 py-2 border rounded-lg focus:ring-orange-500 focus:border-orange-500', 'placeholder': 'Mobile Number'}),
            'street_address': forms.TextInput(attrs={'class': 'w-full px-4 py-2 border rounded-lg focus:ring-orange-500 focus:border-orange-500', 'placeholder': 'Street Address'}),
            'city': forms.TextInput(attrs={'class': 'w-full px-4 py-2 border rounded-lg focus:ring-orange-500 focus:border-orange-500', 'placeholder': 'City'}),
            'state': forms.TextInput(attrs={'class': 'w-full px-4 py-2 border rounded-lg focus:ring-orange-500 focus:border-orange-500', 'placeholder': 'State'}),
            'pincode': forms.TextInput(attrs={'class': 'w-full px-4 py-2 border rounded-lg focus:ring-orange-500 focus:border-orange-500', 'placeholder': 'Pincode'}),
            'address_type': forms.Select(attrs={'class': 'w-full px-4 py-2 border rounded-lg focus:ring-orange-500 focus:border-orange-500'}),
            'is_default': forms.CheckboxInput(attrs={'class': 'rounded text-orange-500 focus:ring-orange-500'}),
        }
