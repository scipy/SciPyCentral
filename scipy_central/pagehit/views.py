# Built-in imports
from datetime import date
from collections import defaultdict

# Imports from other SPC apps
from scipy_central.utils import get_IP_address

import models


def create_hit(request, item):
    """
    Given a Django ``request`` object, create an entry in the DB for the hit.
    """
    page_hit = models.PageHit(ip_address=get_IP_address(request),
                            ua_string=request.META.get('HTTP_USER_AGENT', ''),
                           item=item._meta.module_name, item_pk=item.pk)
    page_hit.save()

# TODO(KGD): cache this result for NN hours
def get_pagehits(item, start_date=None, end_date=None):
    """
    Returns a list of tuples of the form:  [(n_hits, Submission.pk), ....]
    This allows one to use the builtin ``list.sort()`` function where Python
    orders the list based on the first entry in the tuple.

    The list will be returned in the order of the ``Submission.pk``, but the
    first tuple entry is the number of hits, allowing for easy sorting
    using Python's ``sort`` method.
    """
    if start_date is None:
        start_date = date.min
    if end_date is None:
        end_date = date.max

    page_hits = models.PageHit.objects.filter(item=item).\
                                       filter(datetime__gte=start_date).\
                                       filter(datetime__lte=end_date)

    hits_by_pk = defaultdict(int)
    for hit in page_hits:
        hits_by_pk[hit.item_pk] += 1

    hit_counts = []
    for key, val in hits_by_pk.iteritems():
        hit_counts.append((val, key))

    return hit_counts
