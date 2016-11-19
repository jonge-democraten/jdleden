import os

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.10/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = ''

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sites',
    'mezzanine.core',
    'hemres',
    'jdleden',
]

TEMPLATES = [{},]

from jdleden.local_settings import *

LOG_DIR = BASE_DIR
LOGFILE_MAXSIZE = 10 * 1024 * 1024
LOGFILE_BACKUP_COUNT = 3

# Logging settings
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': "[%(asctime)s] %(levelname)s [%(name)s::%(funcName)s() (%(lineno)s)]: %(message)s",
            'datefmt': "%d/%b/%Y %H:%M:%S"
        },
        'simple': {
            'format': "[%(asctime)s] %(levelname)s: %(message)s"
        },
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose'
        },
        'file_django': {
            'level': 'ERROR',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(LOG_DIR, 'django.log'),
            'maxBytes': LOGFILE_MAXSIZE,
            'backupCount': LOGFILE_BACKUP_COUNT,
            'formatter': 'verbose'
        },
        'file_error': {
            'level': 'ERROR',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(LOG_DIR, 'error.log'),
            'maxBytes': LOGFILE_MAXSIZE,
            'backupCount': LOGFILE_BACKUP_COUNT,
            'formatter': 'verbose'
        },
        'file_debug': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(LOG_DIR, 'debug.log'),
            'maxBytes': LOGFILE_MAXSIZE,
            'backupCount': LOGFILE_BACKUP_COUNT,
            'formatter': 'verbose'
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file_django', 'console'],
            'propagate': True,
            'level': 'ERROR',
        },
        'hemres': {
            'handlers': ['file_debug', 'file_error', 'console'],
            'propagate': True,
            'level': 'DEBUG',
        },
        'jdleden': {
            'handlers': ['file_debug', 'file_error', 'console'],
            'propagate': True,
            'level': 'DEBUG',
        },
    },
}

PACKAGE_NAME_FILEBROWSER = 'filebrowser'