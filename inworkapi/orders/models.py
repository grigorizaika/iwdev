from django.db import models

# Create your models here.


class Order(models.Model):
    client = models.ForeignKey(
        'clients.Client',
        on_delete=models.CASCADE,
        null=False,
        blank=False
    )
    name = models.CharField(max_length=40, null=False, blank=False, default='')
    address = models.ForeignKey('utils.Address', on_delete=models.CASCADE, null=True)
    billingPeriod = models.PositiveIntegerField()
    status = models.CharField(
        max_length=40, null=False, blank=False, default='')
    description = models.TextField()


class Task(models.Model):
    order = models.ForeignKey(
        'Order',
        on_delete=models.CASCADE,
        null=False,
        blank=False
    )
    name = models.CharField(max_length=40, null=False, blank=False, default='')
    date = models.DateTimeField()
    manualTimeSet = models.BooleanField()
    hoursWorked = models.TimeField(null=True, blank=True)
    isHoursWorkedAccepted = models.BooleanField(null=True, blank=True, default=False)
    isCancelled = models.BooleanField(null=True, blank=True, default=False)
    worker = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        null=False,
        blank=False,
        related_name='worker'
    )
    workerSubstitution = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='substitution',
        null=True,
        blank=True,
    )
    description = models.TextField(blank=True)
    comment = models.TextField(blank=True)
