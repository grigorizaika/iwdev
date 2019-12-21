from django.db import models

# Create your models here.
class Address(models.Model):
    street                  = models.CharField(max_length=40)
    houseNo                 = models.PositiveIntegerField()
    flatNo                  = models.PositiveIntegerField(blank=True, null=True)
    city                    = models.CharField(max_length=40)
    district                = models.CharField(max_length=40)
    country                 = models.CharField(max_length=40)
    
    def __str__(self):
        flatNo = ("/" + str(self.flatNo)) if self.flatNo else ''
        return (str(self.houseNo) + flatNo + " "
            + self.street + ", " 
            + self.city + ", " 
            + self.district + ", " 
            + self.country)

    class Meta:
        verbose_name_plural = "Addresses"