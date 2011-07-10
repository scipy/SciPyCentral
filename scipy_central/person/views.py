from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response, redirect
from django.template import RequestContext
from django.core.exceptions import ObjectDoesNotExist

# Imports from other SciPy Central apps
from scipy_central.pages.views import page_404_error, not_implemented_yet
from scipy_central.submission.models import Revision, Submission
from scipy_central.utils import paginated_queryset

import models
import random
import logging

logger = logging.getLogger('scipycentral')
logger.debug('Initializing person::views.py')

def user_logged_in(user, **kwargs):
    """
    Triggered when the user signs in.
    """
    logger.debug('User logged in: %s' % user.username)

@login_required
def profile_page_edit(request, slug):
    """
    User wants to edit his/her profile page.
    """
    # First verify that request.user is the same as slug
    return not_implemented_yet(request, 43)


@login_required
def sign_in_landing(request):
    """ Redirect the user to their actual profile page """
    return redirect(profile_page, request.user.profile.slug)


def profile_page(request, slug):
    """
    Shows the user's profile.
    """
    if slug is None:
        the_user = request.user
    else:
        try:
            the_user = models.User.objects.get(profile__slug=slug)
        except ObjectDoesNotExist:
            return page_404_error(request)

    # Don't show the profile for inactive (unvalidated) users
    if not(the_user.is_active):
        return page_404_error(request)


    # Items created by this user. Use the ``all()`` function first, to prevent
    # unvalidated submissions from showing
    all_revs = Revision.objects.all().filter(created_by=the_user)
    all_subs = set()
    for rev in all_revs:
        all_subs.add(rev.entry)

    if the_user == request.user:
        no_entries = 'You have not submitted any entries to SciPy Central.'
    else:
        no_entries = 'This user has not submitted any entries to SciPy Central.'

    return render_to_response('person/profile.html', {},
                context_instance=RequestContext(request,
                            {'theuser': the_user,
                             'entries':paginated_queryset(request, all_subs),
                             'no_entries_message': no_entries, }))


def create_new_account_internal(email):
    """
    Creates a *temporary* new user account so submissions can be made via
    email address. User's submission will be deleted if their account is not
    activated.

    We assume the ``email`` has already been validated as an email address.
    """
    # First check if that email address have been used; return ``False``
    previous = models.User.objects.filter(email=email)
    if len(previous) > 0:
        return previous[0]

    username = 'Unvalidated User ' + email.split('@')[0]
    new_user = models.User.objects.create(username=username, email=email)
    temp_password = ''.join([random.choice('abcdefghjkmnpqrstuvwxyz2345689')\
                             for i in range(50)])
    new_user.set_password(temp_password)
    new_user.save()
    return new_user


def create_new_account( user=None, **kwargs):
    """
    Complete creating the new user account: i.e. a new ``User`` object.
    """
    if 'instance' in kwargs and kwargs.get('created', False):
        new_user = kwargs.get('instance', user)

        # Create a UserProfile object in the DB
        new_user_profile = models.UserProfile.objects.create(user=new_user)
        new_user_profile.save()


def account_activation(user, **kwargs):
    """ User's account has been successfully activated.

    Make all their previous submissions visible.
    """
    user_profile = models.UserProfile.objects.get(user=user)
    user_profile.is_validated = True
    user_profile.save()

    user_revisions = Revision.objects.filter(created_by=user)
    for rev in user_revisions:
        rev.is_displayed = True
        rev.validation_hash = None
        rev.save()
