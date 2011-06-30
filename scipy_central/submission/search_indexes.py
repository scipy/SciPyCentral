from haystack import indexes, site
from models import Revision

class RevisionIndex(indexes.RealTimeSearchIndex):

    # Entries in common to all submissions:
    title = indexes.CharField(model_attr='title')
    text = indexes.CharField(document=True, model_attr='description')

    # Code submissions:
    item_code = indexes.CharField(model_attr='item_code', default='')

    # For link-type submissions
    item_url = indexes.CharField(model_attr='item_url', default='')

    # TODO: How to handle tags in search?
    #??? tags = indexes.MultiValueField()

    def get_model(self):
        return Revision

    def index_queryset(self):
        # The ``Revision`` model has its own managers that does the right
        # thing in calling ``all()``.
        return self.get_model().objects.all()#_for_search()

    #def prepare_tags(self, obj):
        ## Store a list of tag names for filtering
        #return [tag.name for tag in obj.tags.all()]

site.register(Revision, RevisionIndex)