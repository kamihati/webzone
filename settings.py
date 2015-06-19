#coding: utf-8
'''
Created on 2014-3-24

@author: Administrator
'''
"""
Django settings for WebZone project.

For more information on this file, see
https://docs.djangoproject.com/en/1.6/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.6/ref/settings/
"""
from WebZone.conf import is_debug

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
FONT_ROOT = os.path.join(BASE_DIR, 'font')
FONT_IMG_URL = '/static/images/font/'


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.6/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'e0d26v6e+1yf-2op5^bxa9y+za-zae0ka1laut76f&_wcb$yw&'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = is_debug

TEMPLATE_DEBUG = is_debug

AUTH_USER_MODEL = 'account.AuthUser'

LOGIN_URL = '/account/login/'

LOGOUT_URL = '/account/logout/'

LOGIN_REDIRECT_URL = '/account/profile/'

ALLOWED_HOSTS = []



# Database
# https://docs.djangoproject.com/en/1.6/ref/settings/#databases
from WebZone.conf import DB_ENGINE, DB_NAME, DB_USER, DB_PASS, DB_HOST, DB_PORT
DATABASES = {
    'default': {
        'ENGINE': DB_ENGINE,
        'NAME': DB_NAME,
        'USER': DB_USER,
        'PASSWORD': DB_PASS,
        'HOST': DB_HOST,
        'PORT': DB_PORT,
    }
}


from WebZone.conf import MEMCACHED_ADDR
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
        'LOCATION': MEMCACHED_ADDR,
        'TIMEOUT': 1,
    },
#    'default': {
#        'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
#        'LOCATION': 'F:/DjangoCache', #'/var/tmp/django_cache',
#        'TIMEOUT': 60,
#    },
}
#CACHE_MIDDLEWARE_ALIAS = 'default'
#CACHE_MIDDLEWARE_SECONDS = 60
#CACHE_MIDDLEWARE_ANONYMOUS_ONLY = True
CACHE_MIDDLEWARE_KEY_PREFIX = ''
CACHE_MIDDLEWARE_SECONDS = 60*15
CACHE_MIDDLEWARE_ALIAS = 'default'

# 按秒计算
SESSION_COOKIE_AGE = 60*60*8
SESSION_SAVE_EVERY_REQUEST = True
#SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'


# Application definition

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    #'django.contrib.messages',
    'django.contrib.staticfiles',
    'account',
    'library',
    'gateway',
    'diy',
    'manager',
    'widget',
    'topic',
    'manager2',
    'resource',
    'online_status',
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    #'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = 'WebZone.urls'

WSGI_APPLICATION = 'WebZone.wsgi.application'


# Internationalization
# https://docs.djangoproject.com/en/1.6/topics/i18n/

LANGUAGES = (('en', 'English'),
             ('zh-cn', 'Simplified Chinese'),)

LANGUAGE_CODE = 'zh-CN'

TIME_ZONE = 'Asia/Shanghai'

USE_I18N = False

USE_L10N = False

USE_TZ = False


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.6/howto/static-files/

STATIC_URL = '/static/'
#STATIC_URL = 'http://10.0.0.177:81/static/'
#STATIC_ROOT = os.path.join(BASE_DIR, 'static')
STATIC_ROOT = os.path.join(BASE_DIR, 'static1')
STATICFILES_DIRS = (
    os.path.join(BASE_DIR, 'static'),
    os.path.join(BASE_DIR, 'manager/static'),
)



# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
#MEDIA_ROOT = ''
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = '/media/'



# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
    #'django.template.loaders.eggs.load_template_source',
)

TEMPLATE_CONTEXT_PROCESSORS = (
     'django.contrib.auth.context_processors.auth',
#     'django.core.context_processors.debug',
#     'django.core.context_processors.i18n',
     'django.core.context_processors.media',
     'django.core.context_processors.request',
#     'django.contrib.messages.context_processors.messages',
)


TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    os.path.join(BASE_DIR, 'templates'),
)



