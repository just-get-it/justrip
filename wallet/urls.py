from django.urls import path,include
from .views import *


urlpatterns = [
    path('', wallet_index, name='wallet_index'),
    path('customer', customer_wallet, name='customer_wallet'),
    path('customer/<int:transaction_id>/', customer_transaction_details, name='customer_transaction_details'),
    path('vendor', vendor_wallet, name='vendor_wallet'),
    path('vendor/<int:transaction_id>/', vendor_transaction_details, name='vendor_transaction_details'),
    path('owner', owner_wallet, name='owner_wallet'),
    path('owner/<int:transaction_id>/', owner_transaction_details, name='owner_transaction_details'),
    path('admin', admin_wallet, name='admin_wallet'),
    path('admin_owner_wallet', admin_owner_wallet, name='admin_owner_wallet'),
    path('admin_customer_wallet', admin_customer_wallet, name='admin_customer_wallet'),
    path('admin/<int:wallet_id>', admin_wallet_det, name='admin_wallet_det'),
    path('admin/transaction/<int:transaction_id>', admin_transaction_det, name='admin_transaction_det'),
]