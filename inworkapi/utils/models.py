from django.db import models

# Create your models here.
class Address(models.Model):
    street                  = models.CharField(max_length=40)
    houseNo                 = models.PositiveIntegerField()
    flatNo                  = models.PositiveIntegerField()
    city                    = models.CharField(max_length=40)
    district                = models.CharField(max_length=40)
    country                 = models.CharField(max_length=40)
    
    def __str__(self):
        return (str(self.houseNo) + "/"
            + str(self.flatNo) + " "
            + self.street + ", " 
            + self.city + " " 
            + self.district + " " 
            + self.country)