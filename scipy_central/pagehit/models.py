from django.db import models


class PageHitManager(models.Manager):
    def most_viewed(self, field):
        """ From BSD licensed code:
        http://github.com/coleifer/djangosnippets.org/blob/master/cab/models.py
        """
        return self.filter(item='submission')

            #annotatecore=models.Count(field))\
                                               #.order_by('-score', 'username')

class PageHit(models.Model):
    """ Records each hit (page view) of an item: whether the item is a link,
    code snippet or library, tag, person's profile, etc.

    The only requirement is that the item must have an integer primary key.
    """
    objects = PageHitManager()
    ua_string = models.CharField(max_length=255) # browser's user agent
    ip_address = models.IPAddressField()
    datetime = models.DateTimeField(auto_now=True)
    item = models.CharField(max_length=50)
    item_pk = models.IntegerField()

    def __unicode__(self):
        return '%s at %s' % (self.item, self.datetime)


    def most_viewed(self, field):
        """ Most viewed in terms of a certain item.
        """
        return PageHit.objects.filter(item=field)\
                            .annotate(score=models.Count('revision'))\
                            .order_by('-score', 'username')
