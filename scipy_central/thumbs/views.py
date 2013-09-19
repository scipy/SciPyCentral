# python, django imports
import simplejson, datetime
from django.contrib import comments
from django.contrib.contenttypes.models import ContentType
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST
from django.shortcuts import Http404, get_object_or_404
from django.http import HttpResponse

# scipy central imports
from scipy_central.submission.models import Revision
from scipy_central import submission, utils
from scipy_central.thumbs.forms import ThumbsForm
from scipy_central.thumbs.models import Thumbs

@csrf_protect
@require_POST
def post_thumbs(request):
    # If user is authenticated and using ajax call
    if request.user.is_authenticated() and request.is_ajax():
        data = {'success': False, 'removed': False}
        form = ThumbsForm(request.POST)
        if form.is_valid():
            form = form.cleaned_data
            # if voting for (r) Revision object
            if form['thumb_for'] == 'r':
                thumb_obj = get_object_or_404(Revision, pk=form['object_pk'])
                ct_type = get_object_or_404(ContentType, 
                    app_label='submission', 
                    model='revision')
            # if voting for (c) SpcComment object
            elif form['thumb_for'] == 'c':
                thumb_obj = get_object_or_404(comments.get_model(), pk=form['object_pk'])
                ct_type = get_object_or_404(ContentType,
                    app_label='comments',
                    model='spccomment')
            else:
                raise Http404

            vote = None
            if form['thumb_as'] == 'up':
                vote = True
            elif form['thumb_as'] == 'down' and form['thumb_for'] != 'c':
                vote = False
            else:
                raise Http404
            
            ct_obj = ct_type.get_object_for_this_type(pk=form['object_pk'])
            if form['thumb_for'] == 'r':
                if ct_obj.created_by == request.user:
                    raise Http404
            elif form['thumb_for'] == 'c':
                if ct_obj.user == request.user:
                    raise Http404

            # check moderation settings
            if not ct_obj.enable_reputation:
                raise Http404
            
            ip_address = utils.get_IP_address(request)
            submit_date = datetime.datetime.now()
            user_agent = request.META['HTTP_USER_AGENT']
            
            # get or create Thumbs object
            thumb_obj, created = Thumbs.objects.get_or_create(
                person = request.user,
                content_type = ct_type,
                object_pk = form['object_pk'],
                defaults = {
                    'submit_date': submit_date,
                    'ip_address': ip_address,
                    'user_agent': user_agent,
                    'vote': vote,
                }
            )

            # if User vote already present, change it
            if not created:
                # is_vaid has to be explicitly made True
                # If `is_valid` might be made False from admin
                thumb_obj.is_valid = True
                if vote == thumb_obj.vote:
                    thumb_obj.vote = None
                    data['removed'] = True
                else:
                    thumb_obj.vote = vote
                     
                thumb_obj.ip_address = ip_address
                thumb_obj.submit_date = submit_date
                thumb_obj.save()

            ct_obj = ct_type.get_object_for_this_type(pk=form['object_pk'])
            data['votes'] = ct_obj.reputation
            data['success'] = True

        return HttpResponse(simplejson.dumps(data), mimetype="application/json")

    else:
        raise Http404
