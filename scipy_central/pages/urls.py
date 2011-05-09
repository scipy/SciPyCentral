from django.conf.urls.defaults import patterns, url

urlpatterns = patterns('scipy_central.pages.views',

    # Front page
    url(r'^$', 'front_page', name='scipycentral-main-page'),

    # About page
    url(r'about', 'about_page', name='scipycentral-about-page'),

    # About licences
    url(r'licenses', 'licence_page', name='scipycentral-about-licenses'),
)
