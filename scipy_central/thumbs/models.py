# django imports
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _
from django.db import models

class Thumbs(models.Model):
    """
    Class for handling thumbs up/thumbs down voting
    """

    # Who is voting? Null for anonymous users.
    person = models.ForeignKey(User)

    # Vote for object - Which object to vote?
    content_type = models.ForeignKey(ContentType,
        verbose_name=_('content type'),
        related_name="content_type_set_for_%(class)s"
    )
    object_pk = models.TextField(_('object ID'))
    content_object = generic.GenericForeignKey(
        ct_field="content_type", 
        fk_field="object_pk"
    )

    # When the vote was cast
    submit_date = models.DateField(auto_now=True)

    # IP_address: for abuse prevention
    ip_address = models.IPAddressField()

    # user_agent: web browser's user agent: for abuse prevention
    user_agent = models.CharField(max_length=255)

    # vote: ``True`` is thumbs up, ``False`` is thumbs down
    vote = models.NullBooleanField(default=None)

    # vote is valid?
    is_valid = models.BooleanField(default=True)

    class Meta:
        unique_together = ( ("person", "content_type", "object_pk"), )

    def __unicode__(self):
        return "%s: %s" % (self.person.username, self.vote)
