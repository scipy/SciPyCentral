#HAYSTACK_CONNECTIONS = {
    #'solr': {
        #'ENGINE': 'haystack.backends.solr_backend.SolrEngine',
        #'URL': 'http://localhost:9001/solr/example',

        #'INCLUDE_SPELLING': True,
    #},
    #'whoosh': {
        #'ENGINE': 'haystack.backends.whoosh_backend.WhooshEngine',
        #'PATH': os.path.join(os.path.dirname(__file__), 'whoosh_index'),
        #'INCLUDE_SPELLING': True,
    #},
    #'default': {
        ## For Simple:
        #'ENGINE': 'haystack.backends.simple_backend.SimpleEngine',
    #},
    #'xapian': { # Xapian (requires the third-party install):
        #'ENGINE': 'haystack.backends.xapian_backend.SearchBackend',
        #'PATH': os.path.join(os.path.dirname(__file__), 'xapian_index'),
        #'TIMEOUT': 60 * 5,
        #'INCLUDE_SPELLING': True,
    #}
#}

# See: http://docs.haystacksearch.org/dev/settings.html for details
# Many of the settings below are just their default values (to be explicit)

# These 3 settings will go away when using haystack 2.0.0
HAYSTACK_SEARCH_ENGINE = 'xapian'
HAYSTACK_XAPIAN_PATH = os.path.join(os.path.dirname(__file__), 'xapian_index')
HAYSTACK_SITECONF = 'search_sites'  # refers to <project_root>/search_sites.py
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