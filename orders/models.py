from django.db import models

from django.db.models.signals import (post_delete, post_save)

from utils.models import CustomFile, FileOwner

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
        max_length=40, null=False, blank=False, default='-')
    description = models.TextField()

    file_owner = models.OneToOneField(
                            'utils.FileOwner',
                            on_delete=models.CASCADE,
                            null=True,
                            blank=True,
                            )

    def __str__(self):
        return 'Order ' + str(self.id) + '. ' + str(self.name)

    def files(self):
        files = utils.models.CustomFile.objects.filter(owner=self.file_owner)
        return files

    @staticmethod
    def create_file_owner(instance):
        fo = FileOwner.objects.create()
        fo.save()
        instance.file_owner = fo
        instance.save()

    @staticmethod
    def delete_file_owner(instance):
        if instance.file_owner:
            instance.file_owner.delete()

    @staticmethod
    def create_setup(sender, instance, created, *args, **kwagrs):
        if not created:
            return
        Order.create_file_owner(instance)


    @staticmethod
    def delete_cleanup(sender, instance, *args, **kwargs):
        Order.delete_file_owner(instance)



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

    file_owner          = models.OneToOneField(
                            'utils.FileOwner',
                            on_delete=models.CASCADE,
                            null=True,
                            blank=True,
                            )

    def __str__(self):
        return 'Task ' + str(self.id) + '. ' + str(self.name)

    def files(self):
        files = utils.models.CustomFile.objects.filter(owner=self.file_owner)
        return files


    @staticmethod
    def create_file_owner(instance):
        fo = FileOwner.objects.create()
        fo.save()
        instance.file_owner = fo
        instance.save()

    @staticmethod
    def delete_file_owner(instance):
        if instance.file_owner:
            instance.file_owner.delete()

    @staticmethod
    def create_setup(sender, instance, created, *args, **kwagrs):
        if not created:
            return
        Task.create_file_owner(instance)


    @staticmethod
    def delete_cleanup(sender, instance, *args, **kwargs):
        Task.delete_file_owner(instance)



post_delete.connect(Task.delete_cleanup, sender=Task)
post_save.connect(Task.create_setup, sender=Task)
post_delete.connect(Order.delete_cleanup, sender=Order)
post_save.connect(Order.create_setup, sender=Order)

