from django.conf.urls.defaults import patterns, url

urlpatterns = patterns('scipy_central.thumbs.views',

    # thumb post request
    url(r'^post/$', 'post_thumbs', name='spc-post-thumbs'),
)
