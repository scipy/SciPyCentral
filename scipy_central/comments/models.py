from django.db import models
from django.contrib.comments.models import Comment
from django.contrib.contenttypes import generic

from django.utils.translation import ugettext_lazy as _
from django.conf import settings

from scipy_central.thumbs.models import Thumbs
from scipy_central.thumbs import scale

COMMENT_MAX_LENGTH = getattr(settings, 'COMMENT_MAX_LENGTH', 3000)

class SpcComment(Comment):
    """
    Custom model for comments
    `rest_comment` stores compiled ReST comments
    """
    rest_comment = models.TextField(_('rest_comment'),
        max_length=COMMENT_MAX_LENGTH,
        null = True)

    thumbs = generic.GenericRelation(Thumbs,
        content_type_field='content_type',
        object_id_field='object_pk')

    # aggregate reputation of `thumbs`
    reputation = models.IntegerField(default=0)

    def set_reputation(self):
        """
        Calculate total reputation for the object.
        Only needed when `scale` is changed
        """
        score = 0
        for aThumb in self.thumbs.all().filter(is_valid=True).exclude(vote=None):
            score += scale.COMMENT_VOTE['thumb']['up']
        return score

    def calculate_reputation(self, vote, prev_vote):
        """
        Please refer to `scipy_central.submission.models.Revision`
        `calculate_reputation` method doc string

        Arguments:
            `vote`: True or None
            (comments does not have down-voting. `False` is thus not taken)
            `prev_vote`: True or None
            (This argument is not really requied but helps to validate)
        Returns:
            updated reputation value (int)
        """
        rept = self.reputation
        if vote == True and prev_vote == None:
            rept += scale.COMMENT_VOTE['thumb']['up']
        elif vote == None and prev_vote == True:
            rept -= scale.COMMENT_VOTE['thumb']['up']
        return rept
