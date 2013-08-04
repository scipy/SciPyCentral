from haystack import indexes
from models import Revision

# SearchIndex object for each revision in the database

class RevisionIndex(indexes.SearchIndex, indexes.Indexable):

    # The main field to search in: see template search/indexes/submission/revision_text.txt
    text = indexes.CharField(document=True, use_template=True)#model_attr='description')

    # Code submissions: all search the code
    item_code = indexes.CharField(model_attr='item_code', default='')

    # For link-type submissions: perhaps the link contains the search term
    item_url = indexes.CharField(model_attr='item_url', default='')

    # Include the tags as a search fields
    tags = indexes.CharField()

    def get_model(self):
        return Revision

    def index_queryset(self, **kwargs):
        # The ``Revision`` model has its own managers that does the right
        # thing in calling ``all()``.
        return self.get_model().objects.all()

    def prepare(self, object):
        """ See http://docs.haystacksearch.org/dev/searchindex_api.html
        """
        self.prepared_data = super(RevisionIndex, self).prepare(object)
        self.prepared_data['tags'] = ' '.join([tag.name for tag in object.tags.all()])

        return self.prepared_data

