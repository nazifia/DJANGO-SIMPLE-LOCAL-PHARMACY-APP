from django import forms
from .models import Store, Loan, Customers, Wallet
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

class searchForm(forms.Form):
    search_query = forms.CharField(min_length=2, label="", required=True, widget=forms.TextInput(attrs={'placeholder': 'SEARCH ITEM HERE', 'class': 'form-control'}))
    
    
    
class addToStore(forms.ModelForm):
    name = forms.CharField(max_length=100, label="", required=True, widget=forms.TextInput(attrs={'placeholder': 'ITEM NAME', 'class': 'form-control'}))
    description =  forms.CharField(max_length=100, label="", required=True, widget=forms.TextInput(attrs={'placeholder': 'DESCRIPTION', 'class': 'form-control'}))   
    unit_price = forms.DecimalField(decimal_places=2)
    stock_qnty = forms.IntegerField()
    exp_date = forms.CharField(max_length=100, label="", required=True, widget=forms.TextInput(attrs={'placeholder': 'EXP DATE', 'class': 'form-control'}))
    
    class Meta:
        model = Store
        exclude = ('user',)
    


class salesForm(forms.Form):
    search_date = forms.DateField(label='Search Date', widget=forms.TextInput(attrs={'type': 'date'}))
    
    

class CustomerRegistrationForm(forms.ModelForm):
    class Meta:
        model = Customers
        fields = ['name', 'phone', 'address']
    
    
    
class LoanForm(forms.ModelForm):
    class Meta:
        model = Loan
        fields = ['customer', 'amount', 'start_date', 'due_date']


class DiscountForm(forms.Form):
    discount_amount = forms.DecimalField(max_digits=10, decimal_places=2, label='Discount Amount')
    
    

class RegistrationForm(UserCreationForm):

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

    def save(self, commit=True):
        user = super(RegistrationForm, self).save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user


class AddFundsForm(forms.Form):
    amount = forms.DecimalField(max_digits=10, decimal_places=2)
    
    
class PurchaseItemsForm(forms.Form):
    customer = forms.ModelChoiceField(queryset=Customers.objects.all(), label="Select Customer")
    items = forms.ModelMultipleChoiceField(queryset=Store.objects.all(), widget=forms.CheckboxSelectMultiple, label="Select Items")

    def __init__(self, *args, **kwargs):
        super(PurchaseItemsForm, self).__init__(*args, **kwargs)
        self.quantity_fields = {}
        for item in Store.objects.all():
            field_name = f'quantity_{item.id}'
            self.fields[field_name] = forms.IntegerField(
                min_value=1,
                initial=1,
                label=f'Quantity for {item.name}',
                required=False
            )
            self.quantity_fields[item.id] = self.fields[field_name]