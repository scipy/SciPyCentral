from django.conf import settings

# Python imports
import logging
logger = logging.getLogger('scipycentral')
logger.debug('Initializing filestorage::views.py')

backend = settings.SPC['revisioning_backend']