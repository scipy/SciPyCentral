# See: http://docs.haystacksearch.org/dev/settings.html for details
# Many of the settings below are just their default values (to be explicit)

HAYSTACK_SEARCH_ENGINE = None

if HAYSTACK_SEARCH_ENGINE is None:
    try:
        import xapian
        HAYSTACK_SEARCH_ENGINE = 'xapian'
        HAYSTACK_XAPIAN_PATH = os.path.join(DATA_DIR, 'xapian_index')
    except ImportError:
        pass

if HAYSTACK_SEARCH_ENGINE is None:
    try:
        import whoosh
        HAYSTACK_SEARCH_ENGINE = 'whoosh'
        HAYSTACK_WHOOSH_PATH = os.path.join(DATA_DIR, 'whoosh_index')
    except ImportError:
        pass

if HAYSTACK_SEARCH_ENGINE is None:
    raise RuntimeError("Neither xapian nor whoosh is installed")

HAYSTACK_SITECONF = 'scipy_central.search_sites'
HAYSTACK_DEFAULT_OPERATOR = 'AND'
HAYSTACK_INCLUDE_SPELLING = True
HAYSTACK_SEARCH_RESULTS_PER_PAGE = SPC['entries_per_page']
HAYSTACK_BATCH_SIZE = 100
HAYSTACK_ITERATOR_LOAD_PER_QUERY = 10
HAYSTACK_LIMIT_TO_REGISTERED_MODELS = True
HAYSTACK_SILENTLY_FAIL = True
HAYSTACK_ID_FIELD = 'id'
HAYSTACK_DJANGO_CT_FIELD = 'django_CT'
HAYSTACK_DJANGO_ID_FIELD = 'django_id'
