import boto3
import datetime
# import firebase_admin

from botocore.exceptions import ParamValidationError
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.db import models
from django.db.models.signals import (post_delete, post_save)
from django.utils.translation import gettext as _
from phonenumber_field.modelfields import PhoneNumberField

from inworkapi.settings import (COGNITO_USER_POOL_ID, COGNITO_APP_CLIENT_ID, COGNITO_ATTR_MAPPING)
#from inworkapi.settings import COGNITO_APP_CLIENT_SECRET
# from inworkapi.settings import FIREBASE_KEY
# from inworkapi.settings import FIREBASE_CONFIG
from utils.models import (AddressOwner, Address)
from warrant import Cognito


class UserManager(BaseUserManager):
    use_in_migrations = True


    def create_user(self, email, name, surname, phone, password=None):
        # TODO: Ensure that if a Django User creation fails, Firebase User creation fails too
        if not email:
            raise ValueError("An email address has not been provided")

        djangoUser = self.model(
            email=self.normalize_email(email),
            name=name,
            surname=surname,
            phone=phone,
            #firebaseId = firebaseUser.uid
        )
        
        djangoUser.set_password(password)
        djangoUser.save()

        User.create_cognito_user(djangoUser, password)

        # TODO: if create_cognito_user fails, delete django user
        
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
            djangoUser.role = Role.objects.get_or_create(
                name='Administrator'
            )
        except ValueError:
            print('Didn\'t assign a role to the user')

        djangoUser.save()
        return djangoUser


    def get_or_create_for_cognito(self, payload):
        cognito_id = payload['sub']

        try:
            return self.get(cognito_id=cognito_id)
        except self.model.DoesNotExist:
            pass

        return user


# TODO: change UserManager according to the updated User model
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
                                blank=True
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
                                limit_choices_to={'role__name': 'administrator'})
    created_at               = models.DateTimeField(auto_now_add=True)
    cognito_id               = models.CharField(max_length=191)
    profile_picture_url      = models.URLField(max_length=300, blank=True, null=True)
    # A required Django field. Does not represent the business logic.
    is_staff                = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name', 'surname', 'phone']


    def addresses(self):
        return Address.objects.filter(owner=self.address_owner)


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
        instance.address_owner = AddressOwner.objects.create()


# TODO: Disallow Django user creation if Cognito user creation fails
    @staticmethod
    def create_cognito_user(instance, password):
        username = str(instance.email).replace('@', '.')

        # TODO: rewrite using boto3
        try:
            client = boto3.client('cognito-idp', region_name='eu-central-1')
            response = client.admin_create_user(
                UserPoolId=COGNITO_USER_POOL_ID,
                Username=username,
                UserAttributes=[
                    {
                        'Name': 'email',
                        'Value': instance.email
                    },
                    {
                        'Name': 'phone_number',
                        'Value': instance.phone
                    },
                ]
            )
        except Exception as e:
            instance.delete()

        try:
            client = boto3.client('cognito-idp', region_name='eu-central-1')
            response = client.admin_get_user(
                UserPoolId=COGNITO_USER_POOL_ID,
                Username=username
            )
            instance.cognito_id = [item for item in response.get('UserAttributes') if item['Name'] == 'sub'][0]['Value']
        except Exception as e:
            print(e)


    # # TODO: add photo_url
    # @staticmethod
    # def create_firebase_user(instance):
    #     try:
    #         firebaseUser = auth.create_user(
    #             email=instance.email,
    #             email_verified=False,
    #             phone_number=str(instance.phone),
    #             password=instance.password,
    #             display_name=(instance.name + ' ' + instance.surname),
    #             # photo_url='http://www.example.com/12345678/photo.png',
    #             disabled=False)
    #         print('Sucessfully created new user: {0}'.format(firebaseUser.uid))
    #         instance.firebaseId = firebaseUser.uid
    #     except EmailAlreadyExistsError as eaee:
    #         print('EAEE')


    @staticmethod
    def create_setup(sender, instance, created, *args, **kwagrs):
        if not created:
            return
        else:
            #User.create_firebase_user(instance)
            #User.create_cognito_user(instance)
            User.create_address_owner(instance)

    @staticmethod
    def delete_address_owner(instance):
        if instance.address_owner:
            instance.address_owner.delete()


    @staticmethod
    def delete_cognito_user(instance):
        client = boto3.client('cognito-idp', region_name='eu-central-1')
        try:
            response = client.admin_delete_user(
                UserPoolId=COGNITO_USER_POOL_ID,
                Username=str(instance.email).replace('@', '.')
            )
        except Exception as e:
            print(e)
        

    @staticmethod
    def delete_cleanup(sender, instance, *args, **kwargs):
        User.delete_address_owner(instance)
        User.delete_cognito_user(instance)
        

    def __str__(self):
        return self.name + ', ' + self.email


class Role(models.Model):
    ROLE_CHOICES = [
        ('Administrator', 'administrator'),
        ('Coordinator', 'coordinator'),
        ('Worker', 'worker'),
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


    def save(self, *args, **kwargs):
        if self.dateEnd > self.dateStart:
            super(Absence, self).save(*args, **kwargs)
        else:
            raise Exception('dateEnd can\'t be earlier than dateStart')


    def __str__(self):
        return (str(self.user) + ', from ' + str(self.dateStart) + ' to ' + str(self.dateEnd) + ' ' + str(self.dateStart-self.dateEnd))


class Company(models.Model):
    name = models.CharField(max_length=100, null=False, blank=False)


    def __str__(self):
        return 'id: ' + str(self.id) + '; ' + 'name: ' + str(self.name)


post_delete.connect(User.delete_cleanup, sender=User)
post_save.connect(User.create_setup, sender=User)