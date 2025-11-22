

from django.contrib import admin
from django.urls import path
from .views import home,index,signup,signin,forgot_password,enter_otp,logout_view,profile,resend_otp,enter_otp_fp,reset_password
from .views.product_views import product_detail

urlpatterns = [
    path("", index,name='index'),
    path("digital_painting", home,name='digital_painting'),
    path("acrylic_painting/", home,name='acrylic_painting'),
    path("oil_painting/", home,name='oil_painting'),
    path("offer", home,name='offer'),
    path("signin", signin,name='signin'),
    path("signup", signup,name='signup'),
    path("cart", home,name='cart'),
    path("wishlist", home,name='wishlist'),
    path("shipping", home,name='shipping'),
    path("order_tracking", home,name='order_tracking'),
    path("size_guide", home,name='size_guide'),
    path('forgot_password',forgot_password,name='forgot_password'),
    path('enter_otp',enter_otp,name='enter_otp'),
    path('resend_otp',resend_otp,name='resend_otp'),
    path('logout',logout_view,name='logout'),
    path('profile/',profile,name='profile'),
    path('my_orders',home,name='my_orders'),
    path('manage_addresses',home,name='manage_addresses'),
    path('wallet',home,name='wallet'),
    path('home/',home,name='home'),
    path('search/',home,name='search'),
    path('enter_otp_fp',enter_otp_fp,name='enter_otp_fp'),
    path('reset_password',reset_password,name='reset_password'),
    path('product/<int:product_id>/', product_detail, name='product_detail'),
    
]
