from scipy_central.submission.models import TagCreation
import datetime
from collections import defaultdict

def get_tag_uses(start_date=None, end_date=None):
    """
    Returns a list of tuples of the form:  [(n_uses, Tag.pk), ....]
    This allows one to use the builtin ``list.sort()`` function where Python
    orders the list based on the first entry in the tuple.

    The list will be returned in the order of the ``Tag.pk``, but the
    first tuple entry is the number of uses of that tag, allowing for easy
    sorting using Python's ``sort`` method.
    """
    if start_date is None:
        start_date = datetime.date.min
    if end_date is None:
        end_date = datetime.date.max

    tags_created = TagCreation.objects.all().\
                                       filter(date_created__gte=start_date).\
                                       filter(date_created__lte=end_date)

    uses_by_pk = defaultdict(int)
    for use in tags_created:
        uses_by_pk[use.tag.pk] += 1

    hit_counts = []
    for key, val in uses_by_pk.iteritems():
        hit_counts.append((val, key))

    return hit_counts