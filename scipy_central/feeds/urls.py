from django.conf.urls.defaults import patterns, url
import feeds

urlpatterns = patterns('scipy_central.feeds.views',

        url(r'^$', feeds.RssSiteFeed(), name='spc-rss-feed-page'),
        url(r'^atom/$', feeds.AtomSiteFeed(), name="spc-atom-feed-page"),
)
