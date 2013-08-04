SEARCH_ENGINE = None

try:
	import xapian
	SEARCH_ENGINE = {
	    'default': {
	        'ENGINE': 'xapian_backend.XapianEngine',
	        'PATH': os.path.join(DATA_DIR, 'xapian_index'),
	        'INCLUDE_SPELLING': True,
	        'BATCH_SIZE': 100,
	    },
	}

except ImportError:
	import whoosh
	SEARCH_ENGINE = {
	    'default': {
	        'ENGINE': 'haystack.backends.whoosh_backend.WhooshEngine',
	        'PATH': os.path.join(DATA_DIR, 'whoosh_index'),
	        'STORAGE': 'file',
	        'POST_LIMIT': 128 * 1024 * 1024,
	        'INCLUDE_SPELLING': True,
	        'BATCH_SIZE': 100,
	    },
	}

HAYSTACK_CONNECTIONS = SEARCH_ENGINE
HAYSTACK_DEFAULT_OPERATOR = 'AND'
HAYSTACK_SEARCH_RESULTS_PER_PAGE = SPC['entries_per_page']
HAYSTACK_ITERATOR_LOAD_PER_QUERY = 10
HAYSTACK_LIMIT_TO_REGISTERED_MODELS = True
HAYSTACK_SILENTLY_FAIL = True
HAYSTACK_ID_FIELD = 'id'
HAYSTACK_DJANGO_CT_FIELD = 'django_CT'
HAYSTACK_DJANGO_ID_FIELD = 'django_id'
