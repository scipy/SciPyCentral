from django.conf.urls import url, include, patterns

urlpatterns = patterns('scipy_central.comments.views',
    # flag comments
    url(r'^flag/(\d+)/$', 'moderation.flag', name='spc-comments-flag'),
    # built-in comment urls
    url(r'', include('django.contrib.comments.urls')),
)
