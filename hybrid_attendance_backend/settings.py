

# """
# Django settings for hybrid_attendance_backend project.
# """

from pathlib import Path
import os
from datetime import timedelta
from cryptography.fernet import Fernet
from dotenv import load_dotenv

AUTH_USER_MODEL = 'core_app.User'


# Load environment variables from .env
load_dotenv()

# Build paths inside the project
BASE_DIR = Path(__file__).resolve().parent.parent
ENCRYPTION_KEY= os.getenv('FERNET_KEY')
# Initialize global Fernet instance
FERNET = Fernet(ENCRYPTION_KEY.encode())
# SECURITY
SECRET_KEY = os.getenv('SECRET_KEY', 'your-dev-secret-key')
DEBUG = os.getenv('DEBUG', 'True') == 'True'
ALLOWED_HOSTS = [
    'localhost',
    '127.0.0.1',
    "192.168.1.5"
    
]


# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third-party apps
    'rest_framework',
    'drf_spectacular',
    'corsheaders',
    'django_filters',
    'core_app',  
    'web_app',
    'superadmin_app',
    'salary_slip_app',
    
    'rest_framework_simplejwt.token_blacklist',
    'django_crontab',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',  
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'core_app.middleware.encryption_middleware.ResponseEncryptionMiddleware',
    # flutter
    'core_app.middleware.react_crypto_middleware.ReactCryptoMiddleware',      
    # react
]

ROOT_URLCONF = 'hybrid_attendance_backend.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],  # Add templates folder if needed
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'hybrid_attendance_backend.wsgi.application'

# Database: PostgreSQL
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('POSTGRES_DB', 'hybrid_attendance_db'),
        'USER': os.getenv('POSTGRES_USER', 'postgres'),
        'PASSWORD': 'admin',
        'HOST': os.getenv('POSTGRES_HOST', 'localhost'),
        'PORT': os.getenv('POSTGRES_PORT', '5432'),
        "CONN_MAX_AGE": 60,  
    }
}

EMAIL_BACKEND = os.getenv('EMAIL_BACKEND')
EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = os.getenv('EMAIL_PORT', 587)
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True') == 'True'
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', EMAIL_HOST_USER)

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',},
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kolkata'
USE_I18N = True
USE_TZ = True
DATE_INPUT_FORMATS = ['%d-%m-%Y']

# Static & Media Files
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'


# Allow cross-origin cookies
# SESSION_COOKIE_SAMESITE = "None"
# SESSION_COOKIE_SECURE = False  # True if using HTTPS
# CSRF_COOKIE_SAMESITE = "None"
# CSRF_COOKIE_SECURE = False     # True if using HTTPS

# Make sure credentials are allowed


CORS_ALLOW_CREDENTIALS = True
# Restart backend

CORS_ALLOW_HEADERS = ["*"]

# settings.py
SESSION_COOKIE_SAMESITE = 'Lax'  
CSRF_COOKIE_SAMESITE = 'Lax'
SESSION_COOKIE_SECURE = False      # must be False on HTTP
CSRF_COOKIE_SECURE = False
CORS_ALLOW_CREDENTIALS = True

CSRF_TRUSTED_ORIGINS = [
    "http://localhost:5173",
]
# from corsheaders.defaults import default_headers
CORS_ALLOW_HEADERS = [
    "accept",
    "accept-encoding",
    "authorization",
    "content-type",
    "origin",
    "user-agent",
    "x-client",
    "x-csrftoken",
    "x-requested-with",
    "expires",
    "cache-control",
    "pragma",


]



# CORS settings (React frontend)
CORS_ALLOWED_ORIGINS = [
"http://localhost:5173",  # React (Vite dev server)
    "http://127.0.0.1:5173",
    "http://192.168.1.12:5173",
    "http://localhost:3000",
]

# REST Framework settings
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    
      'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',

      'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',  
    )
}

OFFICE_LOCATION = {
    "lat": 10.0921616,      # example — replace with your office latitude
    "lng": 76.3180602,     # office longitude
    "radius": 200         # allowed radius in meters
}


# JWT Settings
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=15),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,                      
}

# Celery configuration
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


CORS_ALLOW_ALL_ORIGINS = True

