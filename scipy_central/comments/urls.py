from django.conf.urls import url, include, patterns

urlpatterns = patterns('scipy_central.comments.views',
	# preview comment 
	url(r'^preview/$', 'comments.preview', name='spc-comment-preview'),
	# post comment 
	url(r'^post/$', 'comments.post_comment', name='spc-post-comment'),
    # flag comments
    url(r'^flag/(\d+)/$', 'moderation.flag', name='spc-comments-flag'),
    # built-in comment urls
    url(r'', include('django.contrib.comments.urls')),
)
