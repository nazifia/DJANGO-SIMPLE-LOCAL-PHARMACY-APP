from django.utils import timezone
from datetime import timedelta
from django.urls import reverse
from django.db.models.functions import TruncDay, TruncMonth
from django.db.models import Sum, F, ExpressionWrapper, fields
from django.db import transaction
from django.contrib.auth.decorators import user_passes_test, login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from .models import Store, cartItem, ActivityLog, DeductionLog, Sales, Loan, Customers, Wallet
from .forms import searchForm, addToStore, salesForm, LoanForm, CustomerRegistrationForm, DiscountForm, RegistrationForm, AddFundsForm




# Create your views here.
def index(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            messages.success(request, 'Invalid credentials.')
            return redirect('index')            
    else:
        return render(request, 'pharmapp/index.html', {})

def logout_user(request):
    logout(request)
    return redirect('index')

def is_admin(user):
    return user.is_authenticated and user.is_superuser

def home(request):
    return render(request, 'pharmapp/home.html', {})

def store(request):
    if request.user.is_authenticated:
        items = Store.objects.all()
        total_purchase_value = calculate_purchase_value()
        total_stock_value = calculate_stock_value()
        return render(request, 'pharmapp/store.html', {
            'items': items,
            'total_purchase_value': total_purchase_value,
            'total_stock_value': total_stock_value
        })
    else:
        return render(request, 'pharmapp/index.html', {})

@user_passes_test(is_admin)
@transaction.atomic
def edit_item(request, pk):
    if request.user.is_authenticated:
        edit_item = Store.objects.get(id=pk)
        form = addToStore(request.POST or None, instance=edit_item)
        if form.is_valid():
            form.save()
            return redirect('store')
        return render(request, 'pharmapp/edit_item.html', {'form': form})
    else:
        return render(request, 'pharmapp/index.html', {})

@transaction.atomic
def add_to_store(request):
    form = addToStore(request.POST or None)
    if request.user.is_authenticated:
        if request.method == 'POST':
            if form.is_valid():
                add_to_store = form.save()
                return redirect('store')
        return render(request, 'pharmapp/add_to_store.html', {'form': form})
    else:
        return render(request, 'pharmapp/index.html', {})

def search(request):
    if request.user.is_authenticated:
        if request.method == 'POST':
            form = searchForm(request.POST)
            if form.is_valid():
                search_query = form.cleaned_data['search_query']
                results = Store.objects.filter(name__icontains=search_query)
            else:
                results = None
        else:
            form = searchForm()
            results = None
    return render(request, 'pharmapp/search.html', {'form': form, 'results': results})



@login_required
@transaction.atomic
def add_funds(request, pk):
    customer = get_object_or_404(Customers, pk=pk)
    wallet = Wallet.objects.get(customer=customer)
    
    if request.method == 'POST':
        form = AddFundsForm(request.POST, instance=wallet)
        if form.is_valid():
            wallet.balance += form.cleaned_data['balance']
            wallet.save()
            messages.success(request, 'Funds added successfully.')
            return redirect('customer_list')
    else:
        form = AddFundsForm()
    
    return render(request, 'pharmapp/add_funds.html', {'form': form, 'customer': customer})



@transaction.atomic
def add_to_cart(request, pk):
    item = Store.objects.get(id=pk)
    if request.method == 'POST':
        quantity = int(request.POST['quantity'])
        customer = Customers.objects.get(user=request.user)
        wallet, created = Wallet.objects.get_or_create(customer=customer)
        total_price = item.unit_price * quantity
        
        if wallet.balance >= total_price:
            wallet.balance -= total_price
            wallet.save()

            item.stock_qnty -= quantity
            item.save()

            DeductionLog.objects.create(user=request.user, name=item.name, quantity=quantity)

            cartItem.objects.create(item=item, quantity=quantity)
            return redirect('view_cart')
        elif item.stock_qnty >= quantity:
            item.stock_qnty -= quantity
            item.save()

            DeductionLog.objects.create(user=request.user, name=item.name, quantity=quantity)

            cartItem.objects.create(item=item, quantity=quantity)
            return redirect('view_cart')
        else:
            messages.error(request, f"Sorry, the requested quantity ({quantity}) exceeds the available stock quantity ({item.stock_qnty}).")
    return render(request, 'pharmapp/add_to_cart.html', {'item': item})

def view_cart(request):
    cart_items = cartItem.objects.all()
    
    total_price = 0
    total_discounted_price = 0
    for cart_item in cart_items:
        cart_item.subtotal = cart_item.item.unit_price * cart_item.quantity
        cart_item.discounted_subtotal = cart_item.subtotal - cart_item.discount_amount
        total_price += cart_item.subtotal
        total_discounted_price += cart_item.discounted_subtotal
    
    return render(request, 'pharmapp/view_cart.html', {
        'cart_items': cart_items,
        'total_price': total_price,
        'total_discounted_price': total_discounted_price,
    })
    
    

@transaction.atomic
def remove_from_cart(request, pk):
    cart_item = get_object_or_404(cartItem, id=pk)
    item = cart_item.item
    
    if request.method == 'POST':
        quantity_to_return = int(request.POST['quantity'])
        if quantity_to_return > 0 and quantity_to_return <= cart_item.quantity:
            # Update stock quantity
            item.stock_qnty += quantity_to_return
            item.save()
            
            # Update cart item quantity
            cart_item.quantity -= quantity_to_return
            cart_item.save()
            
            # If cart item quantity becomes 0, delete it
            if cart_item.quantity == 0:
                cart_item.delete()
                
            return redirect('view_cart')
    
    return render(request, 'pharmapp/remove_from_cart.html', {'cart_item': cart_item})


@transaction.atomic
def generate_receipt(request):
    cart_items = cartItem.objects.select_related('item').all()
    total_price = 0
    total_discounted_price = 0

    for cart_item in cart_items:
        cart_item.subtotal = cart_item.item.unit_price * cart_item.quantity
        cart_item.discounted_subtotal = cart_item.subtotal - cart_item.discount_amount
        total_price += cart_item.subtotal
        total_discounted_price += cart_item.discounted_subtotal

        # Determine if the sale is on credit based on wallet balance
        customer = Customers.objects.get(user=request.user)
        wallet = Wallet.objects.get(customer=customer)
        on_credit = wallet.balance < total_discounted_price

        # Deduct from wallet balance if sufficient
        if not on_credit:
            wallet.balance -= total_discounted_price
            wallet.save()

        Sales.objects.create(
            user=request.user,
            name=cart_item.item.name,
            quantity=cart_item.quantity,
            amount=cart_item.discounted_subtotal,
            on_credit=on_credit
        )
    
    cartItem.objects.all().delete()
    return render(request, 'pharmapp/receipt.html', {'cart_items': cart_items, 'total_price': total_price, 'total_discounted_price': total_discounted_price})

@user_passes_test(is_admin)
def activity_logs(request):
    logs = ActivityLog.objects.all()
    return render(request, 'pharmapp/logs.html', {'logs': logs})

@user_passes_test(is_admin)
def deduction_logs(request):
    Dlogs = DeductionLog.objects.all()
    return render(request, 'pharmapp/Dlogs.html', {'Dlogs': Dlogs})

def activities(request):
    if request.user.is_authenticated:
        return render(request, 'pharmapp/activities.html', {})

def calculate_purchase_value():
    total_purchase_value = Store.objects.annotate(
        total_value=ExpressionWrapper(F('purchase_price') * F('stock_qnty'), output_field=fields.DecimalField())
    ).aggregate(Sum('total_value'))['total_value__sum']
    return total_purchase_value or 0

def calculate_stock_value():
    total_stock_value = Store.objects.annotate(
        total_value=ExpressionWrapper(F('unit_price') * F('stock_qnty'), output_field=fields.DecimalField())
    ).aggregate(Sum('total_value'))['total_value__sum']
    return total_stock_value or 0

def get_daily_sales():
    daily_sales = Sales.objects.annotate(
        day=TruncDay('date')
    ).values('day').annotate(
        total_sales=Sum('amount')
    ).order_by('day')
    return daily_sales

def get_monthly_sales():
    monthly_sales = Sales.objects.annotate(
        month=TruncMonth('date')
    ).values('month').annotate(
        total_sales=Sum('amount')
    ).order_by('month')
    return monthly_sales

def daily_sales(request):
    daily_sales = get_daily_sales()
    return render(request, 'pharmapp/daily_sales.html', {'daily_sales': daily_sales})

def monthly_sales(request):
    monthly_sales = get_monthly_sales()
    return render(request, 'pharmapp/monthly_sales.html', {'monthly_sales': monthly_sales})



def sales(request):
    if request.method == 'POST':
        form = salesForm(request.POST)
        if form.is_valid():
            search_date = form.cleaned_data['search_date']
            daily_sales = Sales.objects.filter(date=search_date).aggregate(total_sales=Sum('amount'))
            monthly_sales = Sales.objects.filter(date__month=search_date.month, date__year=search_date.year).aggregate(total_sales=Sum('amount'))
            return render(request, 'pharmapp/search_sales.html', {
                'search_date': search_date,
                'daily_sales': daily_sales['total_sales'],
                'monthly_sales': monthly_sales['total_sales'],
            })
    else:
        form = salesForm()
    return render(request, 'pharmapp/search_sales.html', {'form': form})




@login_required
def loan_list(request):
    loans = Loan.objects.all()
    return render(request, 'pharmapp/loan_list.html', {'loans': loans})

# @user_passes_test(is_admin)
@login_required
def add_loan(request):
    if request.method == 'POST':
        form = LoanForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Loan added successfully.')
            return redirect('loan_list')
    else:
        form = LoanForm()
    return render(request, 'pharmapp/add_loan.html', {'form': form})

@user_passes_test(is_admin)
@login_required
def edit_loan(request, pk):
    loan = get_object_or_404(Loan, pk=pk)
    if request.method == 'POST':
        form = LoanForm(request.POST, instance=loan)
        if form.is_valid():
            form.save()
            messages.success(request, 'Loan updated successfully.')
            return redirect('loan_list')
    else:
        form = LoanForm(instance=loan)
    return render(request, 'pharmapp/edit_loan.html', {'form': form})

@user_passes_test(is_admin)
@login_required
def delete_loan(request, pk):
    loan = get_object_or_404(Loan, pk=pk)
    if request.method == 'POST':
        loan.delete()
        messages.success(request, 'Loan deleted successfully.')
        return redirect('loan_list')
    return render(request, 'pharmapp/delete_loan.html', {'loan': loan})




def register_customer(request):
    if request.method == 'POST':
        form = CustomerRegistrationForm(request.POST)
        if form.is_valid():
            customer = form.save(commit=False)  # Don't save to database yet
            # customer.user = request.user  # Associate the logged-in user
            customer.save()  # Save to database now
            return redirect('customer_list')  # Redirect to a success page
    else:
        form = CustomerRegistrationForm()
    return render(request, 'pharmapp/register_customer.html', {'form': form})



def customer_list(request):
    if request.user.is_authenticated:
        customers = Customers.objects.all()
        return render(request, 'pharmapp/customer_list.html', {'customers': customers})
    else:
        return redirect('home')



@login_required
@user_passes_test(is_admin)
def delete_customer(request, pk):
    customer = get_object_or_404(Customers, pk=pk)
    if request.method == 'POST':
        customer.delete()
        messages.success(request, 'Customer deleted successfully.')
        return redirect('customer_list')
    return render(request, 'pharmapp/delete_customer.html', {'customer': customer})



@transaction.atomic
def apply_discount(request, pk):
    cart_item = get_object_or_404(cartItem, id=pk)
    
    if request.method == 'POST':
        form = DiscountForm(request.POST)
        if form.is_valid():
            discount_amount = form.cleaned_data['discount_amount']
            cart_item.discount_amount = discount_amount
            cart_item.save()
            return redirect('view_cart')
    else:
        form = DiscountForm(initial={'discount_amount': cart_item.discount_amount})
    
    return render(request, 'pharmapp/apply_discount.html', {'form': form, 'cart_item': cart_item})


@user_passes_test(is_admin)
def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password1')
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('home')
            else:
                messages.error(request, 'Registration successful, but login failed. Please try logging in manually.')
                return redirect('login')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = RegistrationForm()
    return render(request, 'pharmapp/register.html', {'form': form})



@login_required
@transaction.atomic
def add_funds(request, customer_id):
    customer = get_object_or_404(Customers, id=customer_id)
    wallet = customer.wallet

    if request.method == 'POST':
        form = AddFundsForm(request.POST)
        if form.is_valid():
            amount = form.cleaned_data['amount']
            wallet.add_funds(amount)
            messages.success(request, 'Funds added successfully.')
            return redirect('wallet_detail', customer_id=customer_id)
    else:
        form = AddFundsForm()

    return render(request, 'pharmapp/add_funds.html', {'form': form, 'customer': customer})

def exp_date_alert(request):
    if request.user.is_authenticated:
        # Define the alert threshold (e.g., 90 days before expiration)
        alert_threshold = timezone.now() + timedelta(days=90)
        
        # Get items that are expiring within the next 90 days
        expiring_items = Store.objects.filter(exp_date__lte=alert_threshold, exp_date__gt=timezone.now())
        
        # Get items that have already expired
        expired_items = Store.objects.filter(exp_date__lt=timezone.now())
        
        return render(request, 'pharmapp/exp_date_alert.html', {
            'expiring_items': expiring_items,
            'expired_items': expired_items,
        })
    else:
        return redirect('home')
    
    
    
    
@login_required
def wallet_detail(request, customer_id):
    customer = get_object_or_404(Customers, id=customer_id)
    wallet = customer.wallet
    return render(request, 'pharmapp/wallet_detail.html', {'wallet': wallet, 'customer': customer})



@login_required
@transaction.atomic
def purchase_items(request):
    if request.method == 'POST':
        customer_id = request.POST.get('customer_id')
        customer = get_object_or_404(Customers, id=customer_id)
        wallet = customer.wallet
        
        item_ids = request.POST.getlist('item_ids')
        total_price = 0
        items_with_quantities = []
        insufficient_stock = False
        
        for item_id in item_ids:
            item = get_object_or_404(Store, id=item_id)
            quantity = int(request.POST.get(f'quantity_{item_id}', 1))
            
            if item.stock_qnty < quantity:
                messages.error(request, f'Insufficient stock for {item.name}. Available: {item.stock_qnty}')
                insufficient_stock = True
            else:
                total_price += item.unit_price * quantity
                items_with_quantities.append((item, quantity))

        if insufficient_stock:
            return redirect('purchase_items')
        
        if wallet.balance >= total_price:
            # Render a confirmation page
            return render(request, 'pharmapp/purchase_approval.html', {'customer': customer, 'total_price': total_price, 'items_with_quantities': items_with_quantities})
        else:
            messages.error(request, 'Insufficient funds in wallet.')
            return redirect('wallet_detail', customer_id=customer_id)
    else:
        items = Store.objects.all()
        customers = Customers.objects.all()
        return render(request, 'pharmapp/purchase_items.html', {'items': items, 'customers': customers})
    
    
    
    
@login_required
@transaction.atomic
def purchase_items(request):
    if request.method == 'POST':
        customer_id = request.POST.get('customer_id')
        customer = get_object_or_404(Customers, id=customer_id)
        wallet = customer.wallet
        
        item_ids = request.POST.getlist('item_ids')
        total_price = 0
        items_with_quantities = []
        insufficient_stock = False
        
        for item_id in item_ids:
            item = get_object_or_404(Store, id=item_id)
            quantity = int(request.POST.get(f'quantity_{item_id}', 1))
            
            if item.stock_qnty < quantity:
                messages.error(request, f'Insufficient stock for {item.name}. Available: {item.stock_qnty}')
                insufficient_stock = True
            else:
                total_price += item.unit_price * quantity
                items_with_quantities.append((item, quantity))

        if insufficient_stock:
            return redirect('purchase_items')
        
        if wallet.balance >= total_price:
            # Deduct the total price from the wallet balance
            wallet.balance -= total_price
            wallet.save()

            # Deduct the quantity from store and create sales records
            for item, quantity in items_with_quantities:
                item.stock_qnty -= quantity
                item.save()

                # Log the sale
                Sales.objects.create(
                    user=request.user,
                    name=item.name,
                    quantity=quantity,
                    amount=item.unit_price * quantity,
                    on_credit=False
                )

                # Record into DeductionLog
                DeductionLog.objects.create(
                    user=request.user,
                    name=item.name,
                    quantity=quantity
                )

            messages.success(request, 'Items purchased successfully and wallet balance updated.')
            return redirect('wallet_detail', customer_id=customer_id)
        else:
            messages.error(request, 'Insufficient funds in wallet.')
            return redirect('wallet_detail', customer_id=customer_id)
    else:
        items = Store.objects.all()
        customers = Customers.objects.all()
        return render(request, 'pharmapp/purchase_items.html', {'items': items, 'customers': customers})





@login_required
def clear_balance(request, customer_id):
    wallet = get_object_or_404(Wallet, customer_id=customer_id)
    wallet.balance = 0
    wallet.save()
    messages.success(request, 'Wallet balance has been cleared.')
    return redirect('wallet_detail', customer_id=customer_id)

