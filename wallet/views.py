from django.shortcuts import render, redirect
from django.core.paginator import Paginator
from main.models import *
from .models import *
from django.contrib import messages

# Create your views here.
def wallet_index(request):
    if request.user.is_authenticated:
        details = detail.objects.filter(email=request.user.email).first()
        owner = OwnerProfile.objects.filter(user=details).first()
        customer = CustomerProfile.objects.filter(user=details).first()
        if owner:
            if owner.is_owner:
                return redirect('owner_wallet')
            elif owner.is_vendor:
                return redirect('vendor_wallet')
        if customer:
            return redirect('customer_wallet')
        if request.user.is_superuser:
            return redirect('admin_wallet')
        else:
            return redirect('index')
    else:
        return redirect('login_page')

def customer_wallet(request):
    if request.user.is_authenticated:
        details = detail.objects.filter(email=request.user.email).first()
        owner = OwnerProfile.objects.filter(user=details).first()
        customer = CustomerProfile.objects.filter(user=details).first()
        if owner:
            if owner.is_owner:
                return redirect('owner_wallet')
            elif owner.is_vendor:
                return redirect('vendor_wallet')
        if request.user.is_superuser:
            return redirect('admin_wallet')
        # Customer wallet code
        wallet = customer.wallet.first()
        if request.POST.get('razorpay_signature'):
            razorpay_payment_id = request.POST.get('razorpay_payment_id')
            razorpay_order_id = request.POST.get('razorpay_order_id')
            razorpay_signature = request.POST.get('razorpay_signature')
            razorData = {'razorpay_payment_id':razorpay_payment_id, 'razorpay_order_id':razorpay_order_id, 'razorpay_signature':razorpay_signature}
            client = razorpay.Client(auth=(razorpay_id, razorpay_secret))
            client.utility.verify_payment_signature(razorData)
            transaction = Transaction.objects.get(razorpay_order_id=razorpay_order_id)
            transaction.razorpay_payment_id = razorpay_payment_id
            transaction.razorpay_signature = razorpay_signature
            transaction.status = "Paid Successfully"
            transaction.running_balance = wallet.balance
            if transaction.credit:
                wallet.balance += transaction.amount
                transaction.running_balance = wallet.balance
            transaction.save()
            wallet.save()
            if request.POST.get('add_wallet'):
                messages.success(request, 'Amount added to wallet successfully!')
            return redirect('customer_wallet')
        if request.POST.get('wallet_add'):
            amount = request.POST.get('amount')
            amount = int(amount)
            razorpay_od_id = wallet.customer_to_company_generate_transaction(amount)
            return render(request, 'customer_make_payment.html', {'razorpay_od_id':razorpay_od_id, 'amount':amount, 'profile':customer, 'type':'wallet_add'})
        transactions = wallet.transactions.all().order_by('-time')
        # Pagination
        page = request.GET.get('page', 1)
        paginator = Paginator(transactions, 15)
        try:
            transactions = paginator.page(page)
        except PageNotAnInteger:
            transactions = paginator.page(1)
        except EmptyPage:
            transactions = paginator.page(paginator.num_pages)
        data = {'transactions': transactions, 'wallet':wallet, 'details':details}
        return render(request, 'customer_wallet.html', data)
    else:
        return redirect('login_page')

def customer_transaction_details(request, transaction_id):
    if request.user.is_authenticated:
        details = detail.objects.filter(email=request.user.email).first()
        owner = OwnerProfile.objects.filter(user=details).first()
        customer = CustomerProfile.objects.filter(user=details).first()
        if owner:
            if owner.is_owner:
                return redirect('owner_wallet')
            elif owner.is_vendor:
                return redirect('vendor_wallet')
        if request.user.is_superuser:
            return redirect('admin_wallet')
        # Check if transaction belongs to customer
        transaction = Transaction.objects.filter(pk=transaction_id).first()
        customer_wallet = customer.wallet.first()
        customer_transactions = customer_wallet.transactions.all()
        if transaction not in customer_transactions:
            messages.error(request, 'Sorry, this transaction does not belong to you')
            return redirect('wallet_index')
        if not transaction:
            messages.error(request, 'Sorry, transaction does not exist!')
            return redirect('wallet_index')
        data = {'transaction': transaction, 'details':details}
        return render(request, 'customer_transaction_details.html', data)
    else:
        return redirect('login_page')

def vendor_wallet(request):
    if request.user.is_authenticated:
        details = detail.objects.filter(email=request.user.email).first()
        owner = OwnerProfile.objects.filter(user=details).first()
        customer = CustomerProfile.objects.filter(user=details).first()
        if customer:
            return redirect('customer_wallet')
        if owner:
            if owner.is_owner:
                return redirect('owner_wallet')
        if request.user.is_superuser:
            return redirect('admin_wallet')
        # Customer wallet code
        wallet = owner.wallet.first()
        if request.POST.get('razorpay_signature'):
            razorpay_payment_id = request.POST.get('razorpay_payment_id')
            razorpay_order_id = request.POST.get('razorpay_order_id')
            razorpay_signature = request.POST.get('razorpay_signature')
            razorData = {'razorpay_payment_id':razorpay_payment_id, 'razorpay_order_id':razorpay_order_id, 'razorpay_signature':razorpay_signature}
            client = razorpay.Client(auth=(razorpay_id, razorpay_secret))
            client.utility.verify_payment_signature(razorData)
            transaction = Transaction.objects.get(razorpay_order_id=razorpay_order_id)
            transaction.razorpay_payment_id = razorpay_payment_id
            transaction.razorpay_signature = razorpay_signature
            transaction.status = "Paid Successfully"
            if transaction.credit:
                wallet.balance += transaction.amount
                if wallet.balance >= wallet.deactivate_amount:
                    wallet.is_active = True
                    owner.is_active = True
                wallet.save()
            transaction.running_balance = wallet.balance
            transaction.save()
            if request.POST.get('security'):
                messages.success(request, 'Security deposit added successfully!')
            else:
                messages.success(request, 'Amount added to wallet successfully!')
            return redirect('vendor_wallet')
        if request.POST.get('razorpay_security'):
            amount = wallet.deactivate_amount - wallet.balance
            razorpay_od_id = wallet.vendor_to_company_generate_transaction(amount)
            return render(request, 'vendor_make_payment.html', {'razorpay_od_id':razorpay_od_id, 'amount':amount, 'profile':owner, 'type':'security'})
        if request.POST.get('wallet_add'):
            amount = request.POST.get('amount')
            amount = int(amount)
            razorpay_od_id = wallet.vendor_to_company_generate_transaction(amount)
            return render(request, 'vendor_make_payment.html', {'razorpay_od_id':razorpay_od_id, 'amount':amount, 'profile':owner, 'type':'wallet_add'})
        transactions = wallet.transactions.all().order_by('-time')
        # Pagination
        page = request.GET.get('page', 1)
        paginator = Paginator(transactions, 15)
        try:
            transactions = paginator.page(page)
        except PageNotAnInteger:
            transactions = paginator.page(1)
        except EmptyPage:
            transactions = paginator.page(paginator.num_pages)
        data = {'transactions': transactions, 'wallet':wallet, 'details':details}
        # if vendor has less wallet amount then deactivate amount s
        if wallet.balance < wallet.deactivate_amount:
            data['security_deposit'] = wallet.deactivate_amount - wallet.balance
        return render(request, 'vendor_wallet.html', data)
    else:
        return redirect('login_page')

def vendor_transaction_details(request, transaction_id):
    if request.user.is_authenticated:
        details = detail.objects.filter(email=request.user.email).first()
        owner = OwnerProfile.objects.filter(user=details).first()
        customer = CustomerProfile.objects.filter(user=details).first()
        if customer:
            return redirect('customer_wallet')
        if owner:
            if owner.is_owner:
                return redirect('owner_wallet')
        if request.user.is_superuser:
            return redirect('admin_wallet')
        # Check if transaction belongs to customer
        transaction = Transaction.objects.filter(pk=transaction_id).first()
        wallet = owner.wallet.first()
        owner_transactions = wallet.transactions.all()
        if transaction not in owner_transactions:
            messages.error(request, 'Sorry, this transaction does not belong to you')
            return redirect('wallet_index')
        if not transaction:
            messages.error(request, 'Sorry, transaction does not exist!')
            return redirect('wallet_index')
        data = {'transaction': transaction, 'details':details}
        return render(request, 'vendor_transaction_details.html', data)
    else:
        return redirect('login_page')

def owner_wallet(request):
    print(f'THIS IS POST: {request.POST}')
    if request.user.is_authenticated:
        details = detail.objects.filter(email=request.user.email).first()
        owner = OwnerProfile.objects.filter(user=details).first()
        customer = CustomerProfile.objects.filter(user=details).first()
        if customer:
            return redirect('customer_wallet')
        if owner:
            if owner.is_vendor:
                return redirect('vendor_wallet')
        if request.user.is_superuser:
            return redirect('admin_wallet')
        wallet = owner.wallet.first()
        # Customer wallet code
        if request.POST.get('razorpay_signature'):
            razorpay_payment_id = request.POST.get('razorpay_payment_id')
            razorpay_order_id = request.POST.get('razorpay_order_id')
            razorpay_signature = request.POST.get('razorpay_signature')
            razorData = {'razorpay_payment_id':razorpay_payment_id, 'razorpay_order_id':razorpay_order_id, 'razorpay_signature':razorpay_signature}
            client = razorpay.Client(auth=(razorpay_id, razorpay_secret))
            client.utility.verify_payment_signature(razorData)
            transaction = Transaction.objects.get(razorpay_order_id=razorpay_order_id)
            transaction.razorpay_payment_id = razorpay_payment_id
            transaction.razorpay_signature = razorpay_signature
            transaction.status = "Paid Successfully"
            if transaction.credit:
                wallet.balance += transaction.amount
                if wallet.balance >= wallet.deactivate_amount:
                    wallet.is_active = True
                    owner.is_active = True
                wallet.save()
            transaction.running_balance = wallet.balance
            transaction.save()
            if request.POST.get('security'):
                messages.success(request, 'Security deposit added successfully!')
            else:
                messages.success(request, 'Amount added to wallet successfully!')
            return redirect('owner_wallet')
        if request.POST.get('razorpay_security'):
            amount = wallet.deactivate_amount - wallet.balance
            razorpay_od_id = wallet.vendor_to_company_generate_transaction(amount)
            return render(request, 'owner_make_payment.html', {'razorpay_od_id':razorpay_od_id, 'amount':amount, 'profile':owner, 'type':'security'})
        if request.POST.get('wallet_add'):
            amount = request.POST.get('amount')
            amount = int(amount)
            razorpay_od_id = wallet.vendor_to_company_generate_transaction(amount)
            return render(request, 'owner_make_payment.html', {'razorpay_od_id':razorpay_od_id, 'amount':amount, 'profile':owner, 'type':'wallet_add'})
        transactions = wallet.transactions.all().order_by('-time')
        # Pagination
        page = request.GET.get('page', 1)
        paginator = Paginator(transactions, 15)
        try:
            transactions = paginator.page(page)
        except PageNotAnInteger:
            transactions = paginator.page(1)
        except EmptyPage:
            transactions = paginator.page(paginator.num_pages)
        data = {'transactions': transactions, 'wallet':wallet, 'details':details}
        # if owner has less balance than his deactivate amount
        if wallet.balance < wallet.deactivate_amount:
            data['security_deposit'] = wallet.deactivate_amount - wallet.balance
        return render(request, 'owner_wallet.html', data)
    else:
        return redirect('login_page')

def owner_transaction_details(request, transaction_id):
    if request.user.is_authenticated:
        details = detail.objects.filter(email=request.user.email).first()
        owner = OwnerProfile.objects.filter(user=details).first()
        customer = CustomerProfile.objects.filter(user=details).first()
        if customer:
            return redirect('customer_wallet')
        if owner:
            if owner.is_vendor:
                return redirect('vendor_wallet')
        if request.user.is_superuser:
            return redirect('admin_wallet')
        # Check if transaction belongs to customer
        transaction = Transaction.objects.filter(pk=transaction_id).first()
        wallet = owner.wallet.first()
        owner_transactions = wallet.transactions.all()
        if transaction not in owner_transactions:
            messages.error(request, 'Sorry, this transaction does not belong to you')
            return redirect('wallet_index')
        if not transaction:
            messages.error(request, 'Sorry, transaction does not exist!')
            return redirect('wallet_index')
        data = {'transaction': transaction, 'wallet':wallet, 'details':details}
        return render(request, 'owner_transaction_details.html', data)
    else:
        return redirect('login_page')

def admin_wallet(request):
    if request.user.is_authenticated:
        details = detail.objects.filter(email=request.user.email).first()
        owner = OwnerProfile.objects.filter(user=details).first()
        customer = CustomerProfile.objects.filter(user=details).first()
        if customer:
            return redirect('customer_wallet')
        if owner:
            if owner.is_owner:
                return redirect('owner_wallet')
            if owner.is_vendor:
                return redirect('vendor_wallet')
        if request.POST.get('activate'):
            wallet_id = int(request.POST.get('activate'))
            wallet = Wallet.objects.filter(pk=wallet_id).first()
            if wallet:
                wallet.is_active = True
                wallet.save()
                messages.success(request, "Wallet activated successfully")
                return redirect('admin_wallet')
            else:
                messages.error(request, 'Sorry there was an error!')
                return redirect('admin_wallet')
        if request.POST.get('deactivate'):
            wallet_id = int(request.POST.get('deactivate'))
            wallet = Wallet.objects.filter(pk=wallet_id).first()
            if wallet:
                wallet.is_active = False
                wallet.save()
                messages.success(request, "Wallet deactivated successfully")
                return redirect('admin_wallet')
            else:
                messages.error(request, "Sorry there was an error!")
                return redirect('admin_wallet')
        if request.POST.get('deactivate_amount'):
            wallet_id = int(request.POST.get('deactivate_amount'))
            amount = int(request.POST.get('amount'))
            wallet = Wallet.objects.filter(pk=wallet_id).first()
            if wallet:
                wallet.deactivate_amount = amount
                wallet.save()
                if wallet.balance < amount:
                    wallet.is_active = False
                    wallet.save()
                else:
                    wallet.is_active = True
                    wallet.save()
                messages.success(request, "Wallet deactivate amount set to " + str(amount))
                return redirect('admin_wallet')
            else:
                messages.error(request, "Sorry there was an error!")
                return redirect('admin_wallet')
        # Get all wallets and display them in table format
        wallets = Wallet.objects.all().order_by('-id')
        data = {'wallets':wallets,}
        return render(request, 'admin_wallet.html', data)
    else:
        return redirect('login_page')

def admin_customer_wallet(request):
    if request.user.is_authenticated:
        details = detail.objects.filter(email=request.user.email).first()
        owner = OwnerProfile.objects.filter(user=details).first()
        customer = CustomerProfile.objects.filter(user=details).first()
        if customer:
            return redirect('customer_wallet')
        if owner:
            if owner.is_owner:
                return redirect('owner_wallet')
            if owner.is_vendor:
                return redirect('vendor_wallet')
        if request.POST.get('activate'):
            wallet_id = int(request.POST.get('activate'))
            wallet = Wallet.objects.filter(pk=wallet_id).first()
            if wallet:
                wallet.is_active = True
                wallet.save()
                messages.success(request, "Wallet activated successfully")
                return redirect('admin_customer_wallet')
            else:
                messages.error(request, 'Sorry there was an error!')
                return redirect('admin_customer_wallet')
        if request.POST.get('deactivate'):
            wallet_id = int(request.POST.get('deactivate'))
            wallet = Wallet.objects.filter(pk=wallet_id).first()
            if wallet:
                wallet.is_active = False
                wallet.save()
                messages.success(request, "Wallet deactivated successfully")
                return redirect('admin_customer_wallet')
            else:
                messages.error(request, "Sorry there was an error!")
                return redirect('admin_customer_wallet')
        if request.POST.get('deactivate_amount'):
            wallet_id = int(request.POST.get('deactivate_amount'))
            amount = int(request.POST.get('amount'))
            wallet = Wallet.objects.filter(pk=wallet_id).first()
            if wallet:
                wallet.deactivate_amount = amount
                wallet.save()
                if wallet.balance < amount:
                    wallet.is_active = False
                    wallet.save()
                else:
                    wallet.is_active = True
                    wallet.save()
                messages.success(request, "Wallet deactivate amount set to " + str(amount))
                return redirect('admin_customer_wallet')
            else:
                messages.error(request, "Sorry there was an error!")
                return redirect('admin_customer_wallet')
        # Get all wallets and display them in table format
        customers = CustomerProfile.objects.all()
        wallets = Wallet.objects.filter(customer__in = customers).order_by('-id')
        data = {'wallets':wallets, 'is_customer':True}
        return render(request, 'admin_wallet.html', data)
    else:
        return redirect('login_page')

def admin_owner_wallet(request):
    if request.user.is_authenticated:
        details = detail.objects.filter(email=request.user.email).first()
        owner = OwnerProfile.objects.filter(user=details).first()
        customer = CustomerProfile.objects.filter(user=details).first()
        if customer:
            return redirect('customer_wallet')
        if owner:
            if owner.is_owner:
                return redirect('owner_wallet')
            if owner.is_vendor:
                return redirect('vendor_wallet')
        if request.POST.get('activate'):
            wallet_id = int(request.POST.get('activate'))
            wallet = Wallet.objects.filter(pk=wallet_id).first()
            if wallet:
                wallet.is_active = True
                wallet.save()
                messages.success(request, "Wallet activated successfully")
                return redirect('admin_owner_wallet')
            else:
                messages.error(request, 'Sorry there was an error!')
                return redirect('admin_owner_wallet')
        if request.POST.get('deactivate'):
            wallet_id = int(request.POST.get('deactivate'))
            wallet = Wallet.objects.filter(pk=wallet_id).first()
            if wallet:
                wallet.is_active = False
                wallet.save()
                messages.success(request, "Wallet deactivated successfully")
                return redirect('admin_owner_wallet')
            else:
                messages.error(request, "Sorry there was an error!")
                return redirect('admin_owner_wallet')
        if request.POST.get('deactivate_amount'):
            wallet_id = int(request.POST.get('deactivate_amount'))
            amount = int(request.POST.get('amount'))
            wallet = Wallet.objects.filter(pk=wallet_id).first()
            if wallet:
                wallet.deactivate_amount = amount
                wallet.save()
                if wallet.balance < amount:
                    wallet.is_active = False
                    wallet.save()
                else:
                    wallet.is_active = True
                    wallet.save()
                messages.success(request, "Wallet deactivate amount set to " + str(amount))
                return redirect('admin_owner_wallet')
            else:
                messages.error(request, "Sorry there was an error!")
                return redirect('admin_owner_wallet')
        # Get all wallets and display them in table format
        wallets = Wallet.objects.filter(owner__in = OwnerProfile.objects.all()).order_by('-id')
        data = {'wallets':wallets, 'is_owner':True}
        return render(request, 'admin_wallet.html', data)
    else:
        return redirect('login_page')

def admin_wallet_det(request, wallet_id):
    if request.user.is_authenticated:
        details = detail.objects.filter(email=request.user.email).first()
        owner = OwnerProfile.objects.filter(user=details).first()
        customer = CustomerProfile.objects.filter(user=details).first()
        if customer:
            return redirect('customer_wallet')
        if owner:
            if owner.is_owner:
                return redirect('owner_wallet')
            if owner.is_vendor:
                return redirect('vendor_wallet')
        wallet = Wallet.objects.filter(pk=wallet_id).first()
        if not wallet:
            messages.error(request, 'Sorry you can not access the wallet')
        if request.POST.get('wallet_add'):
            amount = int(request.POST.get('amount'))
            note = str(request.POST.get('note'))
            if wallet.customer:
                wallet.company_to_customer(amount, note)
                messages.success(request, 'Money added to wallet successfully')
                return redirect('admin_wallet_det', wallet_id=wallet.id)
            elif wallet.owner:
                wallet.company_to_vendor(amount, note)
                messages.success(request, 'Money added to wallet successfully')
                return redirect('admin_wallet_det', wallet_id=wallet.id)
        if request.POST.get('activate'):
            wallet_id = int(request.POST.get('activate'))
            wallet = Wallet.objects.filter(pk=wallet_id).first()
            if wallet:
                wallet.is_active = True
                wallet.save()
                messages.success(request, "Wallet activated successfully")
                return redirect('admin_wallet')
            else:
                messages.error(request, 'Sorry there was an error!')
                return redirect('admin_wallet')
        if request.POST.get('deactivate'):
            wallet_id = int(request.POST.get('deactivate'))
            wallet = Wallet.objects.filter(pk=wallet_id).first()
            if wallet:
                wallet.is_active = False
                wallet.save()
                messages.success(request, "Wallet deactivated successfully")
                return redirect('admin_wallet')
            else:
                messages.error(request, "Sorry there was an error!")
                return redirect('admin_wallet')
        if request.POST.get('deactivate_amount'):
            wallet_id = int(request.POST.get('deactivate_amount'))
            amount = int(request.POST.get('amount'))
            wallet = Wallet.objects.filter(pk=wallet_id).first()
            if wallet:
                wallet.deactivate_amount = amount
                wallet.save()
                if wallet.balance < amount:
                    wallet.is_active = False
                    wallet.save()
                else:
                    wallet.is_active = True
                    wallet.save()
                messages.success(request, "Wallet deactivate amount set to " + str(amount))
                return redirect('admin_wallet')
            else:
                messages.error(request, "Sorry there was an error!")
                return redirect('admin_wallet')
        # Get all wallets and display them in table format
        transactions = wallet.transactions.all().order_by('-time')
        page = request.GET.get('page', 1)
        paginator = Paginator(transactions, 15)
        try:
            transactions = paginator.page(page)
        except PageNotAnInteger:
            transactions = paginator.page(1)
        except EmptyPage:
            transactions = paginator.page(paginator.num_pages)
        data = {'transactions': transactions, 'wallet':wallet, 'details':details}
        if wallet.customer:
            return render(request, 'admin_cust_wallet_det.html', data)
        elif wallet.owner:
            if wallet.owner.is_vendor:
                return render(request, 'admin_vend_wallet_det.html', data)
            elif wallet.owner.is_owner:
                return render(request, 'admin_own_wallet_det.html', data)
        else:
            messages.error(request, "Sorry can't find wallet")
            return redirect('dashboard')
    else:
        return redirect('login_page')

def admin_transaction_det(request, transaction_id):
    if request.user.is_authenticated:
        details = detail.objects.filter(email=request.user.email).first()
        owner = OwnerProfile.objects.filter(user=details).first()
        customer = CustomerProfile.objects.filter(user=details).first()
        if customer:
            return redirect('customer_wallet')
        if owner:
            if owner.is_owner:
                return redirect('owner_wallet')
            if owner.is_vendor:
                return redirect('vendor_wallet')
        transaction = Transaction.objects.filter(pk=transaction_id).first()
        if not transaction:
            messages.error(request, 'Sorry you can not access the wallet')
        wallet = transaction.wallet
        data = {'transaction': transaction, 'wallet':wallet, 'details':details}
        if wallet.customer:
            return render(request, 'admin_cust_transaction_det.html', data)
        elif wallet.owner:
            if wallet.owner.is_vendor:
                return render(request, 'admin_vend_transaction_det.html', data)
            elif wallet.owner.is_owner:
                return render(request, 'admin_own_transaction_det.html', data)
        else:
            messages.error(request, "Sorry can't find wallet")
            return redirect('dashboard')
    else:
        return redirect('login_page')