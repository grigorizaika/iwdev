import datetime
from firebase_admin import auth
from firebase_admin._auth_utils import EmailAlreadyExistsError

from django.contrib.auth.models import AbstractBaseUser,BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.db import models
from django.utils.translation import gettext as _
from phonenumber_field.modelfields import PhoneNumberField

firebaseConfig = {
    'apiKey': 'AIzaSyDV00d68812eZuIoCMKKX27w7tEGs_1Bwg',
    'authDomain': 'inworktest.firebaseapp.com',
    'databaseURL': 'https://inworktest.firebaseio.com',
    'projectId': 'inworktest',
    'storageBucket': 'inworktest.appspot.com',
    'messagingSenderId': '111246495065',
    'appId': '1:111246495065:web:f4a63df5719dd825e41048'
}

class UserManager(BaseUserManager):
    use_in_migrations = True

    # TODO: Also defing user deletion (delete firebase user when django user gets deleted)

    def create_user(self, email, name, surname, phone, password=None):
    # TODO: Ensure that if a Django User creation fails, Firebase User creation fails too
        if not email:
            raise ValueError("An email address has not been provided")
        
        djangoUser = self.model(
            email = self.normalize_email(email),
            name = name,
            surname = surname,
            phone = phone,
            #firebaseId = firebaseUser.uid
        )
        
        djangoUser.set_password(password)
        djangoUser.save(using=self._db)

        try:
            firebaseUser = auth.create_user(
                email=email,
                email_verified=False,
                phone_number=phone,
                password=password,
                display_name= (name + ' ' + surname),
                #photo_url='http://www.example.com/12345678/photo.png',
                disabled=False)
            print('Sucessfully created new user: {0}'.format(firebaseUser.uid))
            djangoUser.firebaseId = firebaseUser.uid
        except EmailAlreadyExistsError as eaee:
            print ('EAEE')

        return djangoUser

    def create_superuser(self, email, name, surname, phone, password):
        
        if not email:
            raise ValueError("An email address has not been provided")
        
        djangoUser = self.create_user(
            email = self.normalize_email(email),
            password = password,
            name = "True",
            surname = surname,
            phone = phone,
            
            #**kwargs
        )
        djangoUser.is_superuser = True
        djangoUser.is_staff = True
        djangoUser.admin = True
        djangoUser.save(using=self._db)

        try:
            firebaseUser = auth.create_user(
                email=email,
                email_verified=False,
                phone_number=phone,
                password=password,
                display_name= (name + ' ' + surname),
                #photo_url='http://www.example.com/12345678/photo.png',
                disabled=False)
            print('Sucessfully created new user: {0}'.format(firebaseUser.uid))
            djangoUser.firebaseId = firebaseUser.uid
        except EmailAlreadyExistsError as eaee:
            # TODO: what if there really is an email collision?
            print("EAEE")
        
        return djangoUser

# TODO: change UserManager according to the updated User model
class User(AbstractBaseUser, PermissionsMixin):
    username = None
    email                   = models.EmailField(_('email address'), unique=True)
    name                    = models.CharField(max_length=40)
    surname                 = models.CharField(max_length=40)
    phone                   = PhoneNumberField(null=False, blank=False, unique=True)
    address                 = models.ForeignKey('utils.Address', on_delete=models.CASCADE, null=True)
    # TODO: profilePictureUrl, after the Firebase storage integration
    role                    = models.ForeignKey('Role', on_delete=models.CASCADE, null=True, blank=True,)
    supervisor              = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, limit_choices_to={'role__name': 'administrator'})
    createdAt               = models.DateTimeField(auto_now_add=True)
    firebaseId              = models.CharField(max_length=191, null=False, blank=False, unique=True)

    # A required Django field. Does not represent the business logic.
    is_staff                = models.BooleanField(default=False)

    objects                 = UserManager()

    USERNAME_FIELD          = 'email'
    REQUIRED_FIELDS         = ['name', 'surname', 'phone']

    def save(self, *args, **kwargs):
        if self.supervisor != self:
            super(User, self).save(*args, **kwargs)
        else:
            raise Exception('A user can\'t be their own supervisor')

    def __str__(self):
        return self.name + ', ' + self.email


class Role(models.Model):
    ROLE_CHOICES = [
        ('Administrator', 'administrator'),
        ('Coordinator', 'coordinator'),
        ('Worker', 'worker'),
    ]
    
    name                    = models.CharField(
                                max_length=13,
                                choices=ROLE_CHOICES,
                                unique=True)

    def __str__(self):
        return self.name


class Absence(models.Model):
    user                    = models.ForeignKey('User', on_delete=models.CASCADE, null=True, blank=True,)
    dateStart               = models.DateField()
    dateEnd                 = models.DateField()
    state                   = models.CharField(
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
        return (str(self.user) + ', from ' + str(self.dateStart) + ' to ' + str(self.dateEnd) + ' ' + str(self.dateStart-self.dateEnd) )