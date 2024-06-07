from django.contrib import admin
from .models import Store, Customers, Wallet

# Register your models here.
admin.site.register(Store)

class WalletInline(admin.TabularInline):
    model = Wallet
    extra = 1

class CustomerAdmin(admin.ModelAdmin):
    inlines = (WalletInline,)

admin.site.register(Customers, CustomerAdmin)
admin.site.register(Wallet)