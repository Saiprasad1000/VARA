

from django.contrib import admin
from django.urls import path
from .views import home,index,signup,signin,forgot_password,enter_otp,logout_view,profile,resend_otp,enter_otp_fp,reset_password,about_us
from .views.product_views import product_detail
from .views.cart_views import add_to_cart, view_cart, update_cart, remove_from_cart, get_cart_count
from .views.wishlist_views import add_to_wishlist, view_wishlist, remove_from_wishlist, get_wishlist_count, move_to_cart
from .views.checkout_views import checkout, add_address, place_order, order_success, create_razorpay_order, verify_razorpay_payment, retry_payment, place_wallet_order, apply_coupon, remove_coupon
from .views.order_views import my_orders
from .views.address_views import manage_addresses, add_address as add_address_profile, get_address, edit_address, delete_address
from .views.profile_views import edit_profile, verify_email_change
from .views.order_action_views import order_detail, cancel_order, cancel_order_item, return_order_item
from .views.wallet_views import wallet_view, add_money as wallet_add_money, verify_wallet_payment

urlpatterns = [
    path("", index,name='index'),
    path("digital_painting", home,name='digital_painting'),
    path("acrylic_painting/", home,name='acrylic_painting'),
    path("oil_painting/", home,name='oil_painting'),
    path("offer/", home,name='offer'),
    path("about-us/", about_us, name='about_us'),
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
    path('my_orders',my_orders,name='my_orders'),
    path('manage_addresses',manage_addresses,name='manage_addresses'),
    
    # Address Management
    path('profile/address/add/', add_address_profile, name='add_address_profile'),
    path('profile/address/get/<int:address_id>/', get_address, name='get_address'),
    path('profile/address/edit/<int:address_id>/', edit_address, name='edit_address'),
    path('profile/address/delete/<int:address_id>/', delete_address, name='delete_address'),

    # Profile Management
    path('profile/edit/', edit_profile, name='edit_profile'),
    path('profile/verify-email-change/', verify_email_change, name='verify_email_change'),

    # Wallet Custom
    path('wallet/', wallet_view, name='wallet'),
    path('wallet/add-money/', wallet_add_money, name='add_money'),
    path('wallet/verify-payment/', verify_wallet_payment, name='verify_wallet_payment'),

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

    # Checkout & Order Placement
    path('checkout/', checkout, name='checkout'),
    path('add-address-ajax/', add_address, name='add_address'),
    path('place-order/', place_order, name='place_order'),
    path('place-wallet-order/', place_wallet_order, name='place_wallet_order'),
    path('create-razorpay-order/', create_razorpay_order, name='create_razorpay_order'),
    path('verify-razorpay-payment/', verify_razorpay_payment, name='verify_razorpay_payment'),
    path('retry-payment/<int:order_id>/', retry_payment, name='retry_payment'),
    path('order-success/<int:order_id>/', order_success, name='order_success'),
    path('apply-coupon/', apply_coupon, name='apply_coupon'),
    path('remove-coupon/', remove_coupon, name='remove_coupon'),

    # Order Actions
    path('order/<int:order_id>/', order_detail, name='user_order_detail'),
    path('order/cancel/<int:order_id>/', cancel_order, name='cancel_order'),
    path('order/item/cancel/<int:item_id>/', cancel_order_item, name='cancel_order_item'),
    path('order/item/return/<int:item_id>/', return_order_item, name='return_order_item'),
    ]
