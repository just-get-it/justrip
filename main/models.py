from pyexpat import model
from django.db import models, router
import random
import os
from django.db.models.base import Model
# from mapbox_location_field.spatial.models import SpatialLocationField
from mapbox_location_field.models import LocationField
from datetime import datetime
from django.utils import timezone
from django.contrib.auth.models import User


def get_filename_ext(filepath):
    base_name = os.path.basename(filepath)
    name, ext = os.path.splitext(base_name)
    return name, ext


def upload_cheque_path(instance, filename):
    new_filename = random.randint(1, 13516546431654)
    name, ext = get_filename_ext(filename)
    final_filename = '{new_filename}{ext}'.format(
        new_filename=new_filename, ext=ext)
    return "just_cabs/cheque/{final_filename}".format(
        new_filename=new_filename,
        final_filename=final_filename
    )

def upload_pan_path(instance, filename):
    new_filename = random.randint(1, 13516546431654)
    name, ext = get_filename_ext(filename)
    final_filename = '{new_filename}{ext}'.format(new_filename=new_filename, ext=ext)
    return "just_cabs/pan/{final_filename}".format(
        new_filename=new_filename,
        final_filename=final_filename
    )

def upload_profile_path(instance, filename):
    new_filename = random.randint(1, 13516546431654)
    name, ext = get_filename_ext(filename)
    final_filename = '{new_filename}{ext}'.format(
        new_filename=new_filename, ext=ext)
    return "just_cabs/profile/{final_filename}".format(
        new_filename=new_filename,
        final_filename=final_filename
    )


def upload_aadhar_path(instance, filename):
    new_filename = random.randint(1, 13516546431654)
    name, ext = get_filename_ext(filename)
    final_filename = '{new_filename}{ext}'.format(
        new_filename=new_filename, ext=ext)
    return "just_cabs/aadhar/{final_filename}".format(
        new_filename=new_filename,
        final_filename=final_filename
    )


def upload_licence_path(instance, filename):
    new_filename = random.randint(1, 13516546431654)
    name, ext = get_filename_ext(filename)
    final_filename = '{new_filename}{ext}'.format(
        new_filename=new_filename, ext=ext)
    return "just_cabs/licence/{final_filename}".format(
        new_filename=new_filename,
        final_filename=final_filename
    )


def upload_police_verification_path(instance, filename):
    new_filename = random.randint(1, 13516546431654)
    name, ext = get_filename_ext(filename)
    final_filename = '{new_filename}{ext}'.format(
        new_filename=new_filename, ext=ext)
    return "just_cabs/police_verification/{final_filename}".format(
        new_filename=new_filename,
        final_filename=final_filename
    )


def upload_car_path(instance, filename):
    new_filename = random.randint(1, 13516546431654)
    name, ext = get_filename_ext(filename)
    final_filename = '{new_filename}{ext}'.format(
        new_filename=new_filename, ext=ext)
    return "just_cabs/car/{final_filename}".format(
        new_filename=new_filename,
        final_filename=final_filename
    )

def upload_vehicle_group_path(instance, filename):
    new_filename = random.randint(1, 13516546431654)
    name, ext = get_filename_ext(filename)
    final_filename = '{new_filename}{ext}'.format(
        new_filename=new_filename, ext=ext)
    return "just_cabs/vehicle_group/{final_filename}".format(
        new_filename=new_filename,
        final_filename=final_filename
    )
def upload_vehicle_type_path(instance, filename):
    new_filename = random.randint(1, 13516546431654)
    name, ext = get_filename_ext(filename)
    final_filename = '{new_filename}{ext}'.format(
        new_filename=new_filename, ext=ext)
    return "just_cabs/vehicle_type/{final_filename}".format(
        new_filename=new_filename,
        final_filename=final_filename
    )
def upload_vehicle_company_path(instance, filename):
    new_filename = random.randint(1, 13516546431654)
    name, ext = get_filename_ext(filename)
    final_filename = '{new_filename}{ext}'.format(
        new_filename=new_filename, ext=ext)
    return "just_cabs/vehicle_company/{final_filename}".format(
        new_filename=new_filename,
        final_filename=final_filename
    )
def upload_vehicle_path(instance, filename):
    new_filename = random.randint(1, 13516546431654)
    name, ext = get_filename_ext(filename)
    final_filename = '{new_filename}{ext}'.format(
        new_filename=new_filename, ext=ext)
    return "just_cabs/vehicle/{final_filename}".format(
        new_filename=new_filename,
        final_filename=final_filename
    )


def upload_car_documents_path(instance, filename):
    new_filename = random.randint(1, 13516546431654)
    name, ext = get_filename_ext(filename)
    final_filename = '{new_filename}{ext}'.format(
        new_filename=new_filename, ext=ext)
    return "just_cabs/car_documents/{final_filename}".format(
        new_filename=new_filename,
        final_filename=final_filename
    )


def get_all_states():
    return State.objects.all()

# Create your models here.


class detail(models.Model):
    name = models.CharField(max_length=255)
    email = models.EmailField()
    password = models.CharField(max_length=255)
    contact = models.BigIntegerField(null=True)
    gender = models.CharField(max_length=100)
    is_staff = models.BooleanField(default=False)
    # OTP AND RECOVERY
    user_otp = models.CharField(max_length=255, null=True, blank=True)
    user_otp_time = models.DateTimeField(null=True, blank=True)
    user_otp_key = models.TextField(null=True, blank=True)
    user_otp_verify = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return str(self.name)


class State(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return str(self.name)


class Tax(models.Model):
    GST = models.IntegerField()

    def __str__(self):
        return str(self.GST)


class OwnerProfile(models.Model):
    user = models.ForeignKey(
        detail, on_delete=models.CASCADE, related_name='owner_profile')
    profile_picture = models.FileField(
        upload_to=upload_profile_path, null=True,  blank=True)
    cheque_image = models.FileField(
        upload_to=upload_cheque_path, null=True, blank=True)
    bank_account_no = models.CharField(max_length=100, null=True, blank=True)
    ifsc_code = models.CharField(max_length=100, null=True, blank=True)
    account_holders_name = models.CharField(
        max_length=200, null=True, blank=True)
    is_owner = models.BooleanField(default=False)
    is_vendor = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    is_active = models.BooleanField(default=False)
    address_coords = LocationField(map_attrs={"center": [
                                   78.742730, 23.424107], "marker_color": "blue", "placeholder": "Address Coordinates", "zoom": 3}, blank=True, null=True)
    address = models.CharField(max_length=400, null=True, blank=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    states = models.ManyToManyField(State, blank=True, default=get_all_states)

    def __str__(self):
        return str(self.user.name)


class DriverProfile(models.Model):
    owner = models.ForeignKey(
        OwnerProfile, on_delete=models.CASCADE, related_name='drivers')
    name = models.CharField(max_length=200, null=True)
    phone = models.CharField(max_length=100, null=True)
    picture = models.FileField(
        upload_to=upload_profile_path, null=True, blank=True)
    aadhar_front_image = models.FileField(
        upload_to=upload_aadhar_path, null=True, blank=True)
    aadhar_back_image = models.FileField(
        upload_to=upload_aadhar_path, null=True, blank=True)
    aadhar_card_number = models.CharField(
        max_length=100, null=True, blank=True)
    police_verification = models.FileField(
        upload_to=upload_police_verification_path, null=True, blank=True)
    driving_licence_front = models.FileField(
        upload_to=upload_licence_path, null=True, blank=True)
    driving_licence_back = models.FileField(
        upload_to=upload_licence_path, null=True, blank=True)
    driving_licence_number = models.CharField(
        max_length=200, null=True, blank=True)
    driving_licence_expiry_date = models.DateField(null=True, blank=True)
    taxi_badge_number = models.CharField(max_length=200, null=True, blank=True)
    is_verified = models.BooleanField(default=False)
    current_location = models.CharField(max_length=200, null=True, blank=True)
    cur_address_coords = LocationField(map_attrs={"center": [78.742730, 23.424107], "marker_color": "blue", "placeholder":"Address Coordinates", "zoom":3},blank=True, null=True)
    request_location = models.CharField(max_length=200, null=True, blank=True)
    request_loc_coords = LocationField(map_attrs={"center": [78.742730, 23.424107], "marker_color": "blue", "placeholder":"Address Coordinates", "zoom":3},blank=True, null=True)
    home_location = models.CharField(max_length=200, null=True, blank=True)
    home_loc_coords = LocationField(map_attrs={"center": [78.742730, 23.424107], "marker_color": "blue", "placeholder":"Address Coordinates", "zoom":3},blank=True, null=True)
    has_requested = models.BooleanField(default=False)

    def __str__(self):
        return str(self.name)


class CustomerProfile(models.Model):
    user = models.ForeignKey(
        detail, on_delete=models.CASCADE, related_name='customer_profile')
    profile_picture = models.FileField(
        upload_to=upload_profile_path, null=True, blank=True)
    address = LocationField(map_attrs={"center": [
                            78.742730, 23.424107], "marker_color": "blue", "placeholder": "Address", "zoom": 3}, blank=True, null=True)
    address_text = models.CharField(max_length=400, null=True, blank=True)
    is_verified = models.BooleanField(default=False)
    is_corporate = models.BooleanField(default=False)
    corporate_cust_discount = models.FloatField( null=True, blank=True)

class CorporateCustomerProfile(models.Model):
    user = models.ForeignKey(CustomerProfile, on_delete=models.CASCADE, related_name='corporate_customer_profile')
    gst = models.IntegerField(null=True, blank=True)
    pan = models.CharField(max_length=400, null=True, blank=True)
    pan_image = models.FileField(upload_to=upload_pan_path, null=True, blank=True)

class VehicalGroup(models.Model):
    picture = models.FileField(upload_to=upload_vehicle_group_path)
    name = models.CharField(max_length=100, unique=True, primary_key=True)

    def __str__(self):
        return str(self.name)
class CarCompany(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return str(self.name)
class CarType(models.Model):
    name = models.CharField(max_length=100)
    company = models.ForeignKey(CarCompany, on_delete=models.SET_NULL, null=True)
    picture = models.FileField(upload_to=upload_car_path)
    justcab_commision = models.FloatField(null=True, blank=True)
    description = models.CharField(max_length=400)
    local_morning_surge_charge = models.FloatField(null=True, blank=True)
    local_evening_surge_charge = models.FloatField(null=True, blank=True)
    local_night_surge_charge = models.FloatField(null=True, blank=True)
    local_morning_surge_charge = models.FloatField(null=True, blank=True)
    local_evening_surge_charge = models.FloatField(null=True, blank=True)
    local_night_surge_charge = models.FloatField(null=True, blank=True)
    outstation_morning_surge_charge = models.FloatField(null=True, blank=True)
    outstation_evening_surge_charge = models.FloatField(null=True, blank=True)
    outstation_night_surge_charge = models.FloatField(null=True, blank=True)
    outstation_morning_surge_charge = models.FloatField(null=True, blank=True)
    outstation_evening_surge_charge = models.FloatField(null=True, blank=True)
    outstation_night_surge_charge = models.FloatField(null=True, blank=True)
    redeem_wallet_amount = models.IntegerField(default=500)
    local_waiting_per_min = models.IntegerField(null=True,blank=True)
    local_oneway_min_km = models.IntegerField()
    local_oneway_min_charge = models.IntegerField()
    local_oneway_rate_per_km = models.IntegerField()
    local_round_min_km = models.IntegerField()
    local_round_min_charge = models.IntegerField()
    local_round_rate_per_km = models.IntegerField()
    local_round_driver_allowance = models.IntegerField()
    outstation_waiting_per_day = models.IntegerField(null=True,blank=True)
    outstation_oneway_min_km = models.IntegerField()
    outstation_oneway_min_charge = models.IntegerField()
    outstation_oneway_rate_per_km = models.IntegerField()
    outstation_oneway_stay_charge = models.IntegerField(default=500)
    outstation_round_min_km = models.IntegerField()
    outstation_round_min_charge = models.IntegerField()
    outstation_round_rate_per_km = models.IntegerField()
    outstation_round_driver_allowance = models.IntegerField()
    outstation_round_stay_charge = models.IntegerField(default=500)
    permit = models.FloatField(default=0)
    toll = models.FloatField(default=20)
    is_active = models.BooleanField(default=True, blank=True)
    def __str__(self):
        return str(self.name + ' ' + self.description)

class VehicalType(models.Model):
    group = models.ForeignKey(VehicalGroup, on_delete=models.CASCADE)
    name = models.CharField(max_length=100, unique=True, primary_key=True)
    picture = models.FileField(upload_to=upload_vehicle_type_path)
    conviniance_charge = models.IntegerField(null=True, blank=True, default=10, help_text="In % (percentage)") 
    description = models.CharField(max_length=400)
    is_active = models.BooleanField(default=True, blank=True)
    def __str__(self):
        return str(self.name)


class VehicalCompany(models.Model):
    picture = models.FileField(upload_to=upload_vehicle_company_path)
    group = models.ManyToManyField(VehicalGroup)
    type = models.ManyToManyField(VehicalType)
    name = models.CharField(max_length=100, unique=True, primary_key=True)

    def __str__(self):
        return str(self.name)


class VehicalName(models.Model):
    picture = models.FileField(upload_to=upload_vehicle_path)
    group = models.ForeignKey(
        VehicalGroup, on_delete=models.SET_NULL, null=True)
    type = models.ForeignKey(
        VehicalType, on_delete=models.SET_NULL, null=True)
    company = models.ForeignKey(
        VehicalCompany, on_delete=models.SET_NULL, null=True)
    name = models.CharField(max_length=100, unique=True, primary_key=True)

    def __str__(self):
        return str(self.name)


class Car(models.Model):
    owner = models.ForeignKey(
        OwnerProfile, on_delete=models.CASCADE, related_name='cars')
    car_name = models.ForeignKey(
        VehicalName, on_delete=models.SET_NULL, null=True, related_name="car")
    company = models.ForeignKey(
        CarCompany, on_delete=models.SET_NULL, null=True)
    type = models.ForeignKey(CarType, on_delete=models.CASCADE)
    name = models.CharField(max_length=200, null=True)
    licence_plate_no = models.CharField(max_length=100, null=True)
    rc_book_front = models.FileField(
        upload_to=upload_car_documents_path, null=True, blank=True)
    rc_book_back = models.FileField(
        upload_to=upload_car_documents_path, null=True, blank=True)
    car_year = models.IntegerField(null=True, blank=True)
    owner_name = models.CharField(max_length=200, null=True, blank=True)
    rc_book_expiry_date = models.DateField(null=True, blank=True)
    chassi_number = models.CharField(max_length=17, null=True, blank=True)
    insurance_no = models.CharField(max_length=100, null=True, blank=True)
    insurance_picture = models.FileField(
        upload_to=upload_car_documents_path, null=True, blank=True)
    insurance_expiry_date = models.DateField(null=True, blank=True)
    insurance_company = models.CharField(max_length=200, null=True, blank=True)
    fitness_certificate = models.FileField(
        upload_to=upload_car_documents_path, null=True, blank=True)
    fitness_expiry_date = models.DateField(null=True, blank=True)
    cab_noc_agreement = models.FileField(
        upload_to=upload_car_documents_path, null=True, blank=True)
    car_front = models.FileField(
        upload_to=upload_car_path, null=True, blank=True)
    car_back = models.FileField(
        upload_to=upload_car_path, null=True, blank=True)
    car_side_left = models.FileField(
        upload_to=upload_car_path, null=True, blank=True)
    car_side_right = models.FileField(
        upload_to=upload_car_path, null=True, blank=True)
    car_interior_front = models.FileField(
        upload_to=upload_car_path, null=True, blank=True)
    car_interior_back = models.FileField(
        upload_to=upload_car_path, null=True, blank=True)
    car_dickie = models.FileField(
        upload_to=upload_car_path, null=True, blank=True)
    is_verified = models.BooleanField(default=False)
    registered_on = models.DateTimeField(default=datetime.today)
    def __str__(self):
        return str(self.name)


class Charges(models.Model):
    car = models.ForeignKey(VehicalType, on_delete=models.CASCADE)
    TRIP_VARIANT_CHOICES = [
        ('LOCAL', 'Local'),
        ('OUTSTATION', 'Outstation'),
        ('HOURLY', 'Hourly'),
    ]
    TRIP_TYPE_CHOICES = [
        ('SELF_DRIVING', 'Self Drive'),
        ('RENTAL', 'Rental'),
        ('POOLING', 'Pooling'),
    ]
    TRIP_WAY_CHOICES = [
        ('ONEWAY', 'Oneway'),
        ('ROUND', 'Round'),
    ]
    trip_type = models.CharField(
        choices=TRIP_TYPE_CHOICES, max_length=100, default="RENTAL")
    trip_variant = models.CharField(
        choices=TRIP_VARIANT_CHOICES, max_length=100)
    trip_way = models.CharField(choices=TRIP_WAY_CHOICES, max_length=100)
    min_base_charge = models.FloatField()
    redeem_wallet_percentage = models.FloatField(help_text="in percentage (%)",
        default=0, blank=True, null=True)
    morning_traffic_surge_charge = models.FloatField(
        default=1)
    evening_traffic_surge_charge = models.FloatField(
        default=1)
    night_traffic_surge_charge = models.FloatField(
        default=1)
    easy_I_route_surge = models.FloatField(
        default=1, blank=True, null=True, help_text="values should be in % (percentage)")  # in percentage
    easy_II_route_surge = models.FloatField(
        default=1, blank=True, null=True, help_text="values should be in % (percentage)")  # in percentage
    remote_I_route_surge = models.FloatField(
        default=1, blank=True, null=True, help_text="values should be in % (percentage)")  # in percentage
    remote_II_route_surge = models.FloatField(
        default=1, blank=True, null=True, help_text="values should be in % (percentage)")  # in percentage
    petrol_fuel_surge = models.FloatField(
        default=1, blank=True, null=True,)
    disel_fuel_surge = models.FloatField(
        default=1, blank=True, null=True,)
    cng_fuel_surge = models.FloatField(
        default=1, blank=True, null=True,)
    electric_fuel_surge = models.FloatField(
        default=1, blank=True, null=True,)
    entertainment_charge = models.FloatField(
        default=1, blank=True, null=True,)  # defa
    ride_time_charge = models.FloatField(default=1)
    vehical_waiting_charge = models.FloatField(default=1
                                               )
    driver_waiting_charge = models.FloatField(default=1
                                              )
    driver_waiting_allowances_charge = models.FloatField(default=1
                                                         )
    driver_waiting_night_allowances_charge = models.FloatField(default=1
                                                               )
    driver_waiting_stay_allowances_charge = models.FloatField(default=1
                                                              )
    
    Kms_covered_in_base_fare = models.FloatField(default=1
                                                 )
    minimum_km = models.FloatField(default=1)
    rate_per_km = models.FloatField(default=1)

    def __str__(self):
        return f"{self.car} ({self.trip_type}-{self.trip_variant}-{self.trip_way})"
    


class Trip(models.Model):
    trip_no = models.CharField(max_length=100, default='0')
    customer = models.ForeignKey(CustomerProfile, on_delete=models.SET_NULL,blank=True, null=True, related_name='trips')
    owner = models.ForeignKey(OwnerProfile, on_delete=models.SET_NULL,blank=True, null=True, related_name='trips')
    driver = models.ForeignKey(DriverProfile, on_delete=models.SET_NULL,blank=True, null=True, related_name='trips')
    car = models.ForeignKey(Car, on_delete=models.SET_NULL,blank=True, null=True)
    booking_date = models.DateField(default=datetime.today)
    booking_time = models.TimeField(default=timezone.now)
    pickup_date = models.DateField()
    pickup_time = models.TimeField()
    drop_time = models.DateTimeField()
    car_type = models.ForeignKey(VehicalType, on_delete=models.SET_NULL, null=True)
    pickup_location = LocationField(map_attrs={"center": [
                                    78.742730, 23.424107], "marker_color": "blue", "placeholder": "Pickup Location", "zoom": 3}, null=True)
    drop_location = LocationField(map_attrs={"center": [
                                  78.742730, 23.424107], "marker_color": "red", "placeholder": "Drop Location", "zoom": 3}, null=True)
    pickup_address = models.CharField(max_length=300, blank=True)
    pickup_city = models.CharField(max_length=100, blank=True)
    pickup_state = models.CharField(max_length=100, blank=True)
    drop_address = models.CharField(max_length=300, blank=True)
    drop_city = models.CharField(max_length=100, blank=True, default='Mumbai')
    drop_state = models.CharField(max_length=100, blank=True, default="Goa")
    round_trip = models.BooleanField(default=False)
    days = models.IntegerField(null=True, blank=True)
    bill_amount = models.IntegerField(null=True, blank=True)
    day_charges = models.IntegerField(null=True, blank=True)
    extra_dist_charges = models.IntegerField(null=True, blank=True)
    total_driver_allowance = models.IntegerField(null=True, blank=True)
    fare = models.IntegerField(null=True, blank=True)
    tax = models.IntegerField(null=True, blank=True)
    tax_percent = models.IntegerField(null=True, blank=True)
    vendor_amount = models.IntegerField(null=True, blank=True)
    distance = models.IntegerField(null=True, blank=True)
    is_verified = models.BooleanField(default=False)
    driver_is_visible = models.BooleanField(default=False)
    traveller_is_visible = models.BooleanField(default=False)
    start_otp = models.CharField(max_length=10, null=True, blank=True)
    end_otp = models.CharField(max_length=10, null=True, blank=True)
    is_started = models.BooleanField(default=False)
    is_complete = models.BooleanField(default=False)
    rejected_by = models.ManyToManyField(OwnerProfile, related_name='rejected_trips', blank=True)
    is_canceled = models.BooleanField(default=False)
    trip_perimeter = models.CharField(max_length=100, default='local')
    toll_charges = models.IntegerField(null=True, blank=True, default=20)
    rejected_by = models.ManyToManyField(
        OwnerProfile, related_name='rejected_trips')
    is_canceled = models.BooleanField(default=False)
    TRIP_VARIANT_CHOICES = [
        ('LOCAL', 'Local'),
        ('OUTSTATION', 'Outstation'),
        ('HOURLY', 'Hourly'),
    ]
    TRIP_TYPE_CHOICES = [
        ('RENTAL', 'Rental'),
        ('SELF_DRIVING', 'Self Drive'),
        ('POOLING', 'Pooling'),
    ]
    TRIP_WAY_CHOICES = [
        ('ONEWAY', 'Oneway'),
        ('ROUND', 'Round'),

    ]
    trip_type = models.CharField(
        choices=TRIP_TYPE_CHOICES, max_length=100, default="RENTAL")
    trip_variant = models.CharField(
        choices=TRIP_VARIANT_CHOICES, max_length=100, default="LOCAL")
    trip_way = models.CharField(choices=TRIP_WAY_CHOICES, max_length=100)

    def __str__(self):
        return str(self.pickup_city + " to " + self.drop_city)

    def generate_payment_detail_advance(self):
        customer_wallet = self.customer.wallet.first()
        self.payment_detail.create(
            to_be_paid=self.bill_amount,
            vendor_amount=self.vendor_amount,
            vendor_balance=self.vendor_amount,
            customer_balance=-self.bill_amount
        )
        self.save()
        customer_wallet.balance -= self.bill_amount
        customer_wallet.save()

    def set_vendor_amounts(self, payment_detail):
        payment_detail.vendor_amount = self.vendor_amount
        payment_detail.vendor_balance = self.vendor_amount
        payment_detail.save()
    # def vendor_payment_cash(self, payment_detail):
    #     customer_wallet = self.customer.wallet.first()
    #     vendor_wallet = self.owner.wallet.first()
    #     cash_amount = abs(payment_detail.customer_balance)
    #     payment_detail.vendor_amount = self.vendor_amount,
    #     payment_detail.vendor_balance = self.vendor_amount,
    #     payment_detail.customer_balance = 0
    #     payment_detail.
    #     # self.payment_detail.create(
    #     #     to_be_paid = self.bill_amount,
    #     #     vendor_amount = self.vendor_amount,
    #     #     vendor_balance = self.vendor_amount,
    #     #     customer_balance = -self.bill_amount
    #     # )
    #     self.save()
    #     customer_wallet.balance -= self.bill_amount
    #     customer_wallet.save()

    def generate_otp(self):
        self.start_otp = random.randint(100000, 9999999)
        self.end_otp = random.randint(100000, 999999)
        self.save()


class VendorTrip(models.Model):
    trip_no = models.CharField(max_length=100, default='0')
    poster = models.ForeignKey(OwnerProfile, on_delete=models.SET_NULL,
                               blank=True, null=True, related_name='posted_trips')
    owner = models.ForeignKey(OwnerProfile, on_delete=models.SET_NULL,
                              blank=True, null=True, related_name='vendor_trips')
    driver = models.ForeignKey(DriverProfile, on_delete=models.SET_NULL,
                               blank=True, null=True, related_name='vendor_trips')
    car = models.ForeignKey(
        Car, on_delete=models.SET_NULL, blank=True, null=True)
    pickup_date = models.DateField()
    pickup_time = models.TimeField()
    drop_time = models.DateTimeField()
    car_type = models.ForeignKey(CarType, on_delete=models.SET_NULL, null=True)
    pickup_location = LocationField(blank=True, map_attrs={"center": [
                                    78.742730, 23.424107], "marker_color": "blue", "placeholder": "Pickup Location", "zoom": 3}, null=True)
    drop_location = LocationField(blank=True, map_attrs={"center": [
                                  78.742730, 23.424107], "marker_color": "red", "placeholder": "Drop Location", "zoom": 3}, null=True)
    pickup_address = models.CharField(max_length=300, blank=True)
    pickup_city = models.CharField(max_length=100, blank=True)
    pickup_state = models.CharField(max_length=100, blank=True)
    drop_address = models.CharField(max_length=300, blank=True)
    drop_city = models.CharField(max_length=100, blank=True, default='Mumbai')
    drop_state = models.CharField(max_length=100, blank=True, default="Goa")
    round_trip = models.BooleanField(default=False)
    days = models.IntegerField(null=True, blank=True)
    vendor_amount = models.IntegerField(null=True, blank=True)
    distance = models.IntegerField(null=True, blank=True)
    is_verified = models.BooleanField(default=False)
    acceptor_is_visible = models.BooleanField(default=False)
    is_started = models.BooleanField(default=False)
    is_complete = models.BooleanField(default=False)
    rejected_by = models.ManyToManyField(OwnerProfile, blank=True, related_name='rejected_vendor_trips')
    is_canceled = models.BooleanField(default=False)
    is_demo = models.BooleanField(default=False)

    def __str__(self):
        return str(self.pickup_city + " to " + self.drop_city)


class TravellersInformation(models.Model):
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE,
                             related_name='traveller', null=True, blank=True)
    vendor_trip = models.ForeignKey(
        VendorTrip, on_delete=models.CASCADE, related_name='traveller', null=True, blank=True)
    name = models.CharField(max_length=200)
    phone = models.CharField(max_length=20)
    email = models.EmailField(null=True, blank=True)
    address = models.CharField(max_length=400)
    no_of_travellers = models.IntegerField()
    no_of_bags = models.IntegerField()
    special_instructions = models.CharField(
        max_length=400, blank=True, null=True)
    carrier_required = models.BooleanField(default=False)


class Event(models.Model):
    user = models.ForeignKey(
        detail, null=True, on_delete=models.SET_NULL, related_name='events')
    owner = models.ForeignKey(OwnerProfile, null=True,
                              on_delete=models.SET_NULL, related_name='events')
    customer = models.ForeignKey(
        CustomerProfile, null=True, on_delete=models.SET_NULL, related_name='events')
    driver = models.ForeignKey(
        DriverProfile, null=True, on_delete=models.SET_NULL, related_name='events')
    car = models.ForeignKey(
        Car, null=True, on_delete=models.SET_NULL, related_name='events')
    trip = models.ForeignKey(
        Trip, null=True, on_delete=models.SET_NULL, related_name='events')
    vendor_trip = models.ForeignKey(
        VendorTrip, null=True, on_delete=models.SET_NULL, related_name='events')
    car_type = models.ForeignKey(
        CarType, null=True, on_delete=models.SET_NULL, related_name='events')
    text = models.CharField(max_length=300)
    time = models.DateTimeField(auto_now_add=True)
    username = models.CharField(max_length=200)
    email = models.EmailField()


class Notification(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='admin_notifications', null=True)
    to = models.ForeignKey(detail, on_delete=models.CASCADE,
                           related_name='notifications', null=True)
    text = models.CharField(max_length=200, null=True)
    link_id = models.IntegerField()
    customer_profile = models.BooleanField(default=False)
    owner_profile = models.BooleanField(default=False)
    booking = models.BooleanField(default=False)
    date = models.DateTimeField(auto_now=True)
    seen = models.BooleanField(default=False)

    def __str__(self):
        if self.to:
            return str(self.to)
        else:
            return 'admin - ' + str(self.user)

# class address(models.Model):
#     name = models.CharField(max_length=100)
#     user = models.ForeignKey(detail, on_delete=models.CASCADE, null=True)
#     location = LocationField(blank=True, map_attrs={"center": [78.742730, 23.424107], "marker_color": "red", "placeholder":"Drop Location", "zoom":3}, null=True)
#     address = models.CharField(max_length=300, blank=True)
#     city = models.CharField(max_length=100, blank=True)
#     state = models.CharField(max_length=100, blank=True)

class Route(models.Model):
    # Data should be filled according to this page https://en.wikipedia.org/wiki/Classification_of_Indian_cities
    ROUTE_TYPE_CHOICES = [
        # ('EASY-I', 'Easy-I'),
        # ('EASSY-II', 'Easy-II'),
        # ('REMOTE-I', 'Remote-I'),
        # ('REMOTE-II', 'Remote-II'),
        ('A-I', 'A-I'),
        ('A', 'A'),
        ('B-I', 'B-I'),
        ('B', 'B'),
        ('NONE', 'None'),
    ]
    destination = models.CharField(max_length=100)
    route_type = models.CharField(
        choices=ROUTE_TYPE_CHOICES, max_length=100, default="NONE")

    def __str__(self):
        return f"{self.destination}-{self.route_type}"


class Fuel(models.Model):
    FUEL_TYPE_CHOICES = [
        ('PETROL', 'Petrol'),
        ('DISEL', 'Disel'),
        ('CNG', 'CNG'),
        ('ELECTRIC', 'Electric'),

    ]

    fuel = models.CharField(choices=FUEL_TYPE_CHOICES,
                            max_length=100, unique=True)
    priority=models.IntegerField()
    def __str__(self):
        return self.fuel


class Fuel_Route(models.Model):
    
    frm = models.CharField(max_length=100)
    to = models.CharField(max_length=100)
    fuel_type = models.ManyToManyField(Fuel)  # multiple

    def __str__(self):
        return f"{self.frm} to {self.to}"

class Toll_Permit_Parking(models.Model):
    route_from=models.CharField(max_length=100)
    route_to=models.CharField(max_length=100)
    vehicle_group=models.ForeignKey(VehicalGroup, on_delete=models.CASCADE)
    toll=models.PositiveIntegerField(default=0)
    permit=models.PositiveIntegerField(default=0)
    parking=models.PositiveIntegerField(default=0)
    def __str__(self):
        return f"{self.vehicle_group}-{self.route_from} to {self.route_to}"

class CouponType(models.Model):
    name=models.CharField(max_length=100)
    def __str__(self):
        return f"{self.name}"

class Coupon(models.Model):
    TRIP_VARIANT_CHOICES = [
        ('LOCAL', 'Local'),
        ('OUTSTATION', 'Outstation'),
        ('HOURLY', 'Hourly'),
    ]
    TRIP_TYPE_CHOICES = [
        ('RENTAL', 'Rental'),
        ('SELF_DRIVING', 'Self Drive'),
        ('POOLING', 'Pooling'),
    ]
    TRIP_WAY_CHOICES = [
        ('ONEWAY', 'Oneway'),
        ('ROUND', 'Round'),

    ]
    vehicle_group=models.ForeignKey(VehicalGroup,on_delete=models.CASCADE)
    vehicle_type=models.ForeignKey(VehicalType,on_delete=models.CASCADE)
    trip_type = models.CharField(choices=TRIP_TYPE_CHOICES, max_length=100, default="RENTAL")
    trip_variant = models.CharField(choices=TRIP_VARIANT_CHOICES, max_length=100, default="LOCAL")
    trip_way = models.CharField(choices=TRIP_WAY_CHOICES, max_length=100)
    coupon_type=models.ForeignKey(CouponType,on_delete=models.CASCADE,null=True)
    coupon_name=models.CharField(max_length=100)
    coupon_code=models.PositiveIntegerField()
    coupon_value=models.PositiveIntegerField()
    def __str__(self):
        return f"{self.coupon_code}-{self.coupon_name} {self.vehicle_type}"

