from .base import *
from .search import *

DEBUG = True
TEMPLATE_DEBUG = DEBUG
ADMINS = (
    # ('Your Name', 'your_email@example.com'),
)

ALLOWED_HOSTS = ["127.0.0.1"]

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

# Make this unique, and don't share it with anybody.
SECRET_KEY = '3h%1b@kab#&f4o!!%8&_(-p@6mqm&(04vc_%*y$h+c$6j-s2rg'

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
