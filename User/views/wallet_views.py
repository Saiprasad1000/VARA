import json
import razorpay
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.cache import never_cache
from django.conf import settings
from .common_imports import *
from ..models import Wallet, WalletTransaction

# Initialize Razorpay client
razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

@user_required
@never_cache
def wallet_view(request):
    """Render wallet balance and transaction history."""
    wallet, created = Wallet.objects.get_or_create(user=request.user)
    transactions = wallet.transactions.all().order_by('-created_at')
    
    context = {
        'wallet': wallet,
        'transactions': transactions,
        'razorpay_key_id': settings.RAZORPAY_KEY_ID,
    }
    return render(request, 'wallet.html', context)


@user_required
@require_http_methods(["POST"])
@never_cache
def add_money(request):
    """Create a Razorpay order to add money to wallet."""
    try:
        data = json.loads(request.body)
        amount = data.get('amount')
        
        if not amount or float(amount) <= 0:
            return JsonResponse({'success': False, 'message': 'Invalid amount'})
            
        # Amount in paise
        amount_in_paise = int(float(amount) * 100)
        
        # Create Razorpay order
        razorpay_order = razorpay_client.order.create({
            'amount': amount_in_paise,
            'currency': 'INR',
            'receipt': f'wallet_topup_{request.user.id}',
        })
        
        return JsonResponse({
            'success': True,
            'razorpay_order_id': razorpay_order['id'],
            'amount': amount_in_paise,
            'currency': 'INR',
            'key_id': settings.RAZORPAY_KEY_ID,
            'user_name': f'{request.user.first_name} {request.user.last_name}',
            'user_email': request.user.email,
            'user_phone': request.user.mobile or '',
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error creating order: {str(e)}'
        }, status=500)


@user_required
@require_http_methods(["POST"])
@never_cache
def verify_wallet_payment(request):
    """Verify Razorpay payment and credit the wallet."""
    try:
        data = json.loads(request.body)
        razorpay_order_id = data.get('razorpay_order_id')
        razorpay_payment_id = data.get('razorpay_payment_id')
        razorpay_signature = data.get('razorpay_signature')
        amount_in_paise = data.get('amount')
        
    except (json.JSONDecodeError, AttributeError):
        return JsonResponse({'success': False, 'message': 'Invalid request data'}, status=400)
        
    if not all([razorpay_order_id, razorpay_payment_id, razorpay_signature, amount_in_paise]):
        return JsonResponse({'success': False, 'message': 'Missing payment details'}, status=400)
        
    try:
        # Verify payment signature
        params_dict = {
            'razorpay_order_id': razorpay_order_id,
            'razorpay_payment_id': razorpay_payment_id,
            'razorpay_signature': razorpay_signature,
        }
        
        razorpay_client.utility.verify_payment_signature(params_dict)
        
        # Signature valid - credit the wallet
        amount = float(amount_in_paise) / 100.0
        wallet, _ = Wallet.objects.get_or_create(user=request.user)
        wallet.credit(amount, "Added money via User Wallet Top-up")
        
        # We usually return JsonResponse on ajax calls
        messages.success(request, f"Successfully added ₹{amount} to wallet.")
        return JsonResponse({'success': True, 'message': 'Money added successfully!'})
        
    except razorpay.errors.SignatureVerificationError:
        return JsonResponse({'success': False, 'message': 'Payment verification failed.'}, status=400)
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Error: {str(e)}'}, status=500)
