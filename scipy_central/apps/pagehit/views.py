# Built-in imports
from datetime import date
from collections import defaultdict

# Imports from other SPC apps
from scipy_central.utils import get_IP_address

import models

static_items = {'spc-main-page': 1,
                'spc-about-page': 2,
                'spc-about-licenses': 3,
                'spc-markup-help': 4,
                'haystack_search': 5,
               }

def create_hit(request, item, extra_info=None):
    """
    Given a Django ``request`` object, create an entry in the DB for the hit.

    If the ``item`` is a string, then we assume it is a static item and use
    the dictionary above to look up its "primary key".
    """
    ip_address = get_IP_address(request)
    ua_string = request.META.get('HTTP_USER_AGENT', '')
    if extra_info is None:
        extra_info = request.META.get('HTTP_REFERER', None)
    try:
        page_hit = models.PageHit(ip_address=ip_address, ua_string=ua_string,
                                 item=item._meta.module_name, item_pk=item.pk,
                                 extra_info=extra_info)
    except AttributeError:
        page_hit = models.PageHit(ip_address=ip_address, ua_string=ua_string,
                                 item=item, item_pk=static_items.get(item, 0),
                                 extra_info=extra_info)

    page_hit.save()

# TODO(KGD): cache this result for NN hours
def get_pagehits(item, start_date=None, end_date=None, item_pk=None):
    """
    Returns a list of tuples of the form:  [(n_hits, Submission.pk), ....]
    This allows one to use the builtin ``list.sort()`` function where Python
    orders the list based on the first entry in the tuple.

    The list will be returned in the order of the ``Submission.pk``, but the
    first tuple entry is the number of hits, allowing for easy sorting
    using Python's ``sort`` method.

    However, if ``item_pk`` is provided, then it simply returns the total
    number of page views for that item, as an integer.
    """
    if start_date is None:
        start_date = date.min
    if end_date is None:
        end_date = date.max

    # extra_info=None to avoid counting download hits
    if item_pk is None:
        page_hits = models.PageHit.objects.filter(item=item).\
                                       filter(datetime__gte=start_date).\
                                       filter(datetime__lte=end_date).\
                                       filter(extra_info=None)
    else:
        page_hits = models.PageHit.objects.filter(item=item).\
                                       filter(datetime__gte=start_date).\
                                       filter(datetime__lte=end_date).\
                                       filter(item_pk=item_pk).\
                                       filter(extra_info=None)

        return len(page_hits)

    hits_by_pk = defaultdict(int)
    for hit in page_hits:
        hits_by_pk[hit.item_pk] += 1

    hit_counts = []
    for key, val in hits_by_pk.iteritems():
        hit_counts.append((val, key))

    return hit_counts
