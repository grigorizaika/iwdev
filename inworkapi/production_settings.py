import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# TODO: print->logging
print('using production settings')

SECRET_KEY = 'gm^3*#2*)@v$m)-(xv$+g%wc)nvb@)hn4#0#11k2o-p2*8_vp3'

DEBUG = False

APPEND_SLASH = True

ALLOWED_HOSTS = [
    '127.0.0.1',
    '.compute.amazonaws.com',
]

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

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2', 
        'NAME': 'inwork_db',
        'USER': 'inwork_user',
        'PASSWORD': 'sr2R#97f7GKf',
        'HOST': 'localhost',
        'PORT': '',
    }
}

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

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

STATIC_URL = '/static/'

STATICFILES_DIRS = (
    os.path.join(BASE_DIR, 'static'),
)

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

STATIC_ROOT = os.path.join(PROJECT_ROOT, 'static')

AUTH_USER_MODEL = 'users.User'

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
]

REST_FRAMEWORK = {
    # Use Django's standard `django.contrib.auth` permissions,
    # or allow read-only access for unauthenticated users.
    'DEFAULT_SCHEMA_CLASS': 'rest_framework.schemas.coreapi.AutoSchema',
    'DEFAULT_PERMISSION_CLASSES': [
        #'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.BasicAuthentication',
        'django_cognito_jwt.JSONWebTokenAuthentication',
    ]
}

# Cognito
COGNITO_USER_POOL_ID = os.getenv('INWORK_COGNITO_USER_POOL_ID')
COGNITO_APP_CLIENT_ID =  os.getenv('INWORK_COGNITO_APP_CLIENT_ID')
COGNITO_AWS_REGION =  os.getenv('INWORK_COGNITO_AWS_REGION')
AWS_ACCESS_KEY_ID = os.getenv('INWORK_AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('INWORK_AWS_SECRET_ACCESS_KEY')
COGNITO_APP_ID = COGNITO_APP_CLIENT_ID
COGNITO_USER_POOL = COGNITO_USER_POOL_ID
COGNITO_AUDIENCE = COGNITO_APP_CLIENT_ID


