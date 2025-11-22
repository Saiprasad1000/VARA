from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.db import DatabaseError
import logging
from User.models import CustomUser
from Admin.models import Category, Product