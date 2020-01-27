from django.db import models

import users.models 
import clients.models

class Address(models.Model):
    owner                   = models.ForeignKey(
                                'utils.AddressOwner',
                                on_delete=models.CASCADE, 
                                null=True,
                                blank=True,
                                )
    street                  = models.CharField(max_length=40)
    house_no                = models.CharField(max_length=10)
    flat_no                 = models.CharField(max_length=40, blank=True, null=True)
    city                    = models.CharField(max_length=40)
    district                = models.CharField(max_length=40)
    country                 = models.CharField(max_length=40)
    postal_code             = models.CharField(max_length=12, default='00-001')
    
    def get_owner_instance(self):
        if self.owner:
            return self.owner.get_owner_instance()
        else:
            return None

    def __str__(self):
        flat_no = ("/" + str(self.flat_no)) if self.flat_no else ''
        return (str(self.house_no) + flat_no + " "
            + self.street + ", " 
            + self.city + ", " 
            + self.district + ", " 
            + self.country)
    
    class Meta:
        verbose_name_plural = "Addresses"


# TODO:
# EITHER rename AddressOwner to MultipleAddressOwner,
# and make changes in models accordingly,
# OR make everyone who can have and address an address owner
class AddressOwner(models.Model):

    def get_owner_instance(self):
        # Search a list of all classes that are address owners
        try:
            return users.models.User.objects.get(address_owner=self.id)
        except users.models.User.DoesNotExist:
            try:
                return clients.models.Client.objects.get(address_owner=self.id)
            except clients.models.Client.DoesNotExist:
                return "Neither User nor Client correspond to owner id " + str(self.id)


    def __str__(self):
        return 'AO_' + str(self.id) + ' ' + str(self.get_owner_instance())

    
class CustomFile(models.Model):
    owner               = models.ForeignKey(
                            'utils.FileOwner',
                            on_delete=models.CASCADE, 
                            null=True,
                            blank=True,
                            )
    name                = models.CharField(max_length=191)
    location            = models.URLField(max_length=300)
    date_created        = models.DateTimeField(auto_now_add=True)


class FileOwner(models.Model):
    
    def get_owner_instance(self):
        return 'get_owner_instance is not yet implemented'
        # try:
        #     return users.models.User.objects.get(file_owner=self.id)
        # except users.models.User.DoesNotExist:
        #     try:
        #         return clients.models.Client.objects.get(file_owner=self.id)
        #     except clients.models.Client.DoesNotExist:
        #         return "Neither User nor Client correspond to owner id " + str(self.id)

    def __str__(self):
        return 'FO_' + str(self.id) + ' ' + str(self.get_owner_instance())