import boto3
import datetime
import sys

from botocore.exceptions            import ParamValidationError
from django.conf                    import settings
from django.contrib.auth.models     import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models     import PermissionsMixin
from django.db                      import models
from django.db.models.signals       import post_delete, post_save
from django.utils.translation       import gettext as _
from phonenumber_field.modelfields  import PhoneNumberField

from inworkapi.utils import CognitoHelper
from utils.models import AddressOwner, Address, CustomFile, FileOwner
from warrant import Cognito


class UserManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, email, name, surname, phone, password=None, create_cognito_user=True):

        if not email:
            raise ValueError("An email address has not been provided")

        djangoUser = self.model(
            email=self.normalize_email(email),
            name=name,
            surname=surname,
            phone=phone,
        )

        djangoUser.set_password(password)
        djangoUser.save()

        if create_cognito_user:
            User.create_cognito_user(djangoUser, password)

        return djangoUser


    def create_superuser(self, email, name, surname, phone, password):
        djangoUser = self.create_user(
            email=self.normalize_email(email),
            password=password,
            name=name,
            surname=surname,
            phone=phone,
        )
        djangoUser.is_superuser = True
        djangoUser.is_staff = True
        djangoUser.admin = True
        try:
            adminRole, created =  Role.objects.get_or_create(name='Administrator')
            djangoUser.role = adminRole
        except ValueError as e:
            print(e)

        djangoUser.save()
        return djangoUser


    def get_or_create_for_cognito(self, payload):
        cognito_id = payload['sub']
#        try:
        return self.get(cognito_id=cognito_id)
#        except self.model.DoesNotExist:
 


class User(AbstractBaseUser, PermissionsMixin):
    username                = None
    email                   = models.EmailField(_('email address'), unique=True)
    name                    = models.CharField(max_length=40)
    surname                 = models.CharField(max_length=40)
    phone                   = PhoneNumberField(null=False, blank=False, unique=True)
    address_owner           = models.OneToOneField(
                                'utils.AddressOwner',
                                on_delete=models.CASCADE,
                                null=True,
                                blank=True,
                                )
    file_owner              = models.OneToOneField(
                                'utils.FileOwner',
                                on_delete=models.CASCADE,
                                null=True,
                                blank=True,
                                )
    role                    = models.ForeignKey(
                                'Role', 
                                on_delete=models.CASCADE, 
                                null=True,
                                blank=True,
                                )
    supervisor              = models.ForeignKey(
                                'self', 
                                on_delete=models.CASCADE, 
                                null=True,
                                blank=True, 
                                limit_choices_to={'role__name': 'Administrator'})
    company                 = models.ForeignKey(
                                'Company',
                                on_delete=models.CASCADE,
                                null=True,
                                blank=True,
                                )    
    created_at               = models.DateTimeField(auto_now_add=True)
    cognito_id               = models.CharField(max_length=191)
    profile_picture_url      = models.CharField(max_length=300, blank=True, null=True)
    # A required Django field. Does not represent the business logic.
    is_staff                = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name', 'surname', 'phone']

    def is_administrator(self):
        return self.role.name == 'Administrator'

    def addresses(self):
        addresses = Address.objects.filter(owner=self.address_owner)
        return addresses

    def files(self):
        files = CustomFile.objects.filter(owner=self.file_owner)
        return files

    def add_address(self, **args):
        # In order to assign an address to the user,
        # the address must be added to the user's
        # corresponding AddressOwner instance
        owner_record = self.address_owner()
        address = Address.objects.create(
            args,
            owner=owner_record,
        )


    def save(self, *args, **kwargs):
        if self.supervisor != self:
            super(User, self).save(*args, **kwargs)
        else:
            raise Exception('A user can\'t be their own supervisor')

    @staticmethod
    def create_address_owner(instance):
        ao = AddressOwner.objects.create()
        ao.save()
        instance.address_owner = ao
        instance.address_owner.save()
        instance.save()

    @staticmethod
    def create_file_owner(instance):
        fo = FileOwner.objects.create()
        fo.save()
        instance.file_owner = fo
        instance.file_owner.save()
        instance.save()


# TODO: Disallow Django user creation if Cognito user creation fails
    @staticmethod
    def create_cognito_user(instance, password):
        
        client = CognitoHelper.get_client()

        username = str(instance.email)
        try:
            response = client.sign_up(
                ClientId=settings.COGNITO_APP_CLIENT_ID,
                Username=username,
                Password=password,
                UserAttributes=[
                    {
                        'Name': 'email',
                        'Value': str(instance.email)
                    },
                    {
                        'Name': 'phone_number',
                        'Value': str(instance.phone)
                    },
                ]
            )
        except Exception as e:
            instance.delete()
            return

        try:
            response = client.admin_get_user(
                UserPoolId=settings.COGNITO_USER_POOL_ID,
                Username=username
            )
            instance.cognito_id = [item for item in response.get('UserAttributes') if item['Name'] == 'sub'][0]['Value']
        except Exception as e:
            print(e)

        #TODO: do as below
        cognito_confirm_sign_up(username)


    @staticmethod
    def create_setup(sender, instance, created, *args, **kwagrs):
        if not created:
            return
        else:
            #User.create_cognito_user(instance)
            User.create_address_owner(instance)
            User.create_file_owner(instance)


    @staticmethod
    def delete_address_owner(instance):
        if instance.address_owner:
            instance.address_owner.delete()


    @staticmethod
    def delete_file_owner(instance):
        if instance.file_owner:
            instance.file_owner.delete()

    @staticmethod
    def delete_cognito_user(instance):
        
        client = CognitoHelper.get_client()

        try:
            response = client.admin_delete_user(
                UserPoolId=settings.COGNITO_USER_POOL_ID,
                Username=str(instance.email)
            )
        except Exception as e:
            print(e)

    @staticmethod
    def delete_cleanup(sender, instance, *args, **kwargs):
        User.delete_address_owner(instance)
        User.delete_file_owner(instance)
        User.delete_cognito_user(instance)


    def __str__(self):
        return self.name + ', ' + self.email


class Role(models.Model):
    ROLE_CHOICES = [
        ('Administrator', 'Administrator'),
        ('Coordinator', 'Coordinator'),
        ('Worker', 'Worker'),
    ]

    name = models.CharField(
        max_length=13,
        choices=ROLE_CHOICES,
        unique=True)

    def __str__(self):
        return self.name


class Absence(models.Model):
    user = models.ForeignKey(
        'User', on_delete=models.CASCADE, null=True, blank=True,)
    date_start = models.DateField()
    date_end = models.DateField()
    state = models.CharField(
        max_length=9,
        choices=[
            ('Pending', 'pending'),
            ('Confirmed', 'confirmed'),
            ('Rejected', 'rejected')
        ],
        default='Pending')
    paid = models.BooleanField(default=False)
    description = models.TextField(null=True, blank=True)
    exclude_saturday = models.BooleanField(default=True)
    exclude_sunday = models.BooleanField(default=True)


    def total_days(self):
        date_current = self.date_start
        day_delta = datetime.timedelta(days=1)
        days_total = 0

        while date_current <= self.date_end:
            if (
                not (self.exclude_saturday and date_current.weekday() == 5)
                and 
                not (self.exclude_sunday and date_current.weekday() == 6)
            ):
                days_total += 1

            date_current += day_delta
        
        return days_total


    def save(self, *args, **kwargs):
        if self.date_start <= self.date_end:
            super(Absence, self).save(*args, **kwargs)
        else:
            raise ValueError('date_end can\'t be earlier than date_start')


    def __str__(self):
        return f'Absence {self.id}, user {self.user}, from {self.date_start} to {self.date_end}, {self.total_days()} days'


class Company(models.Model):
    name = models.CharField(max_length=100, null=False, blank=False)

    def __str__(self):
        return f'id: {self.id}; name: {self.name};'

    class Meta:
        verbose_name_plural = 'companies'
    

post_delete.connect(User.delete_cleanup, sender=User)
post_save.connect(User.create_setup, sender=User)


# TODO: Change it to a normal sign up confirmation endpoint
def cognito_confirm_sign_up(username):
    
    client = CognitoHelper.get_client()

    response = client.admin_confirm_sign_up(
        UserPoolId=settings.COGNITO_USER_POOL_ID,
        Username=username,
    )
