from django.conf.urls.defaults import patterns, url
import feeds

urlpatterns = patterns('scipy_central.feeds.views', 

	url(r'^$', feeds.RssSiteFeed()),
)