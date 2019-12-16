import datetime

from django.contrib.auth.models import AbstractBaseUser,BaseUserManager
from django.db import models
from django.utils.translation import gettext as _


class UserManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, email, name, password=None):
        
        if not email:
            raise ValueError("An email address has not been provided")
        
        user = self.model(
            email = self.normalize_email(email),
            name = name
        )
        
        user.set_password(password)
        user.save(using=self._db)

        return user

    def create_superuser(self, email, name, password):
        
        if not email:
            raise ValueError("An email address has not been provided")

        user = self.create_user(
            email = self.normalize_email(email),
            password = password,
            name = "True",
        )
        
        user.staff = True
        user.admin = True
        user.save(using=self._db)
        
        return user


class User(AbstractBaseUser):
    email                   = models.EmailField(_('email address'), unique=True)
    name                    = models.CharField(max_length=40)
    createdAt               = models.DateTimeField(auto_now_add=True)
    
    objects                 = UserManager()

    USERNAME_FIELD          = 'email'
    REQUIRED_FIELDS         = ['name', 'created_at']

    def __str__(self):
        return self.name + ', ' + self.email

