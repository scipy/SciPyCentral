from django.conf.urls.defaults import url, include, patterns

urlpatterns = patterns('scipy_central',

    # NOTE: internal name for front page (defined in scipy_central.pages.urls)
    #       is:  spc-main-page

    # Major pages in the site: front page, about page, etc
    url(r'', include('scipy_central.pages.urls')),

    #(r'^tag/(?P<tag>[a-zA-Z0-9- ]+)/$', 'community.views.view_tag'),
    #(r'^tag/(?P<slug>[a-zA-Z0-9- ]+)/assign/$', 'community.views.assign_tags'),

    # User authentication
    url(r'^user/', include('scipy_central.person.urls'), name='spc-user'),


    # Submissions: new and existing, including previous revisions
    url(r'item/', include('scipy_central.submission.urls'), name='spc-items'),

    # reST comment converted to HTML
    url(r'rest/', include('scipy_central.rest_comments.urls')),

    # Searching
    (r'^search/', include('haystack.urls')),

    # Django-registration user accounts
    (r'^accounts/', include('registration.backends.default.urls')),

)
