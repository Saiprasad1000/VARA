from django.shortcuts import render, redirect
from User.models import CustomUser
from django.contrib import messages
from django.db import IntegrityError
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.contrib.auth import authenticate, login
from User.tasks import send_welcome_email_task
from User.tasks import send_forgot_password_email
from User.tasks import send_update_email_otp
from User.utilites import generate_otp
from django.core.cache import cache
from django.core.exceptions import SuspiciousOperation
from django.contrib.auth import logout
import logging
from User.validators import (validate_name,validate_email_unique,validate_mobile,validate_password_strength,validate_password_match)
from django.http import JsonResponse
logger = logging.getLogger(__name__)
from django.views.decorators.cache import never_cache
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import user_passes_test
from django.db.models import Q
from Admin.models import Product

# Decorator to check if user is authenticated (regular user, not admin)
user_required = user_passes_test(
    lambda user: user.is_authenticated,
    login_url='signin'
)

# Decorator to redirect authenticated users away from auth pages
def anonymous_required(view_func):
    """
    Decorator that redirects authenticated users to their home page.
    - Regular users → redirect to 'home'
    - Superusers → redirect to 'admin_home'
    - Unauthenticated users → allow access to the view
    """
    def wrapper(request, *args, **kwargs):
        if request.user.is_authenticated:
            if request.user.is_superuser:
                return redirect('admin_home')
            return redirect('home')
        return view_func(request, *args, **kwargs)
    return wrapper