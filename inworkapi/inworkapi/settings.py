import os

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'gm^3*#2*)@v$m)-(xv$+g%wc)nvb@)hn4#0#11k2o-p2*8_vp3'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = [
    'herokuinworkapi.herokuapp.com',
    '127.0.0.1',
]


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # External packages
    'django_filters',
    'drf_yasg',
    'rest_framework',
    'phonenumber_field',

    # Local apps
    'users',
    'utils',
    'clients',
    'orders',
    'api',
]

MIDDLEWARE = [
    # Heroku
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'inworkapi.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': ['templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'inworkapi.wsgi.application'


# Database
# https://docs.djangoproject.com/en/2.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2', 
        'NAME': 'inworktestdb',
        'USER': 'gz',
        'PASSWORD': 'watermelon',
        'HOST': 'localhost',
        'PORT': '',
    }
}

# Password validation
# https://docs.djangoproject.com/en/2.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/2.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.2/howto/static-files/

STATIC_URL = '/static/'

STATICFILES_DIRS = (
    os.path.join(BASE_DIR, 'static'),
    )

# Heroku
#  Add configuration for static files storage using whitenoise
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
STATIC_ROOT = os.path.join(PROJECT_ROOT, 'static')

AUTH_USER_MODEL = 'users.User'

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    #'django_warrant.backend.CognitoBackend',
]

# AWS Cognito settings
#COGNITO_USER_POOL_ID = 'eu-central-1_4W9Ujr278'
#COGNITO_APP_ID = '1s4ubtdruk0t08773upbusgum7'
#COGNITO_ATTR_MAPPING = {
    #'email': 'email',
    #'phone': 'phone',
    #'custom:name': 'name',
    #'custom:surname': 'surname',
    #'custom:role': 'role'
#}


REST_FRAMEWORK = {
    # Use Django's standard `django.contrib.auth` permissions,
    # or allow read-only access for unauthenticated users.
    'DEFAULT_SCHEMA_CLASS': 'rest_framework.schemas.coreapi.AutoSchema',
    'DEFAULT_PERMISSION_CLASSES': [
        #'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.BasicAuthentication',
        #'django_warrant.backend.CognitoBackend',
        'django_cognito_jwt.JSONWebTokenAuthentication',
        #'rest_framework.authentication.SessionAuthentication',
        #'inworkapi.authentication.FirebaseAuthentication', 
    ]
}

# FIREBASE_KEY = 'static/config/inworktest-firebase-adminsdk-vxvhx-6658e12f8d.json'

# FIREBASE_CONFIG = {
#     'apiKey': 'AIzaSyDV00d68812eZuIoCMKKX27w7tEGs_1Bwg',
#     'authDomain': 'inworktest.firebaseapp.com',
#     'databaseURL': 'https://inworktest.firebaseio.com',
#     'projectId': 'inworktest',
#     'storageBucket': 'inworktest.appspot.com',
#     'messagingSenderId': '111246495065',
#     'appId': '1:111246495065:web:f4a63df5719dd825e41048'
# }
# import firebase_admin
# cred = firebase_admin.credentials.Certificate(FIREBASE_KEY)
# firebase_admin.initialize_app(cred)

# Heroku
import dj_database_url 
prod_db  =  dj_database_url.config(conn_max_age=500)
DATABASES['default'].update(prod_db)

# Cognito
# TODO: set these up as environment variables
COGNITO_USER_POOL_ID = 'eu-central-1_SZFF66v4y'
COGNITO_APP_CLIENT_ID = '8n4apo9vid3rje18eijbk6plh'
COGNITO_APP_ID = COGNITO_APP_CLIENT_ID
COGNITO_ATTR_MAPPING = {
    'email': 'email',
    'phone_number': 'phone',
}
COGNITO_AWS_REGION = 'eu-central-1'
COGNITO_USER_POOL = COGNITO_USER_POOL_ID
COGNITO_AUDIENCE = COGNITO_APP_CLIENT_ID