from django.conf.urls.defaults import patterns, url

urlpatterns = patterns('scipy_central.pages.views',

    # Front page
    url(r'^$', 'front_page', name='spc-main-page'),

    # About page
    url(r'about', 'about_page', name='spc-about-page'),

    # About licences
    url(r'licenses', 'licence_page', name='spc-about-licenses'),

    # Help with markup
    url(r'markup-help', 'markup_help', name='spc-markup-help'),

    # Search views (go through our app to log search queries)
    url(r'search', 'search', name='haystack_search'),

)
