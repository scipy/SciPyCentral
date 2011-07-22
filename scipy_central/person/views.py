from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response, redirect
from django.template import RequestContext
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings
from django.template.loader import render_to_string


# Imports from other SciPy Central apps
from scipy_central.pages.views import page_404_error
from scipy_central.submission.models import Revision
from scipy_central.rest_comments.views import compile_rest_to_html
from scipy_central.utils import paginated_queryset, send_email
from scipy_central.tagging.views import get_and_create_tags


import models
import forms

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
    if request.user.profile.slug != slug:
        return page_404_error(request, ('You are not authorized to edit that '
                                        'profile. Only that user may edit it.'))


    if request.POST:
        form = forms.ProfileEditForm(request.POST)
        if form.is_valid():
            # Update profile information
            user = request.user

            previous_email = ''
            if form.cleaned_data['email'] != user.email:
                previous_email = user.email
                user.email = form.cleaned_data['email']
                user.save()

            user.profile.affiliation = form.cleaned_data['affiliation']
            user.profile.country = form.cleaned_data['country']
            user.profile.bio = form.cleaned_data['bio']
            user.profile.bio_html = compile_rest_to_html(form.cleaned_data['bio'])
            user.profile.uri = form.cleaned_data['uri']

            user.profile.save()

            tag_list = get_and_create_tags(form.cleaned_data['interests'])

            # First delete all the user's previous interests, so we can update
            # them with the new ones
            for interest in models.InterestCreation.objects.filter(user=user):
                #.profile.interests.all():
                interest.delete()

            # Add user's interests through the intermediate
            # model instance
            for tag in tag_list:
                tag_intermediate = models.InterestCreation(user=user.profile,
                                                           tag=tag)
                tag_intermediate.save()
                logger.debug('User "%s" added interest "%s" to their profile'%\
                             (user.profile.slug, str(tag)))

            # Resave the user profile to capture their interests in the search
            # results.
            user.profile.save()

            if previous_email:
                ctx_dict = {'new_email': user.email,
                            'admin_email': settings.DEFAULT_FROM_EMAIL,
                            'username': user.username}
                message = render_to_string(\
                              'person/email_about_changed_email_address.txt',
                              ctx_dict)
                send_email((previous_email,), ("SciPy Central: change of "
                                        "email address"), message=message)


            return redirect(profile_page, user.profile.slug)

    else:
        user = request.user
        interests = ','.join(list(set([str(intr) for intr in user.profile.interests.all()])))
        fields =  {'uri': user.profile.uri,
                   'email': user.email,
                   'bio': user.profile.bio,
                   'interests': interests,
                   'country': user.profile.country,
                   'affiliation': user.profile.affiliation,
                   'pk': user.id,
                   }
        form = forms.ProfileEditForm(fields)

    return render_to_response('submission/new-item.html', {},
                          context_instance=RequestContext(request,
                                {'item': form,
                                 'buttontext': 'Update your profile',
                                 'pagetitle': 'Update your profile',
                                }))


#return not_implemented_yet(request, 43)


@login_required
def sign_in_landing(request):
    """ Redirect the user to their actual profile page """
    return redirect(profile_page, request.user.profile.slug)


def profile_page(request, slug=None, user_id=None):
    """
    Shows the user's profile.
    """
    try:
        if user_id:
            the_user = models.User.objects.get(id=user_id)
            return redirect(profile_page, the_user.profile.slug)
        elif slug is None:
            the_user = request.user
        else:
            the_user = models.User.objects.get(profile__slug=slug)
    except ObjectDoesNotExist:
        return page_404_error(request, 'No profile for that user.')

    # Don't show the profile for inactive (unvalidated) users
    if not(the_user.is_active):
        return page_404_error(request, "That user's profile isn't available.")


    # Items created by this user. Use the ``all()`` function first, to prevent
    # unvalidated submissions from showing
    all_revs = Revision.objects.all().filter(created_by=the_user)\
                                                    .order_by('-date_created')

    if the_user == request.user:
        no_entries = 'You have not submitted any entries to SciPy Central.'
    else:
        no_entries = 'This user has not submitted any entries to SciPy Central.'

    permalink = settings.SPC['short_URL_root'] + 'user/' + str(the_user.id) + '/'

    return render_to_response('person/profile.html', {},
                context_instance=RequestContext(request,
                            {'theuser': the_user,
                             'permalink': permalink,
                             'entries':paginated_queryset(request, all_revs),
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
    new_user.is_active = False
    new_user.save()
    return new_user


def create_new_account(user=None, **kwargs):
    """
    Complete creating the new user account: i.e. a new ``User`` object.

    This is a signal that is caught when the ``registration`` module creates a
    new user.
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

