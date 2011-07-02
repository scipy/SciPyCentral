from django.db import models
from scipy_central.submission.models import Submission

class PageHit(models.Model):
    """ Records each hit (page view) of a submission: whether it is a link,
    code snippet or library.
    """
    ua_string = models.CharField(max_length=500) # browser's user agent
    ip_address = models.IPAddressField()
    datetime = models.DateTimeField(auto_now=True)
    item = models.ForeignKey(Submission)

    def __unicode__(self):
        return '%s at %s' % (self.item, self.datetime)
