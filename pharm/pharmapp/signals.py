from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Customer, Wallet

@receiver(post_save, sender=Customer)
def create_wallet(sender, instance, created, **kwargs):
    if created:
        Wallet.objects.create(customer=instance)

@receiver(post_save, sender=Customer)
def save_wallet(sender, instance, **kwargs):
    instance.wallet.save()
