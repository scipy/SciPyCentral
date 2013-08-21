from django.contrib.comments.moderation import CommentModerator, moderator
from scipy_central.submission.models import Revision

class RevisionModerator(CommentModerator):
    """
    Comments moderation settings for
    `scipy_central.submission.models.Revision` model
    """
    enable_field = 'enable_comments'

moderator.register(Revision, RevisionModerator)
