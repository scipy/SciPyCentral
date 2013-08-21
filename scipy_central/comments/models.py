from django.db import models
from django.contrib.comments.models import Comment

from django.utils.translation import ugettext_lazy as _
from django.conf import settings

COMMENT_MAX_LENGTH = getattr(settings, 'COMMENT_MAX_LENGTH', 3000)

class SpcComment(Comment):
    """
    Custom model for comments
    `rest_comment` stores compiled ReST comments
    """
    rest_comment = models.TextField(_('rest_comment'),
        max_length=COMMENT_MAX_LENGTH,
        null = True)
