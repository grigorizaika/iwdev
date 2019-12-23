from django.db import models

# Create your models here.
class Order(models.Model):
    client              = models.ForeignKey(
                            'clients.Client', 
                            on_delete=models.CASCADE, 
                            null=False, 
                            blank=False
                            )
    name                = models.CharField(max_length=40, null=False, blank=False, default='')
    address             = models.ForeignKey('utils.Address', on_delete=models.CASCADE)
    billingPeriod       = models.PositiveIntegerField()
    status              = models.CharField(max_length=40, null=False, blank=False, default='')
    description         = models.TextField()


class Task(models.Model):
    order                   = models.ForeignKey(
                                'Order', 
                                on_delete=models.CASCADE, 
                                null=False, 
                                blank=False
                                )
    name                    = models.CharField(max_length=40, null=False, blank=False, default='')
    date                    = models.DateTimeField()
    manualTimeSet           = models.BooleanField()
    hoursWorked             = models.TimeField()
    isHoursWorkedAccepted   = models.BooleanField()
    isCancelled             = models.BooleanField()
    worker                  = models.ForeignKey(
                                'users.User', 
                                on_delete=models.CASCADE, 
                                null=False, 
                                blank=False,
                                related_name='worker'
                                )
    workerSubstitution      = models.ForeignKey(
                                'users.User', 
                                on_delete=models.CASCADE, 
                                related_name='substitution'
                                )
    description             = models.TextField()
    comment                 = models.TextField()