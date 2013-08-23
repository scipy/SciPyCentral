# Django settings for ``deploy`` project.
import django.conf.global_settings as DEFAULT_SETTINGS

import os, sys

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')

sys.path.insert(0, os.path.join(BASE_DIR, os.pardir))

DEBUG = True
TEMPLATE_DEBUG = DEBUG
ADMINS = (
    # ('Your Name', 'your_email@example.com'),
)

MANAGERS = ADMINS
DATABASES = {
    'default': {
        'ENGINE':   'django.db.backends.sqlite3',
        'NAME':     os.path.join(DATA_DIR, 'develop.db'), # Or path to database file if using sqlite3.
        'USER':     '', # Not used with sqlite3.
        'PASSWORD': '', # Not used with sqlite3.
        'HOST':     '', # Set to empty string for localhost. Not used with sqlite3.
        'PORT':     '', # Set to empty string for default. Not used with sqlite3.
    }
}

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# On Unix systems, a value of None will cause Django to use the same
# timezone as the operating system.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'America/Toronto'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale
USE_L10N = True

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/home/media/media.lawrence.com/media/"
MEDIA_ROOT = os.path.join(DATA_DIR, 'media')

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://media.lawrence.com/media/", "http://example.com/media/"
MEDIA_URL = '/media/'

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/home/media/media.lawrence.com/static/"
# Example: "/home/media/media.lawrence.com/media/"
STATIC_ROOT = os.path.join(DATA_DIR, 'static')

# URL prefix for static files.
# Example: "http://media.lawrence.com/static/"
STATIC_URL = '/static/'

# Additional locations of static files
STATICFILES_DIRS = (
    os.path.join(BASE_DIR, 'media'),
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
#    'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

# Make this unique, and don't share it with anybody.
SECRET_KEY = '3h%1b@kab#&f4o!!%8&_(-p@6mqm&(04vc_%*y$h+c$6j-s2rg'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
#     'django.template.loaders.eggs.Loader',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
)

ROOT_URLCONF = 'deploy.urls'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'deploy.wsgi.application'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    os.path.join(BASE_DIR, 'templates'),
)

# To get access to some global variables used in the templates
TEMPLATE_CONTEXT_PROCESSORS = DEFAULT_SETTINGS.TEMPLATE_CONTEXT_PROCESSORS + (
    'scipy_central.context_processors.global_template_variables',
    'django.core.context_processors.request',
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Uncomment the next line to enable the admin:
    'django.contrib.admin',
    # Uncomment the next line to enable admin documentation:
    'django.contrib.admindocs',
    # Humanize some data entries
    'django.contrib.humanize',

    # 3rd party apps:
    'haystack',
    'registration',
    'south',
    "widget_tweaks",

    #  Local apps
    'scipy_central.filestorage',
    'scipy_central.pages',
    'scipy_central.person',
    'scipy_central.submission',
    'scipy_central.tagging',
    'scipy_central.screenshot',
    'scipy_central.pagehit',
    'scipy_central.feeds',
)

# Link the user is redirected to if not logged in and they try to perform
# a function that only logged in users can do
LOGIN_URL = '/user/login/'

# django-registration required setting
ACCOUNT_ACTIVATION_DAYS = 7
REGISTRATION_OPEN = True    # permit users to create new accounts

# For users that have cookies disabled: sorry, you can't use this site
CSRF_FAILURE_VIEW = 'scipy_central.pages.views.csrf_failure'


# These settings define and modify the behaviour of the entire website.
# SciPy Central = SPC.
SPC = {
    # Delete unconfirmed submission after this number of days
    'unvalidated_subs_deleted_after': ACCOUNT_ACTIVATION_DAYS,

    # We only support Mercurial at the moment. Code can support git and
    # other version control systems in the future.
    # Do not change this once files have been added.
    'revisioning_backend': 'hg',

    # Can be left as '', but then we will search for the executable everytime
    # we need to access the repo. Rather specify the full path to the
    # revision control system executable.
    'revisioning_executable': '',

    # Where should files from each submission be stored?
    # Files are stored using revision control in directories as follows:
    #
    # <storage><submission_primary_key>/<submission_slug>.py
    # <storage><submission_primary_key>/LICENSE.txt
    # where <storage> is the variable defined next
    'storage_dir': os.path.join(DATA_DIR, 'code'),

    # Image storage directories. Do not change these settings. They are used
    # in the Sphinx extension to ensure user does not resize image beyond
    # the maximum width or height.
    'raw_image_dir': 'raw-images/%Y%m',
    'resized_image_dir': 'images/%Y%m',

    # Where are ZIP files staged? User's upload ZIP files; only the submission
    # is created, we retrieve the staged ZIP file and handle it appropriately
    # The staged files are then deleted. i.e. this is like a "tempdir".
    # This path is relative to MEDIA_ROOT.
    'ZIP_staging': 'zip-staging',

    # Where should logfiles be written? If DEBUG != True, then you are
    # responsible that this location is valid and exists. Overwrite the
    # location in ``local_settings.py`` below.
    'logfile_location': os.path.join(DATA_DIR, 'spc.log'),

    # Comments are compiled (using Sphinx) in this location. Again, you are
    # required to sure this location exists for production servers.
    'comment_compile_dir': os.path.join(DATA_DIR, 'compile'),

    # Default name of license file (e.g. 'COPYING.TXT')
    'license_filename': 'LICENSE.TXT',

    # Short link URL root (must end with a trailing slash).
    'short_URL_root': 'http://scpyce.org/',

    # Page hit horizon in days. Lists of views are sorted by the number of page
    # views over the past NNN days (the horizon).
    'hit_horizon': 60,

    # Number of entries per page is search output and table outputs
    'entries_per_page': 20,

    # Library submission maximum size (in bytes)
    'library_max_size': 25 * 1024 * 1024,

    # Image (screenshots) maximum size (in bytes)
    'image_max_size': 2 * 1024 * 1024,

    # We will strip out directories from common revision control systems
    # when users upload (ZIP) files
    'common_rcs_dirs': ['.hg', '.git', '.bzr', '.svn',],
}

# Put all the search settings in a single file
execfile(os.path.join(BASE_DIR, 'search_settings.py'))

# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error. See
#
# http://docs.djangoproject.com/en/dev/topics/logging for details
LOGGING = {
    'version': 1,

    'disable_existing_loggers': False,

    'formatters': {
        'verbose': {
            'format': ('%(asctime)s,%(levelname)s,%(filename)s,%(lineno)d,'
                       '[%(funcName)s(...)] : %(message)s')
        },
        'simple': {
            'format': '%(levelname)s %(message)s'
        },
    },

    'filters': {
         'require_debug_false': {
             '()': 'django.utils.log.RequireDebugFalse'
         }
     },

    'handlers': {
        'null': {
            'level':'DEBUG',
            'class':'django.utils.log.NullHandler',
        },

        'console':{
            'level':'DEBUG',
            'class':'logging.StreamHandler',
            'formatter': 'simple'
        },

        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        },

        'file': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'formatter': 'verbose',
            # Inputs to the ``logging.handlers.RotatingFileHandler`` class
            'filename': SPC['logfile_location'],
        },
    },

    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
        'scipycentral': {
            'handlers': ['file', 'mail_admins'],
            'level': 'DEBUG',
            'propagate': True,
        },
    }
}

# All about ``local_settings.py``
# ===============================

# Use ``local_settings.py`` to store variables that you don't want visible to
# revision control systems, or for settings that differ between production and
# development servers.
# The default variables that are expected are listed in the ``ImportError``
# part of the exception below.

try:
    execfile(os.path.join(BASE_DIR, 'local_settings.py'))
except IOError:
    # See https://docs.djangoproject.com/en/1.3/ref/settings for EMAIL settings
    EMAIL_HOST = ''
    EMAIL_HOST_USER = ''
    EMAIL_HOST_PASSWORD = ''
    # Visitors will receive email from this address e.g. "admin@example.org"
    SERVER_EMAIL = ''
    DEFAULT_FROM_EMAIL = SERVER_EMAIL

    # Where should JQuery be served from?
    JQUERY_URL = 'https://ajax.googleapis.com/ajax/libs/jquery/1.9.1/jquery.min.js'
    JQUERYUI_URL = 'https://ajax.googleapis.com/ajax/libs/jqueryui/1.10.2/jquery-ui.min.js'
    JQUERYUI_CSS = 'https://ajax.googleapis.com/ajax/libs/jqueryui/1.10.2/themes/smoothness/jquery-ui.css'

    # If you use Piwik, Google Analytics, etc: add the code snippet here that
    # will be placed as the last entry in the closing </head> tag.
    ANALYTICS_SNIPPET = ''

    # You can also overwrite keys from ``SPC`` in the ``local_settings.py`` file
