from django.conf.urls.defaults import patterns, url
import feeds

urlpatterns = patterns('scipy_central.feeds.views',

        # recent submission feed in rss
        url(r'^$', feeds.RssSiteFeed(), name='spc-rss-recent-submissions'),
        # submission feed in rss
        url(r'^(?P<item_id>\d+)/$', feeds.RssSubmissionFeed(), name='spc-rss-submission-feed'),
        # show tag feeds in rss
        url(r'^(?P<tag_slug>.+)/$', feeds.RssTagFeed(), name='spc-rss-tag-feed'),
        # recent submission feed in atom
        url(r'^atom/$', feeds.AtomSiteFeed(), name="spc-atom-recent-submissions"),
)
