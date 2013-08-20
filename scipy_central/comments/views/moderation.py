import simplejson
from django.conf import settings
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404
from django.contrib import comments
from django.contrib.comments.views.moderation import perform_flag
from django.views.decorators.csrf import csrf_protect

@csrf_protect
def flag(request, comment_id):
    """
    The view overrides the built-in view django.contrib.comments.moderation.flag()
    Reasons to override:
        1) Not compatible with Ajax calls
        
    @login_required is not used as it redirects to login-page and Ajax calls
    cannot be completed as expected.
        1) Error handling cannot be done using response attributes
    """
    if not request.user.is_authenticated():
        return HttpResponse('Unauthorized', status=401)

    if request.method == "POST" and \
        request.is_ajax():
        comment = get_object_or_404(comments.get_model(), pk=comment_id, site__pk=settings.SITE_ID)
        perform_flag(request, comment)
        data = {"success": True}
        data = simplejson.dumps(data)
        return HttpResponse(data, mimetype="application/json")
    else:
        raise Http404
