
from django.contrib import admin
from django.urls import path,include
from .views import admin_home,customers,sales_report,banner_management,category_views,product_views,offers_views
from .views.customers_views import toggle_user

urlpatterns = [
     path("admin_home/", admin_home,name='admin_home'),
     path("dashboard/", admin_home,name='dashboard'),
     
     
     path("products/", product_views.product_list, name='products'),
     path("products/add/", product_views.add_product, name='add_product'),
     path("products/edit/<int:product_id>/", product_views.edit_product, name='edit_product'),
     path("product/delete/<int:product_id>/", product_views.delete_product, name='delete_product'),
     path("product/toggle-status/<int:product_id>/", product_views.toggle_product_status, name='toggle_product_status'),
     path("product/<int:product_id>/variants/", product_views.manage_variants, name='manage_variants'),
     path("product/<int:product_id>/variant/add/", product_views.add_variant, name='add_variant'),
     path("variant/remove/<int:variant_id>/", product_views.remove_variant, name='remove_variant'),
     path("orders/", admin_home,name='orders'),
     path("customers/", customers,name='customers'),
     path("reviews/", admin_home,name='reviews'),
     path("offers/", offers_views.offers,name='offers'),
     path("coupons",admin_home,name='coupons'),
     path("offers/add/", offers_views.add_offer,name='add_offer'),
     path("offers/edit/", offers_views.edit_offer,name='edit_offer'),
     path("sales_report",sales_report,name='sales_report'),
     path("banner_management",banner_management,name='banner_management'),
     
     
     path("category/", category_views.category_list, name='category'),
     path("category/add/", category_views.add_category, name='add_category'),
     path("category/edit/<int:category_id>/", category_views.edit_category, name='edit_category'),
     path("category/delete/<int:category_id>/", category_views.delete_category, name='delete_category'),
     path("category/toggle/<int:category_id>/", category_views.toggle_category_status, name='toggle_category_status'),
     path("toggle_user/<int:user_id>/", toggle_user, name='toggle_user'),

     
 
]
