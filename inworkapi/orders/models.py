from django.db import models


class Order(models.Model):
    client = models.ForeignKey(
        'clients.Client',
        on_delete=models.CASCADE,
        null=False,
        blank=False
    )
    name = models.CharField(max_length=40, null=False, blank=False, default='')
    address = models.ForeignKey('utils.Address', on_delete=models.CASCADE, null=True)
    billing_period = models.PositiveIntegerField()
    status = models.CharField(
        max_length=40, null=False, blank=False, default='')
    description = models.TextField()


class Task(models.Model):
    order = models.ForeignKey(
        'Order',
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    name = models.CharField(max_length=40, null=False, blank=False, default='')
    # TODO: use DateField instead of DateTimeFeild
    date = models.DateField()
    manual_time_set = models.BooleanField()
    hours_worked = models.TimeField(null=True, blank=True)
    is_hours_worked_accepted = models.BooleanField(null=True, blank=True, default=False)
    is_cancelled = models.BooleanField(null=True, blank=True, default=False)
    worker = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        null=False,
        blank=False,
        related_name='worker'
    )
    worker_substitution = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='substitution',
        null=True,
        blank=True,
    )
    description = models.TextField(blank=True)
    comment = models.TextField(blank=True)
