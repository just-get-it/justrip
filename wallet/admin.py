from django.contrib import admin
from .models import Transaction, PaymentDetail, Wallet
# Register your models here.

admin.site.register(Transaction)
admin.site.register(Wallet)
admin.site.register(PaymentDetail)