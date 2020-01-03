from django.db import models
from django.utils.translation import gettext as _
from phonenumber_field.modelfields import PhoneNumberField


class Client(models.Model):
    name = models.CharField(max_length=40, unique=True)
    email = models.EmailField(_('email address'))
    contactName = models.CharField(max_length=40)
    contactPhone = PhoneNumberField()
    address = models.ForeignKey(
        'utils.Address', on_delete=models.CASCADE, null=True)
    # TODO: logoUrl, after the Firebase storage integration

    def __str__(self):
        return self.name
