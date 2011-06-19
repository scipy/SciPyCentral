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
    # If ``username_slug`` does not exist, then simply redirect them to list of users.
    return render_to_response('person/profile.html',
                              dict(user=request.user),
                              context_instance=RequestContext(request)
                              )

def logout_page(request):
    if request.method == "POST":
        if request.user.is_authenticated:
            logout(request)
    next = request.POST.get('next', login_page)
    return redirect(next)

@login_required
def reset_password(request):
    # TODO(KGD)
    pass

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
        openid_check(request.POST['new_openid'])
        email_check(request.POST['new_email'])
        username_check(request.POST['new_username'])
        if len(request.POST['new_openid']) == 0:
            password_check(request.POST['new_password'])

        # Hand-off to another function to create the request
        if len(out) == 0:
            return create_new_account(request)
        else:
            assert(False) # Do validation in AJAX"

            #return HttpResponse(simplejson.dumps(out))

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

    new_user = models.UserProfile.objects.create(username = email,
                                                 email = email)
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
        return render_to_response('person/sign-in.html',
                                  dict(form=form, user=request.user, next=next),
                                  context_instance=RequestContext(request)
                                  )
