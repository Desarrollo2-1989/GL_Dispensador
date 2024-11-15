"""
Django settings for Dispensador project.

Generated by 'django-admin startproject' using Django 5.0.7.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.0/ref/settings/
"""

import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-rf58ip&+p!urt_gfc7v2+7pd#mut!gt^@rg-@14e1igmio7qu*'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1', '192.168.8.87'] # Configuración de los hosts permitidos para acceder a la aplicación


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'tasks', # Aplicación personalizada llamada "tasks"
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'Dispensador.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],  # Directorio donde se encuentran las plantillas
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

WSGI_APPLICATION = 'Dispensador.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases

# Configuración de la base de datos
DATABASES = {
   "default": {
        "ENGINE": "django.db.backends.postgresql", # Motor de base de datos
        "NAME": "DPC", # Nombre de la base de datos
        "USER": "postgres", # Usuario de la base de datos
        "PASSWORD": "GL1989", # Contraseña de la base de datos
        "HOST": "localhost", # Host de la base de datos
        "PORT": "5438", # Puerto de la base de datos
    }
}


# Password validation
# https://docs.djangoproject.com/en/5.0/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/5.0/topics/i18n/

# Zona horaria del proyecto.
# 'America/Bogota' establece la hora según la región de Bogotá, Colombia.
TIME_ZONE = 'America/Bogota'

# Indica si se debe habilitar la internacionalización en el proyecto.
# Esto permite la traducción de textos y otros elementos según la configuración regional.
USE_I18N = True

# Indica si se debe utilizar soporte para zonas horarias.
# Cuando está habilitado, Django manejará las fechas y horas teniendo en cuenta las zonas horarias.
USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.0/howto/static-files/


STATIC_URL = 'static/'  # Prefijo de URL para servir archivos estáticos

STATIC_ROOT = os.path.join(BASE_DIR, 'static')  # Directorio donde se recopilarán y servirán los archivos estáticos


# Default primary key field type
# https://docs.djangoproject.com/en/5.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# configuracion para enviar correo
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'mail.glingenieros.co'   # Servidor saliente (SMTP)
EMAIL_PORT = 26                        # Puerto SMTP
EMAIL_USE_TLS = False                  # No usar TLS porque el puerto 26 usualmente no lo requiere
EMAIL_USE_SSL = False                  # No usar SSL
EMAIL_HOST_USER = 'dispensador@glingenieros.co'  # Tu dirección de correo electrónico
EMAIL_HOST_PASSWORD = 'k#Iy5V7]D!PO'  # La contraseña de tu cuenta de correo
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER
DEFAULT_CHARSET = 'utf-8'

