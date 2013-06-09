from django.contrib.syndication.views import Feed
from django.utils.feedgenerator import Atom1Feed
from scipy_central.submission.models import Revision

class RssSiteFeed(Feed):
    title = "Recent Submissions - Scipy Central"
    link = "/item/show/all-revisions/"
    description = "Most recent 30 submissions from Scipy Central"
    description_template = "feeds/item_description.html"

    def items(self):
        return Revision.objects.filter(is_displayed=True).order_by('-date_created')[:30]

    def item_title(self, item):
        return item.title

    def item_author_name(self, item):
        return item.created_by.username

    def item_pubdate(self, item):
        return item.date_created

    def item_categories(self, item):
        return tuple(eachTag.name for eachTag in item.tags.all())

class AtomSiteFeed(RssSiteFeed):
    feed_type = Atom1Feed
    subtitle = RssSiteFeed.description
