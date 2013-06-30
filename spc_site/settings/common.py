import os

import django.conf.global_settings as DEFAULT_SETTINGS

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))

DATA_DIR = os.path.join(BASE_DIR, os.pardir, 'data')

ROOT_URLCONF = 'spc_site.urls'

WSGI_APPLICATION = 'spc_site.wsgi.application'

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.admin',
    'django.contrib.admindocs',
    'django.contrib.humanize',

    'haystack',
    'registration',
    "widget_tweaks",

    'scipy_central.filestorage',
    'scipy_central.pages',
    'scipy_central.person',
    'scipy_central.submission',
    'scipy_central.tagging',
    'scipy_central.screenshot',
    'scipy_central.pagehit',
    'scipy_central.feeds',

    'south',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
)

AUTH_PROFILE_MODULE = 'person.UserProfile'

MEDIA_ROOT = os.path.join(DATA_DIR, 'media')

STATIC_ROOT = os.path.join(DATA_DIR, 'static')

STATICFILES_DIRS = (
    os.path.join(BASE_DIR, 'static'),
)

STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
)

TEMPLATE_DIRS = (
    os.path.abspath(os.path.join(BASE_DIR, 'templates')),
)

TEMPLATE_CONTEXT_PROCESSORS = DEFAULT_SETTINGS.TEMPLATE_CONTEXT_PROCESSORS + (
    'scipy_central.context_processors.global_template_variables',
    'django.core.context_processors.request',
)

TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
)

ACCOUNT_ACTIVATION_DAYS = 7

REGISTRATION_OPEN = True

CSRF_FAILURE_VIEW = 'scipy_central.pages.views.csrf_failure'

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

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://media.lawrence.com/media/", "http://example.com/media/"
MEDIA_URL = '/media/'

# URL prefix for static files served from ``data/static``.
# Make sure to use a trailing slash.
STATIC_URL = '/static/'

# URL prefix for admin static files -- CSS, JavaScript and images.
# Make sure to use a trailing slash.
# Examples: "http://foo.com/static/admin/", "/static/admin/".
ADMIN_MEDIA_PREFIX = '/static/admin/'

# Link the user is redirected to if not logged in and they try to perform
# a function that only logged in users can do
LOGIN_URL = '/user/login/'

# django-registration required setting
ACCOUNT_ACTIVATION_DAYS = 7

REGISTRATION_OPEN = True    # permit users to create new accounts

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
    'comment_compile_dir': os.path.join(DATA_DIR, 'cache', 'compile'),

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
