from django import forms
from django.contrib import admin
from .models import *
from .forms import VehicalComapnyForm, FuelRouteForm,VehicalNameForm
# Register your models here.


class ChargesAdminInline(admin.TabularInline):
    model = Charges


class VehicalTypeAdmin(admin.ModelAdmin):
    inlines = (ChargesAdminInline,)


class VehicalNameAdmin(admin.ModelAdmin):
    forms = (ChargesAdminInline,)


class FuelRouteAdmin(admin.ModelAdmin):
    form = FuelRouteForm


class VehicalCompanyAdmin(admin.ModelAdmin):
    form = VehicalComapnyForm

    class Media:
        js = (
            # '//ajax.googleapis.com/ajax/libs/jquery/1.9.1/jquery.min.js', # jquery
            # 'js/myscript.js',       # project static folder
            'js/main/form_control.js',   # app static folder
        )
class VehicalNameAdmin(admin.ModelAdmin):
    form = VehicalNameForm

    class Media:
        js = (
            # '//ajax.googleapis.com/ajax/libs/jquery/1.9.1/jquery.min.js', # jquery
            # 'js/myscript.js',       # project static folder
            'js/main/form_control.js',   # app static folder
        )


admin.site.register(detail)
admin.site.register(State)
admin.site.register(OwnerProfile)
admin.site.register(DriverProfile)
admin.site.register(CarCompany)
admin.site.register(Car)
admin.site.register(CarType)
admin.site.register(CustomerProfile)
admin.site.register(CorporateCustomerProfile)
admin.site.register(Trip)
admin.site.register(TravellersInformation)
admin.site.register(Event)
admin.site.register(VendorTrip)
admin.site.register(Notification)
admin.site.register(VehicalGroup)
admin.site.register(VehicalType, VehicalTypeAdmin)
admin.site.register(VehicalName,VehicalNameAdmin)
admin.site.register(Charges)
admin.site.register(VehicalCompany, VehicalCompanyAdmin)
admin.site.register(Route)
admin.site.register(Fuel)
admin.site.register(Fuel_Route)
admin.site.register(Toll_Permit_Parking)
admin.site.register(Coupon)
admin.site.register(CouponType)

