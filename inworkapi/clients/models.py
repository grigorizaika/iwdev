from django.db import models
from django.utils.translation import gettext as _
from phonenumber_field.modelfields import PhoneNumberField
from django.db.models.signals import (post_delete, post_save)
import utils.models

class Client(models.Model):
    name                = models.CharField(max_length=40, unique=True)
    email               = models.EmailField(_('email address'))
    contact_name        = models.CharField(max_length=40)
    contact_phone       = PhoneNumberField()
    address_owner       = models.OneToOneField(
                            'utils.AddressOwner', 
                            on_delete=models.CASCADE, 
                            null=True, 
                            blank=True
                        )
    file_owner          = models.OneToOneField(
                            'utils.FileOwner',
                            on_delete=models.CASCADE,
                            null=True,
                            blank=True,
                            )
    logo_url            = models.CharField(max_length=300, blank=True, null=True)

    def addresses(self):
        return utils.models.Address.objects.filter(owner=self.address_owner)
    
    def files(self):
        return utils.models.CustomFile.objects.filter(owner=self.file_owner)

    @staticmethod
    def create_address_owner(instance):
        instance.address_owner = utils.models.AddressOwner.objects.create()

    @staticmethod
    def create_file_owner(instance):
        fo = utils.models.FileOwner.objects.create()
        fo.save()
        instance.file_owner = fo
        instance.save()

    @staticmethod
    def delete_address_owner(instance):
        if instance.address_owner:
            instance.address_owner.delete()

    @staticmethod
    def delete_file_owner(instance):
        if instance.file_owner:
            instance.file_owner.delete()


    @staticmethod
    def create_setup(sender, instance, created, *args, **kwagrs):
        if not created:
            return
        Client.create_address_owner(instance)
        Client.create_file_owner(instance)


    @staticmethod
    def delete_cleanup(sender, instance, *args, **kwargs):
        Client.delete_address_owner(instance)
        Client.delete_file_owner(instance)


    def __str__(self):
        return self.name

post_delete.connect(Client.delete_cleanup, sender=Client)
post_save.connect(Client.create_setup, sender=Client)
