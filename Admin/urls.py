
from django.contrib import admin
from django.urls import path, include
from .views import customers, category_views, product_views, offers_views, orders_views, wallet_views
from .views.customers_views import toggle_user
from .views.coupon_views import coupon_list, add_coupon, edit_coupon, toggle_coupon_status
from .views.dashboard_views import admin_dashboard
from .views.sales_report_views import sales_report, download_sales_pdf, download_sales_excel
from .views.admin_views import banner_management, download_order_invoice

urlpatterns = [
     # Dashboard
     path("admin_home/", admin_dashboard, name='admin_home'),
     path("dashboard/",  admin_dashboard, name='dashboard'),

     # Products
     path("products/",                               product_views.product_list,           name='products'),
     path("products/add/",                           product_views.add_product,            name='add_product'),
     path("products/edit/<int:product_id>/",         product_views.edit_product,           name='edit_product'),
     path("product/delete/<int:product_id>/",        product_views.delete_product,         name='delete_product'),
     path("product/toggle-status/<int:product_id>/", product_views.toggle_product_status,  name='toggle_product_status'),
     path("product/<int:product_id>/variants/",      product_views.manage_variants,        name='manage_variants'),
     path("product/<int:product_id>/variant/add/",   product_views.add_variant,            name='add_variant'),
     path("variant/remove/<int:variant_id>/",        product_views.remove_variant,         name='remove_variant'),

     # Orders + invoice
     path("orders/",                        orders_views.order_list,   name='orders'),
     path("orders/<int:order_id>/",         orders_views.order_detail, name='vara_admin_order_detail_test'),
     path("orders/<int:order_id>/invoice/", download_order_invoice,    name='admin_order_invoice'),

     # Customers
     path("customers/",                 customers,   name='customers'),
     path("toggle_user/<int:user_id>/", toggle_user, name='toggle_user'),

     # Offers
     path("offers/",                       offers_views.offers,       name='offers'),
     path("offers/add/",                   offers_views.add_offer,    name='add_offer'),
     path("edit_offer/<int:offer_id>/",    offers_views.edit_offer,   name='edit_offer'),
     path("toggle_offer/<int:offer_id>/",  offers_views.toggle_offer, name='toggle_offer'),
     path("delete_offer/<int:offer_id>/",  offers_views.delete_offer, name='delete_offer'),

     # Coupons
     path("coupons/",                         coupon_list,          name='coupons'),
     path("coupons/add/",                     add_coupon,           name='add_coupon'),
     path("coupons/edit/<int:coupon_id>/",    edit_coupon,          name='edit_coupon'),
     path("coupons/toggle/<int:coupon_id>/",  toggle_coupon_status, name='toggle_coupon_status'),

     # Sales Report + downloads
     path("sales_report",          sales_report,         name='sales_report'),
     path("sales_report/pdf/",     download_sales_pdf,   name='sales_report_pdf'),
     path("sales_report/excel/",   download_sales_excel, name='sales_report_excel'),

     # Banner stub (URL preserved so existing hardcoded links don't 404)
     path("banner_management", banner_management, name='banner_management'),

     # Wallet transactions
     path("wallet/", wallet_views.wallet_transactions, name='wallet_transactions'),

     # Categories
     path("category/",                          category_views.category_list,          name='category'),
     path("category/add/",                      category_views.add_category,           name='add_category'),
     path("category/edit/<int:category_id>/",   category_views.edit_category,          name='edit_category'),
     path("category/delete/<int:category_id>/", category_views.delete_category,        name='delete_category'),
     path("category/toggle/<int:category_id>/", category_views.toggle_category_status, name='toggle_category_status'),
]
