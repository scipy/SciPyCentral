from django.conf.urls.defaults import url, include, patterns
urlpatterns = patterns('scipy_central',

    # NOTE: internal name for front page (defined in scipy_central.pages.urls)
    #       is:  spc-main-page

    # Major pages in the site: front page, about page, search, etc
    url(r'', include('scipy_central.pages.urls')),

    # User registration, authentication and profile viewing.
    url(r'^user/', include('scipy_central.person.urls'), ),

    # Submissions: new and existing, including previous revisions
    url(r'item/', include('scipy_central.submission.urls'), name='spc-items'),

    # reST comment converted to HTML
    url(r'rest/', include('scipy_central.rest_comments.urls')),

    # Tagging
    (r'^tagging/', include('scipy_central.tagging.urls')),

    # Images and screenshots
    (r'^image/', include('scipy_central.screenshot.urls')),

    # feeds
    (r'^feeds/', include('scipy_central.feeds.urls')),
)
from django.conf import settings
settings.LOGIN_REDIRECT_URL = '/user/profile/'
