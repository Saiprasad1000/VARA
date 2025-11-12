
from django.contrib import admin
from django.urls import path,include
from .views import home,signup,signin,forgot_password,enter_otp

urlpatterns = [
    path("", home,name='home'),
    path("home/", home,name='fsd'),
    path("digital_painting", home,name='digital_painting'),
    path("acrylic_painting/", home,name='acrylic_painting'),
    path("oil_painting/", home,name='oil_painting'),
    path("offer", home,name='offer'),
    path("signin", signin,name='signin'),
    path("signup", signup,name='signup'),
    path("cart", home,name='cart'),
    path("wishlist", home,name='wishlist'),
    path("profile", home,name='profile'),
    path("shipping", home,name='shipping'),
    path("order_tracking", home,name='order_tracking'),
    path("size_guide", home,name='size_guide'),
    path('forgot_password',forgot_password,name='forgot_password'),
    path('enter_otp',enter_otp,name='enter_otp')
    
    
]
