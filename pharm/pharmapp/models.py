from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class Store(models.Model):
    name = models.CharField(max_length=50)
    description = models.CharField(max_length=50)
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    stock_qnty = models.IntegerField()
    exp_date =models.CharField(max_length=10)
    
    def __str__(self):
        return (f"{self.name} {self.description} {self.unit_price} {self.stock_qnty} {self.exp_date}")



class cartItem(models.Model):
    item = models.ForeignKey(Store, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)



class ActivityLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    action = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.action} - {self.timestamp}"



class DeductionLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    quantity = models.PositiveIntegerField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.name} - {self.quantity} - {self.timestamp}"
    




class Customers(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15)
    address = models.CharField(max_length=255)
    
    def __str__(self):
        return f"{self.name} ({self.phone} {self.address}"


    
class Sales(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    customer = models.ForeignKey(Customers, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=100)
    quantity = models.IntegerField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField(auto_now_add=True)
    on_credit = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.user} {self.name} {self.quantity} {self.amount}"





class Wallet(models.Model):
    customer = models.OneToOneField(Customers, on_delete=models.CASCADE, related_name='wallet')
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def __str__(self):
        return f"{self.customer.name}'s Wallet - Balance: {self.balance}"
    
    
    def add_funds(self, amount):
        self.balance += amount
        self.save()
        
        
    def clear_balance(self):
        self.balance = 0
        self.save()



    
@receiver(post_save, sender=Customers)
def create_customer_wallet(sender, instance, created, **kwargs):
    if created:
        Wallet.objects.create(customer=instance)





class Loan(models.Model):
    customer = models.ForeignKey(Customers, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    start_date = models.DateField()
    due_date = models.DateField()
    is_paid = models.BooleanField(default=False)
    
    def __str__(self):
        return f"Loan {self.id} for {self.customer.name} {self.amount}"

    