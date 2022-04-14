from main.models import *
from wallet.models import *
import random

# PaymentDetail.objects.all().delete()
# Wallet.objects.all().delete()
# Transaction.objects.all().delete()

det = detail.objects.filter(email='customer@gmail.com').first()
vdet = detail.objects.filter(email='vendor@gmail.com').first()
odet = detail.objects.filter(email='yogita@raymond.in').first()
cust_profile = CustomerProfile.objects.get(user=det)
ven_profile = OwnerProfile.objects.get(user=vdet)
own_profile = OwnerProfile.objects.get(user=odet)
# trip =  Trip.objects.filter(owner=ven_profile, customer=cust_profile).first()
# trip.customer = cust_profile
# trip.owner = ven_profile
# trip.save()
# pd = PaymentDetail(
#     trip = trip,
#     to_be_paid = 50000,
#     vendor_amount = 40000,
#     customer_balance = -50000,
#     vendor_balance = 40000
# )
# pd.save()

# c_wallet = Wallet(
#     customer = trip.customer,
#     balance = 0,
#     redeem_balance = 1000,
#     is_active = True,
#     deactivate_amount = 0
# )
# c_wallet.save()

# v_wallet = Wallet(
#     owner = trip.owner,
#     balance = 1000,
#     is_active = True,
#     deactivate_amount = 1000
# )
# v_wallet.save()

v_wallet = ven_profile.wallet.first()
c_wallet = cust_profile.wallet.first()
v_wallet.balance = 1000
c_wallet.balance = 0
c_wallet.save()
v_wallet.save()
# Trip.objects.all().delete()
# o_wallet = own_profile.wallet.first()
# pd = trip.payment_detail.first()

# v_wallet.transactions.all().delete()
# for i in range(50):
#     amt = random.randint(500, 10000)
#     redeem = random.randint(100,1000)
#     amt = amt-redeem
#     c_wallet.customer_redeem(pd, redeem)
#     c_wallet.customer_to_company_ol(pd, amt, 'razor_payment_id', 'razor_order_id','razor_signature')

# for i in range(50):
#     amt = random.randint(500,10000)
#     o_wallet.vendor_to_company_ol(amt, 'razor_payment_id', 'razor_order_id','razor_signature')


# trips = Trip.objects.all()
# for trip in trips:
#     trip.is_started = False
#     trip.is_complete = False
#     trip.is_verified = True
#     trip.is_canceled = False
#     trip.owner = None
#     trip.driver = None
#     trip.car = None
#     trip.save()

# vendor_trips = VendorTrip.objects.all()
# for trip in vendor_trips:
#     trip.is_started = False
#     trip.is_complete = False
#     trip.is_verified = True
#     trip.is_canceled = False
#     trip.owner = None
#     trip.driver = None
#     trip.car = None
#     trip.save()