from django.conf.urls.defaults import url, include, patterns
from haystack import urls
urlpatterns = patterns('scipy_central',

    # NOTE: internal name for front page (defined in scipy_central.pages.urls)
    #       is:  spc-main-page

    # Major pages in the site: front page, about page, etc
    url(r'', include('scipy_central.pages.urls')),

    # User authentication and profile viewing.
    url(r'^accounts/', include('scipy_central.person.urls'), ),

    # Submissions: new and existing, including previous revisions
    url(r'item/', include('scipy_central.submission.urls'), name='spc-items'),

    # reST comment converted to HTML
    url(r'rest/', include('scipy_central.rest_comments.urls')),

    # Searching
    url(r'^search', include('haystack.urls')),
    #(r'^search/advanced', TODO),


    # Django-registration: new accounts, password resets, etc
    # NOTE: the default backend is overriden ONLY for new account registration
    # in scipy_central.person.urls
    (r'^accounts/', include('registration.backends.default.urls')),

)
