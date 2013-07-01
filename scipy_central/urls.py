from django.conf.urls.defaults import patterns, include, url
from django.conf import settings

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),

    # NOTE: internal name for front page (defined in scipy_central.apps.pages.urls)
    #       is:  spc-main-page

    # Major pages in the site: front page, about page, search, etc
    url(r'', include('scipy_central.apps.pages.urls')),

    # User authentication and profile viewing.
    url(r'^user/', include('scipy_central.apps.person.urls'), ),

    # Submissions: new and existing, including previous revisions
    url(r'item/', include('scipy_central.apps.submission.urls'), name='spc-items'),

    # reST comment converted to HTML
    url(r'rest/', include('scipy_central.apps.rest_comments.urls')),

    # Django-registration: new accounts, password resets, etc
    # NOTE: the default backend is overriden ONLY for new account registration
    # in scipy_central.apps.person.urls
    (r'^user/', include('registration.backends.default.urls')),

    # Tagging
    (r'^tagging/', include('scipy_central.apps.tagging.urls')),

    # Images and screenshots
    (r'^image/', include('scipy_central.apps.screenshot.urls')),

    # feeds
    (r'^feeds/', include('scipy_central.apps.feeds.urls')),
)

handler404 = 'scipy_central.apps.pages.views.page_404_error'
handler500 = 'scipy_central.apps.pages.views.page_500_error'

if settings.DEBUG:
    # Small problem: cannot show 404 templates /media/....css file, because
    # 404 gets overridden by Django when in debug mode
    urlpatterns += patterns(
        '',
        (r'^static/(?P<path>.*)$',
         'django.views.static.serve', {'document_root': settings.STATIC_ROOT}),
    )

