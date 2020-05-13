import json
import os

# TODO: Use django-environ
VARIABLES_PATH = os.path.abspath('/home/grgr/Projects/inwork/variables.json')

with open(VARIABLES_PATH) as variables_json_file:
    variables_dict = json.load(variables_json_file)


# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# TODO: print->logging
print('using development settings')

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = variables_dict['DJANGO_INWORK_SECRET_KEY']

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

APPEND_SLASH = True


SECURE_CONTENT_TYPE_NOSNIFF = True

SECURE_BROWSER_XSS_FILTER = True

X_FRAME_OPTIONS = 'DENY'

# TODO: set to True after Apache setup for port 443
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
# TODO: set to 1 after Apache setup for port 443
SECURE_HSTS_SECONDS = 0


ALLOWED_HOSTS = [
    'inworkapi.herokuapp.com',
    '127.0.0.1',
    '.compute.amazonaws.com',
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
    'csp.middleware.CSPMiddleware',
]

ROOT_URLCONF = 'inworkapi.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': ['templates', BASE_DIR + "/templates", ],
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

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'logfile': {
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'mylogs.log'),
        },
    },
    'loggers': {
        'django': {
            'handlers': ['logfile'],
        },
    },
}

# Database
# https://docs.djangoproject.com/en/2.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': variables_dict['INWORK_DB_NAME'],
        'USER': variables_dict['INWORK_DB_USER'],
        'PASSWORD':  variables_dict['INWORK_DB_PASSWORD'],
        'HOST': 'localhost',
        'PORT': '',
        'TEST': {
            'NAME': 'test',
            'USER': 'test',
            'PASSWORD': 'test',
        }
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
# Add configuration for static files storage using whitenoise
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
STATIC_ROOT = os.path.join(PROJECT_ROOT, 'static')

AUTH_USER_MODEL = 'users.User'

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    # 'django_warrant.backend.CognitoBackend',
]

REST_FRAMEWORK = {
    # Use Django's standard `django.contrib.auth` permissions,
    # or allow read-only access for unauthenticated users.
    'DEFAULT_SCHEMA_CLASS': 'rest_framework.schemas.coreapi.AutoSchema',
    'DEFAULT_PERMISSION_CLASSES': [
        # 'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.BasicAuthentication',
        'django_cognito_jwt.JSONWebTokenAuthentication',
    ]
}

# Heroku
# import dj_database_url
# prod_db  =  dj_database_url.config(conn_max_age=500)
# DATABASES['default'].update(prod_db)

# Cognito
COGNITO_USER_POOL_ID = variables_dict['INWORK_COGNITO_USER_POOL_ID']
COGNITO_APP_CLIENT_ID = variables_dict['INWORK_COGNITO_APP_CLIENT_ID']
COGNITO_AWS_REGION = variables_dict['INWORK_COGNITO_AWS_REGION']
AWS_ACCESS_KEY_ID = variables_dict['INWORK_AWS_ACCESS_KEY_ID']
AWS_SECRET_ACCESS_KEY = variables_dict['INWORK_AWS_SECRET_ACCESS_KEY']

COGNITO_USER_POOL = COGNITO_USER_POOL_ID
COGNITO_APP_ID = COGNITO_APP_CLIENT_ID
COGNITO_AUDIENCE = COGNITO_APP_CLIENT_ID

APPEND_SLASH = True
