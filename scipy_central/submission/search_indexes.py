from haystack import indexes, site
from models import Revision

# SearchIndex object for each revision in the database

class RevisionIndex(indexes.RealTimeSearchIndex):

    # The main field to search in: see template search/indexes/submission/revision_text.txt
    text = indexes.CharField(document=True, use_template=True)#model_attr='description')

    # Code submissions: all search the code
    item_code = indexes.CharField(model_attr='item_code', default='')

    # For link-type submissions: perhaps the link contains the search term
    item_url = indexes.CharField(model_attr='item_url', default='')

    # TODO: How to handle tags in search?
    #??? tags = indexes.MultiValueField()

    def get_model(self):
        return Revision

    def index_queryset(self):
        # The ``Revision`` model has its own managers that does the right
        # thing in calling ``all()``.
        return self.get_model().objects.all()#_for_search()

    def prepare(self, object):
        """ See http://docs.haystacksearch.org/dev/searchindex_api.html
        """
        self.prepared_data = super(RevisionIndex, self).prepare(object)
        #self.prepared_data['tags'] = [tag.name for tag in object.tags.all()]

        return self.prepared_data

    #def prepare_tags(self, obj):
        ## Store a list of tag names for filtering
        #return [tag.name for tag in obj.tags.all()]

site.register(Revision, RevisionIndex)