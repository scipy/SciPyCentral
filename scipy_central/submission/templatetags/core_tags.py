# BSD-licensed code used here:
# https://github.com/coleifer/djangosnippets.org/blob/master/cab/templatetags/core_tags.py
from django.db.models.loading import get_model
from django.db.models.query import QuerySet
from django.db.models.fields import DateTimeField, DateField
from django import template

from scipy_central.pagehit.views import get_pagehits
from scipy_central.submission.models import Revision, Submission

register = template.Library()

@register.filter
def top_authors(field, num=5):
    """ Get the top authors from the Revision model """
    manager = Revision._default_manager

    # Only return query set instances where the score exceeds 0
    # and the user is validated
    candidates = manager.top_authors().filter(score__gt=0)[:num*2]
    return [user for user in candidates if user.profile.is_validated][:num]

@register.filter
def most_viewed(field, num=5):
    """ Get the most viewed items from the Submission model """
    top_items = get_pagehits(field)
    top_items.sort()
    out = []
    for score, pk in reversed(top_items):
        out.append(Submission.objects.get(id=pk))
        out[-1].score = score
    return out

@register.filter
def latest(model_or_obj, num=5):
    # load up the model if we were given a string
    if isinstance(model_or_obj, basestring):
        model_or_obj = get_model(*model_or_obj.split('.'))

    # figure out the manager to query
    if isinstance(model_or_obj, QuerySet):
        manager = model_or_obj
        model_or_obj = model_or_obj.model
    else:
        manager = model_or_obj._default_manager

    # get a field to order by, defaulting to the primary key
    field_name = model_or_obj._meta.pk.name
    for field in model_or_obj._meta.fields:
        if isinstance(field, (DateTimeField, DateField)):
            field_name = field.name
            break
    return manager.all().order_by('-%s' % field_name)[:num]

@register.filter
def call_manager(model_or_obj, method):
    # load up the model if we were given a string
    if isinstance(model_or_obj, basestring):
        model_or_obj = get_model(*model_or_obj.split('.'))

    # figure out the manager to query
    if isinstance(model_or_obj, QuerySet):
        manager = model_or_obj
        model_or_obj = model_or_obj.model
    else:
        manager = model_or_obj._default_manager

    return getattr(manager, method)()
