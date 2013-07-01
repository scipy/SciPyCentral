from django.conf.urls.defaults import url, patterns

urlpatterns = patterns('scipy_central.apps.screenshot.views',

    # Add a new screenshot
    url(r'^add/$', 'add_screenshot', name='spc-screenshot-add'),
)
