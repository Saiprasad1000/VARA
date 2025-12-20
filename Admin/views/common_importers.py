from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.db import DatabaseError
import logging
from User.models import CustomUser
from Admin.models import Category, Product
from django.contrib.auth.decorators import user_passes_test

# Decorator to check if user is authenticated and is a superuser
admin_required = user_passes_test(
    lambda user: user.is_authenticated and user.is_superuser,
    login_url='signin'
)