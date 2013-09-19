from django import template
from django.core.exceptions import ObjectDoesNotExist
from django.db.models.loading import get_model
from django.contrib.auth.models import User

register = template.Library()

@register.filter
def vote(userObj, content_obj):
    """
    args:
        userObj - django.contrib.auth.models.User object
        revisionObj - scipy_central.submission.models.Revision
    return:
        scipy_central.submission.models.Thumbs.vote if object present (or)
        None

        return type: string

    Exceptions: closes silently!

    Example:
        {{request.user|vote:item}}
        {% ifequal request.user|vote:item "True" %}active{% endifequal %}

    """
    try:
        app_name = content_obj._meta.app_label
        module_name = content_obj._meta.module_name
        content_model = get_model(app_name, module_name)
    except (AttributeError, ObjectDoesNotExist):
        return str(None)

    if isinstance(userObj, User):
        try:
            thumb = content_obj.thumbs.get(person=userObj)
            return str(thumb.vote)
        except:
            pass
    return str(None)
