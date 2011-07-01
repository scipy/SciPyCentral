# Django settings for ``deploy`` project.
import django.conf.global_settings as DEFAULT_SETTINGS

# Add the parent to the path, to access files in ``../scipy_central/``
import os, sys
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, parent_dir)

DEBUG = True
TEMPLATE_DEBUG = DEBUG
ADMINS = (
    # ('Your Name', 'your_email@example.com'),
)

MANAGERS = ADMINS
DATABASES = {
    'default': {
        'ENGINE':   '', # Add 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
        'NAME':     '', # Or path to database file if using sqlite3.
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
if DEBUG:
    MEDIA_ROOT = os.path.dirname(__file__) + os.sep + 'media' + os.sep
else:
    # For production: you'll want to copy the <base>/media/* files to your
    # static location and modify this path to match your server.
    MEDIA_ROOT = '<your path here>'

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://media.lawrence.com/media/", "http://example.com/media/"
MEDIA_URL = '/media/'

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/home/media/media.lawrence.com/static/"
STATIC_ROOT = ''

# URL prefix for static files.
# Example: "http://media.lawrence.com/static/"
STATIC_URL = '/static/'

# URL prefix for admin static files -- CSS, JavaScript and images.
# Make sure to use a trailing slash.
# Examples: "http://foo.com/static/admin/", "/static/admin/".
ADMIN_MEDIA_PREFIX = '/static/admin/'

# Additional locations of static files
STATICFILES_DIRS = (
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

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    os.path.abspath(os.path.join(os.path.dirname(__file__), 'templates')),
)

# To get access to some global variables used in the templates
TEMPLATE_CONTEXT_PROCESSORS = DEFAULT_SETTINGS.TEMPLATE_CONTEXT_PROCESSORS + (
    'scipy_central.context_processors.global_template_variables',
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

    # 3rd party apps:
    'haystack',

    #  Local apps
    'scipy_central.filestorage',
    'scipy_central.pages',
    'scipy_central.person',
    'scipy_central.submission',
    'scipy_central.tagging',
    'scipy_central.screenshot',
)

# Authentication related:
AUTHENTICATION_BACKENDS = (
    'scipy_central.person.auth_backends.CustomUserModelBackend',
)
CUSTOM_USER_MODEL = 'person.UserProfile'

# Link the user is redirected to if not logged in and they try to perform
# a function that only logged in users can do
LOGIN_URL = '/user/sign-in/'

if DEBUG:
    import tempfile
    tempdir = tempfile.mkdtemp()
else:
    tempdir = ''

# These settings define and modify the behaviour of the entire website.
# SciPy Central = SPC.
SPC = {
    # Delete unconfirmed submission after this number of days
    'unvalidated_subs_deleted_after': 7,

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
    # where <storage> is the variable defined next, as should always end
    # with ``os.sep``
    #
    # Please ensure this directory is NOT somewhere under your web root,
    # to prevent direct access to the files (note that the setting as written
    # in here might be under the webroot).
    'storage_dir': MEDIA_ROOT + 'code' + os.sep,

    # Where should logfiles be written? If DEBUG != True, then you are
    # responsible that this location is valid and exists. Overwrite the
    # location in ``local_settings.py`` below.
    'logfile_location': tempdir + os.sep + 'logfile.log',

    # Comments are compiled (using Sphinx) in this location. Again, you are
    # required to sure this location exists for production servers.
    'comment_compile_dir': tempdir + os.sep + 'compile',

    # Default name of license file (e.g. 'LICENSE.TXT')
    'license_filename': 'LICENSE.TXT',

    # Short link URL root (must end with a trailing slash)
    'short_URL_root': 'http://scpyce.org/'
}

# All about ``local_settings.py``
# ===============================

# Use ``local_settings.py`` to store variables that you don't want visible to
# revision control systems, or for settings that differ between production and
# development servers.
# The default variables that are expected are listed in the ``ImportError``
# part of the exception below.
this_dir = __file__[0:__file__.find('settings.py')]
try:
    execfile(this_dir + os.sep + 'local_settings.py')
except ImportError:
    # See https://docs.djangoproject.com/en/1.3/ref/settings for EMAIL settings
    EMAIL_HOST = ''
    EMAIL_HOST_USER = ''
    EMAIL_HOST_PASSWORD = ''
    # Visitors will receive email from this address e.g. "admin@example.org"
    SERVER_EMAIL = ''
    DEFAULT_FROM_EMAIL = SERVER_EMAIL

    # Where should JQuery be served from?
    JQUERY_URL = 'https://ajax.googleapis.com/ajax/libs/jquery/1.6.1/jquery.min.js'
    JQUERYUI_URL = 'https://ajax.googleapis.com/ajax/libs/jqueryui/1.8.13/jquery-ui.min.js'
    JQUERYUI_CSS = 'https://ajax.googleapis.com/ajax/libs/jqueryui/1.8.13/themes/smoothness/jquery-ui.css'

    # If you use Piwik, Google Analytics, etc: add the code snippet here that
    # will be placed as the last entry in the closing </head> tag.
    ANALYTICS_SNIPPET = ''

    # You can also overwrite keys from ``SPC`` in the ``local_settings.py`` file

# Put all the search settings in a single file
execfile(this_dir + os.sep + 'search_settings.py')


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