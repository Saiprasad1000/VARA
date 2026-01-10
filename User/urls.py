

from django.contrib import admin
from django.urls import path
from .views import home,index,signup,signin,forgot_password,enter_otp,logout_view,profile,resend_otp,enter_otp_fp,reset_password
from .views.product_views import product_detail
from .views.cart_views import add_to_cart, view_cart, update_cart, remove_from_cart, get_cart_count
from .views.wishlist_views import add_to_wishlist, view_wishlist, remove_from_wishlist, get_wishlist_count, move_to_cart
urlpatterns = [
    path("", index,name='index'),
    path("digital_painting", home,name='digital_painting'),
    path("acrylic_painting/", home,name='acrylic_painting'),
    path("oil_painting/", home,name='oil_painting'),
    path("offer", home,name='offer'),
    path("signin", signin,name='signin'),
    path("signup", signup,name='signup'),
    path("cart", home,name='cart'),
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

    #cart
    path('cart/', view_cart, name='cart'),
    path('cart/add/', add_to_cart, name='add_to_cart'),
    path('cart/update/', update_cart, name='update_cart'),
    path('cart/remove/', remove_from_cart, name='remove_from_cart'),
    path('cart/count/', get_cart_count, name='get_cart_count'),
    
    #Wishlist
    path('wishlist/', view_wishlist, name='wishlist'),
    path('wishlist/add/', add_to_wishlist, name='add_to_wishlist'),
    path('wishlist/remove/', remove_from_wishlist, name='remove_from_wishlist'),
    path('wishlist/count/', get_wishlist_count, name='get_wishlist_count'),
    path('wishlist/move-to-cart/', move_to_cart, name='move_to_cart'),
    ]
