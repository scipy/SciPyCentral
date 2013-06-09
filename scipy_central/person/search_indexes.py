from haystack import indexes, site
from models import UserProfile

# SearchIndex object for each revision in the database

class UserProfileIndex(indexes.RealTimeSearchIndex):

    # The main field to search in: see template search/indexes/person/userprofile_text.txt
    text = indexes.CharField(document=True, use_template=True)

    # Include the tags as a search fields
    interests = indexes.CharField()

    def get_model(self):
        return UserProfile

    def index_queryset(self):
        # The ``Revision`` model has its own managers that does the right
        # thing in calling ``all()``.
        return self.get_model().objects.filter(is_validated=True)

    def prepare(self, object):
        """ See http://docs.haystacksearch.org/dev/searchindex_api.html
        """
        self.prepared_data = super(UserProfileIndex, self).prepare(object)
        #self.prepared_data['interests'] = ' '.join([intr.name for intr in object.interests.all()])

        return self.prepared_data

site.register(UserProfile, UserProfileIndex)
