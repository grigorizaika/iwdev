from django.db import models

import users.models

# Create your models here.
class Address(models.Model):
    owner                   = models.ForeignKey(
                                'utils.AddressOwner',
                                on_delete=models.CASCADE, 
                                #null=True,
                                #blank=True,
                                )
    street                  = models.CharField(max_length=40)
    house_no                = models.PositiveIntegerField()
    flat_no                 = models.PositiveIntegerField(blank=True, null=True)
    city                    = models.CharField(max_length=40)
    district                = models.CharField(max_length=40)
    country                 = models.CharField(max_length=40)
    postal_code             = models.CharField(max_length=12, default='00-001')
    
    def get_owner_instance(self):
        return self.owner.get_owner_instance()

    def __str__(self):
        flat_no = ("/" + str(self.flat_no)) if self.flat_no else ''
        return (str(self.house_no) + flat_no + " "
            + self.street + ", " 
            + self.city + ", " 
            + self.district + ", " 
            + self.country)
    
    class Meta:
        verbose_name_plural = "Addresses"


class AddressOwner(models.Model):

    def get_owner_instance(self):
        # Search a list of all classes that are address owners
        try:
            return users.models.User.objects.get(address_owner=self.id)
        except users.models.User.DoesNotExist:
            return "User not found"

    def __str__(self):
        return 'AO_' + str(self.id) + ' ' + str(self.get_owner_instance())