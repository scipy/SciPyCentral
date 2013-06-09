# django imports
from django.template.defaultfilters import slugify
from django.shortcuts import get_object_or_404
from django.contrib.syndication.views import Feed
from django.utils.feedgenerator import Atom1Feed

# scipycentral imports
from scipy_central.submission.models import Revision
from scipy_central.tagging.models import Tag

class RssSiteFeed(Feed):
    title = "Recent Submissions - Scipy Central"
    link = "/item/show/all-revisions/"
    feed_url = '/feeds/'
    description = "Most recent 30 submissions from Scipy Central"
    description_template = "feeds/item_description.html"
    feed_copyright = 'Please visit http://scipy-central.org/licenses link of SciPy Central Website'

    def items(self):
        return Revision.objects.filter(is_displayed=True).order_by('-date_created')[:30]

    def item_title(self, item):
        return item.title

    def item_author_name(self, item):
        return item.created_by.username

    def item_author_link(self, item):
        return '/user/profile/%s/' %item.created_by.username

    def item_pubdate(self, item):
        return item.date_created

    def item_categories(self, item):
        return tuple(eachTag.name for eachTag in item.tags.all())

    item_copyright = feed_copyright

class AtomSiteFeed(RssSiteFeed):
    feed_type = Atom1Feed
    subtitle = RssSiteFeed.description

class RssTagFeed(RssSiteFeed):
    def get_object(self, request, tag_slug):
        return get_object_or_404(Tag, slug=slugify(tag_slug))

    def title(self, obj):
        return 'Recent 30 %s Submissions - SciPy Central' % obj.slug

    def link(self, obj):
        return '/item/tag/%s/' % obj.slug

    def feed_url(self, obj):
        return '/feeds/%s' % obj.slug

    def description(self, obj):
        return obj.description

    def categories(self, obj):
        return tuple(obj.slug)

    def items(self, obj):
        return Revision.objects.all().filter(tags=obj, is_displayed=True).order_by('-date_created')[:30]
