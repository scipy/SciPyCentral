# django imports
import simplejson, logging, time
from django.conf import settings
from django.db import models
from django.shortcuts import get_object_or_404
from django.http import Http404, HttpResponse
from django.utils.html import escape
from django.contrib import comments
from django.contrib.comments import signals
from django.contrib.comments.views.comments import CommentPostBadRequest
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST
from django.core.exceptions import ObjectDoesNotExist, ValidationError

# scipy central imports
from scipy_central.comments.forms import SpcCommentEditForm
from scipy_central.rest_comments.views import compile_rest_to_html

# other imports
from sphinx.application import SphinxError

logger = logging.getLogger('scipycentral')
logger.debug('Initializing comments::comments.py')

@csrf_protect
@require_POST
def post_comment(request, using=None):
    """
    This method is written with reference to
    django.contrib.comments.views.comments.post_comment() to make compatible with Ajax calls
    """
    if not request.user.is_authenticated():
        return HttpResponse('Unauthorized', status=401)

    if request.is_ajax():
        
        # response JSON object
        response = {'success': False}

        # Fill out some initial data fields from an authenticated user, if present
        data = request.POST.copy()
        data["name"] = request.user.get_full_name() or request.user.username
        data["email"] = request.user.email

        # Look up the object we're trying to comment about
        ctype = data.get("content_type")
        object_pk = data.get("object_pk")
        if ctype is None or object_pk is None:
            return CommentPostBadRequest("Missing content_type or object_pk field.")
        try:
            model = models.get_model(*ctype.split(".", 1))
            target = model._default_manager.using(using).get(pk=object_pk)
        except TypeError:
            return CommentPostBadRequest(
                "Invalid content_type value: %r" % escape(ctype))
        except AttributeError:
            return CommentPostBadRequest(
                "The given content-type %r does not resolve to a valid model." % \
                    escape(ctype))
        except ObjectDoesNotExist:
            return CommentPostBadRequest(
                "No object matching content-type %r and object PK %r exists." % \
                    (escape(ctype), escape(object_pk)))
        except (ValueError, ValidationError), e:
            return CommentPostBadRequest(
                "Attempting go get content-type %r and object PK %r exists raised %s" % \
                    (escape(ctype), escape(object_pk), e.__class__.__name__))

        # Construct the comment form
        form = comments.get_form()(target, data=data)

        # Check security information
        if form.security_errors():
            return CommentPostBadRequest(
                "The comment form failed security verification: %s" % \
                    escape(str(form.security_errors())))

        if form.errors:
            return HttpResponse(simplejson.dumps(response), mimetype="application/json")

        # Otherwise create the comment
        comment = form.get_comment_object()
        comment.ip_address = request.META.get("REMOTE_ADDR", None)
        comment.user = request.user

        # Signal that the comment is about to be saved
        responses = signals.comment_will_be_posted.send(
            sender  = comment.__class__,
            comment = comment,
            request = request
        )

        for (receiver, response) in responses:
            if response == False:
                return CommentPostBadRequest(
                    "comment_will_be_posted receiver %r killed the comment" % receiver.__name__)

        # Save the comment and signal that it was saved
        comment.save()
        signals.comment_was_posted.send(
            sender  = comment.__class__,
            comment = comment,
            request = request
        )

        # get updated comments count on object
        comments_count = comments.get_model().objects.filter(
            content_type=comment.content_type,
            object_pk=object_pk
        ).exclude(is_removed=True).count()
        response['comments_count'] = comments_count
        
        response['success'] = True
        return HttpResponse(simplejson.dumps(response), mimetype="application/json")
    
    else:
        raise Http404

@csrf_protect
def edit_my_comment(request, comment_id):
    if not request.user.is_authenticated():
        return HttpResponse(status=401)

    if not (request.method == 'POST' and \
            request.is_ajax()):
        raise Http404

    response = {}
    post_data = request.POST.copy()
    ctype = post_data.get("content_type")
    object_pk = post_data.get("object_pk")

    if ctype is None or object_pk is None:
        raise Exception('Missing content_type or object_pk fields')

    try:
        model = models.get_model(*ctype.split(".", 1))
        target = model._default_manager.get(pk=object_pk)
    except TypeError:
        return CommentPostBadRequest(
            "Invalid content_type value: %r" % escape(ctype))
    except AttributeError:
        return CommentPostBadRequest(
            "The given content-type %r does not resolve to a valid model." % \
                escape(ctype))
    except ObjectDoesNotExist:
        return CommentPostBadRequest(
            "No object matching content-type %r and object PK %r exists." % \
                (escape(ctype), escape(object_pk)))
    except (ValueError, ValidationError), e:
        return CommentPostBadRequest(
            "Attempting go get content-type %r and object PK %r exists raised %s" % \
                (escape(ctype), escape(object_pk), e.__class__.__name__))


    form = SpcCommentEditForm(target, data=request.POST)
    if form.security_errors():
        return CommentPostBadRequest(
                "The comment edit form failed security verification: %s" % \
                    escape(str(form.security_errors())))


    form = form.cleaned_data

    comment = get_object_or_404(comments.get_model(), pk=comment_id, site__pk=settings.SITE_ID)
    if comment.user == request.user:
        comment.comment = form['edit_comment']
        comment.rest_comment = compile_rest_to_html(form['edit_comment'])
        comment.ip_address = request.META.get('REMOTE_ADDR', None)
        comment.save()

        response['comment'] = comment.comment
        response['rest_comment'] = comment.rest_comment
        response['success'] = True

    else:
        raise Exception('Invalid authorization: User not permitted to edit comment')
    

    return HttpResponse(simplejson.dumps(response), mimetype="application/json")

def preview(request):
    """
    The user has typed in a comment and wants to preview it in HTML.
    GET request needs `rest_comment` field
    """
    if not request.user.is_authenticated():
        return HttpResponse(status=401)
    
    if request.method != "GET" and not request.is_ajax():
        raise Http404

    data = {"success": False}
    try:
        rest_comment = request.GET["rest_comment"]
    except KeyError:
        raise Http404
    start_time = time.time()
    try:
        html_comment = compile_rest_to_html(rest_comment).replace("\n", "<br>")
        data["html_comment"] = html_comment
        data["success"] = True
    except SphinxError:
        data["success"] = False
        logger.warning("Unable to compile comment:: Sphinx compile error")
    end_time = time.time()
    if (end_time-start_time) > 3:
        logger.warning("Comment compile time exceeded 3 seconds; server load too high?")
    
    return HttpResponse(simplejson.dumps(data), mimetype="application/json")
