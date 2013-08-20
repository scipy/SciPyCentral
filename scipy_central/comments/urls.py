from django.conf.urls import url, include, patterns

urlpatterns = patterns('scipy_central.comments.views',
    # edit comment
    url(r'^edit/(\d+)/$', 'comments.edit_my_comment', name='spc-edit-my-comment'),
    # delete comment
    url(r'^user_delete/(\d+)/$', 'moderation.delete_my_comment', name='spc-delete-my-comment'),
    # preview comment 
    url(r'^preview/$', 'comments.preview', name='spc-comment-preview'),
    # post comment 
    url(r'^post/$', 'comments.post_comment', name='spc-post-comment'),
    # flag comments
    url(r'^flag/(\d+)/$', 'moderation.flag', name='spc-comments-flag'),
    # built-in comment urls
    url(r'', include('django.contrib.comments.urls')),
)
