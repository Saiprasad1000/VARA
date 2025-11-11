
from django.contrib import admin
from django.urls import path,include
from .views import home,signup

urlpatterns = [
    path("", home,name='home'),
    path("home/", home,name='home'),
    path("digital_painting", home,name='digital_painting'),
    path("acrylic_painting/", home,name='acrylic_painting'),
    path("oil_painting/", home,name='oil_painting'),
    path("offer", home,name='offer'),
    path("signin", home,name='login'),
    path("signup", signup,name='signup'),
    path("cart", home,name='cart'),
    path("wishlist", home,name='wishlist'),
    path("profile", home,name='profile'),
    path("shipping", home,name='shipping'),
    path("order_tracking", home,name='order_tracking'),
    path("size_guide", home,name='size_guide'),
    
    
]
