from decouple import config
from datetime import timedelta
from pathlib import Path
import dj_database_url

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('DJANGO_SECRET_KEY')
# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DJANGO_DEBUG', default=True, cast=bool)

ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',

    'accounts',
    'widgets',
    'submissions',
    'dashboard',
]


MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',   # must sit high, before CommonMiddleware
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

CORS_ALLOW_ALL_ORIGINS = True     # public endpoints (config + submission) must accept any customer site
CORS_ALLOW_CREDENTIALS = False    # JWT goes via Authorization header, not cookies — no credentials needed cross-origin

DATA_UPLOAD_MAX_MEMORY_SIZE = 20 * 1024   # 20KB — public form payloads are tiny; oversized body → Django raises 400 automatically

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_THROTTLE_RATES': {
        'submission_ip': '10/min',
        'submission_widget': '60/min',
    },
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
}

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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

WSGI_APPLICATION = 'config.wsgi.application'
CORS_ALLOW_ALL_ORIGINS = True     # applies only within CORS_URLS_REGEX below
CORS_ALLOW_CREDENTIALS = False

# django-cors-headers only attaches CORS headers to paths matching this regex.
# Public, embeddable surfaces (submission + widget config) get open CORS —
# any customer site can call them. Admin/authenticated surfaces (widget CRUD,
# dashboard, auth) are NOT matched here, so browsers block cross-origin JS
# from reading their responses even with a valid token — this is the
# "disallowed origin" behavior the brief's demo script explicitly checks.
CORS_URLS_REGEX = r'^/(api/submissions/|api/widgets/[0-9a-fA-F-]{36}/config/|widget\.js)$'

# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases


DATABASE_URL = config('DATABASE_URL', default='sqlite:///db.sqlite3')

DATABASES = {
    'default': dj_database_url.parse(DATABASE_URL, conn_max_age=600)
}

GEO_PROVIDER_A_URL=config('GEO_PROVIDER_A_URL')
GEO_PROVIDER_B_URL=config('GEO_PROVIDER_B_URL')

# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = 'static/'

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
