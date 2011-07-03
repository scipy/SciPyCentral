from collections import defaultdict

from django.http import HttpResponse
from django.utils import simplejson
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response, redirect
from django.template import RequestContext
from scipy_central.person.forms import LoginForm, NewUserForm
from django.conf import settings
from django.db.utils import IntegrityError
from django.core.exceptions import ObjectDoesNotExist

# Imports from other SciPy Central apps
from scipy_central.pages.views import page_404_error
from scipy_central.submission.models import Revision
from scipy_central.utils import paginated_queryset

import models
import re
import random

def login_page(request):
    """
    Handles user authentication
    """
    if request.method == "POST":
        form = LoginForm(request.POST)
        next = request.POST.get('next', '')
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(username=username, password=password)
            if user is not None:
                if user.is_active:
                    login(request, user)
                    if not next:
                        next = user
                    return redirect(next)
                else:
                    form.errors['__all__'] = 'This account is inactive.'
            else:
                #if settings.DEBUG:
                    #try:
                        #user = models.CustomUser.objects.create(
                            #username= 'demo',
                            #email='demo@scipy-central.org')
                    #except IntegrityError:
                        #pass
                    #user = models.CustomUser.objects.get(username__exact='demo')
                    #user.set_password('demo')
                    #user.save()
                    #form.errors['__all__'] = 'Invalid login. Try using the username of <tt>demo</tt> and the password also <tt>demo</tt>'
                #else:
                form.errors['__all__'] = 'Invalid login.'
    else:
        if request.user.is_authenticated():
            return redirect(profile_page, request.user.username_slug)
        else:
            form = LoginForm()
            next = request.GET.get('next', '')

    return render_to_response('person/sign-in.html',
                              dict(form=form, user=request.user, next=next),
                              context_instance=RequestContext(request)
                              )


def profile_page(request, username_slug):
    """
    Shows the user's profile.
    """
    try:
        user = models.UserProfile.objects.get(username_slug=username_slug)
    except ObjectDoesNotExist:
        return page_404_error(request)

    # Items created by this user
    all_revs = Revision.objects.filter(created_by=user)
    all_subs = set()
    for rev in all_revs:
        all_subs.add(rev.entry)

    no_entries = 'This user has not submitted any entries to SciPy Central.'
    return render_to_response('person/profile.html', {},
                context_instance=RequestContext(request,
                            {'user': user,
                             'entries':paginated_queryset(request, all_subs),
                             'no_entries_message': no_entries, }))

@login_required
def logout_page(request):
    if request.method == "POST":
        if request.user.is_authenticated:
            logout(request)
    next = request.POST.get('next', login_page)
    return redirect(next)


def forgot_account_details(request):
    """
    User has forgotten their username or password.
    """
    return HttpResponse('STILL TO DO: reset password page')


def precheck_new_user(request):

    # TODO(KGD): change this to POST later on
    if request.method != 'POST':
        return HttpResponse(status=400)

    out = defaultdict(dict)
    def username_check(username):
    # 30 characters, letters, digits and underscores only
        if len(username) > 30:
            out['new_username']['toolong'] = 1
        elif len(username.strip()) == 0:
            out['new_username']['blank'] = 1
        elif models.UserProfile.objects.filter(username__exact=username):
            out['new_username']['taken'] = 1
        elif not(models.VALID_USERNAME.match(username)):
            out['new_username']['invalidchar'] = 1

    def password_check(password):
        # Anything that is non-blank
        if len(password.strip()) == 0:
            out['new_password']['blank'] = 1

    def email_check(email):
        # Valid email
        pass

    def openid_check(openid):
        # Can we connect?; can we get an email? If so, populate the email field
        # Hide the password field
        pass

    if request.POST['which'] == 'all':
        email_check(request.POST['new_email'])
        username_check(request.POST['new_username'])
        password_check(request.POST['new_password'])

        # Hand-off to another function to create the request
        if len(out) == 0:
            create_new_account(request)
            return HttpResponse('SHOW PROFILE EDITING PAGE')
        else:
            return HttpResponse(simplejson.dumps(out))

    #else:
        #func_name = request.POST['which'].replace('new_', '') + '_check'
        #locals()[func_name](request.POST['value'])
        #return HttpResponse(simplejson.dumps(out))

    #return HttpResponse(simplejson.dumps(out),
                                            #mimetype='application/javascript')

def create_new_account_internal(email):
    """
    Creates a *temporary* new user account so submissions can be made via
    email address. User's submission will be deleted if their account is not
    activated.

    We assume the ``email`` has already been validated as an email address.
    """
    # First check if that email address have been used; return ``False``
    previous = models.UserProfile.objects.filter(email=email)
    if len(previous) > 0:
        return previous[0]

    new_user = models.UserProfile.objects.create(username=email,
                                                 email=email)
    temp_password = ''.join([random.choice('abcdefghjkmnpqrstuvwxyz2345689')\
                             for i in range(50)])
    new_user.set_password(temp_password)
    new_user.save()
    return new_user


def create_new_account(request):
    if request.method == 'POST':
        # Create user account. All fields should have been validated by AJAX.
        # Redirect them to the ``profile_page``
        post = request.POST

        newuser_form = NewUserForm(request.POST)
        #newuser_form.is_valid()


        new_user = models.UserProfile.objects.create(
                            username = post['new_username'],
                            openid = post['new_openid'],
                            email = post['new_email'])
        new_user.set_password(post['new_password'])
        new_user.save()

        # TODO(KGD):
        # Create a cookie, so that the redirect loads the new user's profile
        # page so they can fill in their profile details.
        #authenticate(username=post['new_username'], password=post['new_password'])
        #login(request, new_user)


        # Redirect user to a page where they enter the validation code from their
        # email.

        #return redirect(new_user)# redirect(new_user) #'spc-user-profile', new_user.username_slug)

    else:
        form = LoginForm()
        next = request.GET.get('next', '')
        return render_to_response('person/create-user.html',
                                  dict(form=form, user=request.user, next=next),
                                  context_instance=RequestContext(request)
                                  )
