from django.conf.urls import url, include, patterns

urlpatterns = patterns('scipy_central.comments.views',

    # built-in comment urls
    url(r'', include('django.contrib.comments.urls')),
)
