import os

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

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

TEMPLATES = [{
    'OPTIONS': {
        'builtins': [
            'mezzanine.template.loader_tags',  # dummy to remove Mezzanine warning
        ]
    },
}]

MIDDLEWARE_CLASSES = (
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "janeus.utils.CurrentRequestMiddleware",
)

ALLOWED_HOSTS = ['example.com']
USE_I18N = False
USE_TZ = False
TIME_ZONE = 'Europe/Amsterdam'

#############
# MEZZANINE #
#############

SITE_ID = 1  # required dummy setting
PACKAGE_NAME_FILEBROWSER = 'filebrowser'  # required dummy setting

try:
    from mezzanine.utils.conf import set_dynamic_settings
except ImportError:
    pass
else:
    set_dynamic_settings(globals())
