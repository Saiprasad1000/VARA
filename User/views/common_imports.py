from django.shortcuts import render, redirect
from User.models import CustomUser
from django.contrib import messages
from django.db import IntegrityError
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.contrib.auth import authenticate, login
from User.tasks import send_welcome_email_task
from User.tasks import send_forgot_password_email
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
from django.db.models import Q
from Admin.models import Product