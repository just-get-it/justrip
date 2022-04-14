from django.db import models
from main.models import Trip, OwnerProfile, CustomerProfile
from .errors import InsufficientBalance
import razorpay
# Razorpay ID and Secret
razorpay_id = "rzp_live_048zfpCdwS3iFX"
razorpay_secret = "KclezNB6i7tv5h1UAU4U8AXp"


# Create your models here.
class Wallet(models.Model):
    customer = models.ForeignKey(CustomerProfile, on_delete=models.SET_NULL, null=True, blank=True, related_name='wallet')
    owner = models.ForeignKey(OwnerProfile, on_delete=models.SET_NULL, null=True, blank=True, related_name='wallet')
    balance = models.IntegerField(default=0)
    redeem_balance = models.IntegerField(default=0)
    is_active = models.BooleanField(default=False)
    deactivate_amount = models.IntegerField(default=0)

    # def __str__(self):
    #     if self.customer:
    #         return str(self.customer.user.name) 
    #     else:
    #         return str(self.owner.user.name)


    #################################################################
    ################# CUSTOMER WALLET METHODS #######################
    #################################################################


    # CUSTOMER PAYS TO VENDOR:
    def customer_to_vendor_payment(self, paymentdetail):
        vendor_wallet = paymentdetail.trip.owner.wallet.first()
        amount = abs(paymentdetail.customer_balance)
        # CUSTOMER 
        paymentdetail.customer_balance += amount
        paymentdetail.full_payment = amount
        self.balance += amount
        self.transactions.create(
            credit = True,
            paymentdetail = paymentdetail,
            running_balance = self.balance,
            running_balance_redeem = self.redeem_balance,
            amount = amount,
            is_online = False,
            customer_to_vendor = True,
            status = 'Paid to driver'
        )
        self.save()
        paymentdetail.is_complete_customer = True
        paymentdetail.final_payment = amount
        paymentdetail.save()
        # VENDOR
        vendor_wallet.balance -= amount
        paymentdetail.vendor_amount = paymentdetail.trip.vendor_amount
        paymentdetail.vendor_balance -= amount
        vendor_wallet.transactions.create(
            credit = True,
            paymentdetail = paymentdetail,
            running_balance = vendor_wallet.balance,
            amount = amount,
            is_online = False,
            customer_to_vendor = True,
            status = 'Received Cash'
        )
        vendor_wallet.save()
        # if balance is less then minimun balance then deactivate
        if vendor_wallet.balance < vendor_wallet.deactivate_amount:
            vendor_wallet.owner.is_active = False
        paymentdetail.save()

    # CUSTOMER STARTS BOOKING
    def start_booking_customer(self, paymentdetail):
        self.balance -= paymentdetail.to_be_paid
        paymentdetail.customer_balance = -paymentdetail.to_be_paid
        self.transactions.create(
            debit = True,
            paymentdetail = paymentdetail,
            running_balance = self.balance,
            amount = paymentdetail.to_be_paid,
            is_online = True,
            company_to_customer = True,
        )
        self.save()
        paymentdetail.save()

    # CUSTOMER REDEEMS AMOUNT FROM WALLET AND GETS CASHBACK
    def customer_redeem(self, paymentdetail, amount):
        # If wallet amount less than redeem raise an error
        if self.redeem_balance < amount:
            raise InsufficientBalance
        # paymentdetail.customer_balance += amount
        # paymentdetail.save()
        # Redeems
        self.redeem_balance -= amount
        self.transactions.create(
            debit = True,
            paymentdetail = paymentdetail,
            running_balance_redeem = self.redeem_balance,
            running_balance = self.balance,
            amount = amount,
            is_online = True,
            is_redeemed = True, 
            customer_to_company = True,
            status = 'Successfull'
        )
        # Cashback
        self.redeem_balance += amount
        self.transactions.create(
            credit = True,
            paymentdetail = paymentdetail,
            running_balance_redeem = self.redeem_balance,
            running_balance = self.balance,
            amount = amount,
            is_online = True,
            is_cashback = True, 
            company_to_customer = True,
            status = 'Successfull'
        )
        self.save()

    # CUSTOMER PAYS VIA RAZORPAY
    def customer_to_company_generate_trip_transaction(self, paymentdetail):
        amount = abs(paymentdetail.customer_balance)
        transaction = self.transactions.create(
            credit = True,
            paymentdetail = paymentdetail,
            amount = amount,
            is_online = True,
            running_balance = self.balance,
            running_balance_redeem = self.redeem_balance,
            customer_to_company = True,
            status = "Failed"
        )
        t_receipt = 'transaction_rcptid_' + str(transaction.id)
        notes = {'Shipping address': "None"}
        transaction_dict = {'amount': amount*100, "currency" : 'INR', "receipt" : t_receipt, "notes": notes, "payment_capture": "1"}
        client = razorpay.Client(auth=(razorpay_id, razorpay_secret))
        razor_reponse = client.order.create(transaction_dict)
        transaction.razorpay_order_id = razor_reponse.get('id')
        transaction.status = "Failed"
        transaction.save()
        self.save() 
        self.save()
        return transaction.razorpay_order_id

    # CUSTOMER GENERATE ADVANCE PAYMENT TRANSACTION
    def customer_to_company_generate_trip_advance_transaction(self, paymentdetail):
        amount = abs(paymentdetail.customer_balance)
        amount = int(amount * 30/100)
        transaction = self.transactions.create(
            credit = True,
            paymentdetail = paymentdetail,
            amount = amount,
            is_online = True,
            running_balance = self.balance,
            running_balance_redeem = self.redeem_balance,
            customer_to_company = True,
            status = "Failed"
        )
        t_receipt = 'transaction_rcptid_' + str(transaction.id)
        notes = {'Shipping address': "None"}
        transaction_dict = {'amount': amount*100, "currency" : 'INR', "receipt" : t_receipt, "notes": notes, "payment_capture": "1"}
        client = razorpay.Client(auth=(razorpay_id, razorpay_secret))
        razor_reponse = client.order.create(transaction_dict)
        transaction.razorpay_order_id = razor_reponse.get('id')
        transaction.status = "Failed"
        transaction.save()
        self.save() 
        self.save()
        return transaction.razorpay_order_id
    
    # CUSTOMER GENERATE NEW TRANSACTION
    def customer_to_company_generate_transaction(self, amount):
        transaction = self.transactions.create(
            credit = True,
            amount = amount,
            running_balance = self.balance,
            running_balance_redeem = self.redeem_balance,
            is_online = True,
            customer_to_company = True,
            status = "Failed"
        )
        t_receipt = 'transaction_rcptid_' + str(transaction.id)
        notes = {'Shipping address': "None"}
        transaction_dict = {'amount': amount*100, "currency" : 'INR', "receipt" : t_receipt, "notes": notes, "payment_capture": "1"}
        client = razorpay.Client(auth=(razorpay_id, razorpay_secret))
        razor_reponse = client.order.create(transaction_dict)
        transaction.razorpay_order_id = razor_reponse.get('id')
        transaction.status = "Failed"
        transaction.save()
        self.save() 
        return transaction.razorpay_order_id
    #################################################################
    ################## VENDOR WALLET METHODS ########################
    #################################################################
    def vendor_to_company_generate_transaction(self, amount):
        transaction = self.transactions.create(
            credit = True,
            amount = amount,
            running_balance = self.balance,
            is_online = True,
            vendor_to_company = True,
            status = "Failed"
        )
        t_receipt = 'transaction_rcptid_' + str(transaction.id)
        notes = {'Shipping address': "None"}
        transaction_dict = {'amount': amount*100, "currency" : 'INR', "receipt" : t_receipt, "notes": notes, "payment_capture": "1"}
        client = razorpay.Client(auth=(razorpay_id, razorpay_secret))
        razor_reponse = client.order.create(transaction_dict)
        transaction.razorpay_order_id = razor_reponse.get('id')
        transaction.status = "Failed"
        transaction.save()
        self.save() 
        return transaction.razorpay_order_id
    def vendor_to_company_of_order_ol(self, paymentdetail, razorpay_payment_id, razorpay_order_id, razorpay_signature):
        amount = abs(paymentdetail.vendor_balance)
        paymentdetail.vendor_balance += amount
        self.balance += amount
        self.transactions.create(
            credit = True,
            paymentdetail = paymentdetail,
            amount = amount,
            is_online = True,
            vendor_to_company = True,
            razorpay_order_id=razorpay_order_id,
            razorpay_payment_id=razorpay_payment_id,
            razorpay_signature=razorpay_signature
        )
        self.save() 
    
    def vendor_to_company_ol(self, amount, razorpay_payment_id, razorpay_order_id, razorpay_signature):
        self.balance += amount
        self.transactions.create(
            credit = True,
            amount = amount,
            running_balance = self.balance,
            is_online = True,
            vendor_to_company = True,
            razorpay_order_id=razorpay_order_id,
            razorpay_payment_id=razorpay_payment_id,
            razorpay_signature=razorpay_signature
        )
        self.save() 
    
    def company_to_vendor(self, amount, note):
        self.balance += amount
        if amount > 0:
            credit = True
            debit = False
        else:
            credit = False
            debit = True
        self.transactions.create(
            credit = credit,
            debit = debit,
            amount = amount,
            is_online = True,
            company_to_vendor = True,
            note = note,
            status = 'Received Successfully'
        )
        self.save() 

    def company_to_customer(self, amount, note):
        self.balance += amount
        if amount > 0:
            credit = True
            debit = False
        else:
            credit = False
            debit = True
        self.transactions.create(
            credit = credit,
            debit = debit,
            amount = amount,
            is_online = True,
            company_to_customer = True,
            note = note,
            status = 'Received Successfully'
        )
        self.save()
        
        
    # # CUSTOMER STARTS BOOKING
    # def start_booking_vendor(self, paymentdetail):
    #     self.balance += paymentdetail.vendor_amount
    #     paymentdetail.vendor_balance = paymentdetail.vendor_amount
    #     self.transactions.create(
    #         credit = True,
    #         paymentdetail = paymentdetail,
    #         running_balance = self.balance,
    #         amount = paymentdetail.to_be_paid,
    #         is_online = True,
    #         company_to_customer = True,
    #     )
    #     self.save()
    #     paymentdetail.save()



class PaymentDetail(models.Model):
    trip = models.ForeignKey(Trip, on_delete=models.SET_NULL, null=True, blank=True, related_name='payment_detail')
    to_be_paid = models.IntegerField(default=0, null=True, blank=True)
    vendor_amount = models.IntegerField(default=0, null=True, blank=True)
    is_complete_vendor = models.BooleanField(default=False, blank=True)
    is_complete_customer = models.BooleanField(default=False, blank=True)
    vendor_balance = models.IntegerField(default=None, blank=True, null=True)
    customer_balance = models.IntegerField(default=None, blank=True, null=True)
    partial_payment = models.IntegerField(default=None, blank=True, null=True)
    final_payment = models.IntegerField(default=None, blank=True, null=True)

    def __str__(self):
        return str(self.trip)


class Transaction(models.Model):
    paymentdetail = models.ForeignKey(PaymentDetail, on_delete=models.SET_NULL, related_name='transactions', null=True)
    wallet = models.ForeignKey(Wallet, on_delete=models.SET_NULL, related_name='transactions', null=True)
    amount = models.IntegerField(default=0)
    debit = models.BooleanField(default=False)
    credit = models.BooleanField(default=False)
    running_balance = models.IntegerField(default=0)
    running_balance_redeem = models.IntegerField(default=0)
    is_redeemed = models.BooleanField(default=False)
    is_cashback = models.BooleanField(default=False)
    is_online = models.BooleanField()
    razorpay_payment_id = models.CharField(max_length = 256, null=True)
    razorpay_order_id = models.CharField(max_length = 256, null=True)
    razorpay_signature = models.CharField(max_length = 256, null=True)
    vendor_to_customer = models.BooleanField(default=False)
    vendor_to_company = models.BooleanField(default=False)
    customer_to_vendor = models.BooleanField(default=False)
    customer_to_company = models.BooleanField(default=False)
    company_to_customer = models.BooleanField(default=False)
    company_to_vendor = models.BooleanField(default=False)
    time = models.DateTimeField(auto_now_add=True)
    note = models.CharField(max_length=400, null=True, blank=True)
    status = models.CharField(max_length=400, null=True, blank=True)
    def __str__(self):
        return str(self.wallet)