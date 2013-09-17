from django import template
from django.core.exceptions import ObjectDoesNotExist
from django.db.models.loading import get_model
from django.contrib.auth.models import User
from django.contrib import comments
from scipy_central.submission.models import Revision
from scipy_central.thumbs.models import Thumbs
from scipy_central.thumbs.scale import REVISION_VOTE, COMMENT_VOTE


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

@register.filter
def get_reputation(user_obj):
    """
    NOTE: This filter is deprecated, not used anywhere now.
    Instead `reputation` is stored in field than calculated
    everytime.
    
    args: 
        `django.contrib.auth.models.User` object
    returns: 
        total user's reputation
    Example:
        `{{user_obj|get_reputation}}

    Description:
        Reputation is calculated based on the scale
        `scipy_central.thumbs.scale`

        All user created Revision, SpcComment objects votes 
        are taken and calculated dynamically!
        For calculation of reputation, we are not using `reputation`
        field in `scipy_central.person.models.UserProfile`.
        This helps us to dynamically scale the reputation value. For instance
        if we change magnitude in scale.py (as mentioned above), the 
        whole reputation gets automatically scaled
    """
    score = 0
    revs = Revision.objects.filter(
        is_displayed=True,
        created_by=user_obj)
    all_comments = comments.get_model().objects.filter(
        user=user_obj,
        is_public=True,
        is_removed=False
    )

    for obj in revs:
        all_votes = obj.allvotes_count()
        up_votes = obj.upvotes_count()
        down_votes = all_votes - up_votes
        score += (REVISION_VOTE["user"]["up"] * up_votes) - \
            (REVISION_VOTE["user"]["down"] * down_votes)
    
    for obj in all_comments:
        all_votes = obj.thumbs.filter(is_valid=True, vote=True).count()
        score += COMMENT_VOTE["user"]["up"] * all_votes

    return score

@register.assignment_tag
def my_votes(user_object, count=20):
    """
    Returns list of recent user votes
    """
    if isinstance(user_object, User):
        thumbs_list = Thumbs.objects.filter(
            person=user_object,
            is_valid=True,
        ).exclude(vote=None)
        return thumbs_list.order_by('-submit_date')[:count]
    else:
        raise template.TemplateSyntaxError("Invalid argument")
