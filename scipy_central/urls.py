from django.conf.urls.defaults import url, include, patterns

urlpatterns = patterns('scipy_central',

    # Major pages in the site: front page, about page, etc
    url(r'', include('scipy_central.pages.urls')),

    #(r'^tag/(?P<tag>[a-zA-Z0-9- ]+)/$', 'community.views.view_tag'),
    #(r'^tag/(?P<slug>[a-zA-Z0-9- ]+)/assign/$', 'community.views.assign_tags'),

    # User authentication
    url(r'^user/', include('scipy_central.person.urls')),


    # Submissions: new and existing, including previous revisions
    url(r'item/', include('scipy_central.submission.urls'))


    #url(r'^comments/', include('django.contrib.comments.urls')),

)
