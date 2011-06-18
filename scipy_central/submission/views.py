from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.template import RequestContext, loader
from django.conf import settings
from django.core.files.base import ContentFile
from django.contrib.auth.decorators import login_required

# Imports from this app and other SPC apps
from scipy_central.screenshot.forms import ScreenshotForm as ScreenshotForm
from scipy_central.screenshot.models import Screenshot as ScreenshotClass
from scipy_central.person.views import create_new_account_internal
from scipy_central.filestorage.models import FileSet

from scipy_central.utils import send_email
import models
import forms

# Python imports
from hashlib import md5
import logging
import os
import datetime
logger = logging.getLogger('scipycentral')
logger.debug('Initializing submission::views.py')

def create_new_submission_and_revision(request, snippet, authenticated):
    """
    Creates a new ``Submission`` and ``Revision`` instance. Returns these in
    a tuple.
    """
    post = request.POST

    # NOTE: the ``request.user`` at this point will always already exist in
    # our database. Code posted by users that have not yet validated themselves
    # is not displayed until they do so.
    user = request.user
    is_displayed = False
    if authenticated:
        is_displayed = True

    # A new submission has only 2 fields of interest
    sub = models.Submission.objects.create(sub_type=\
                                           snippet.cleaned_data['sub_type'],
                                           created_by=user,
                                           is_displayed=is_displayed)

    # Process screenshot:
    if request.FILES.get('screenshot', ''):
        sshot_name = '_raw_' + sub.slug + '__' + \
                                         request.FILES['screenshot'].name
        sshot = ScreenshotClass()
        sshot.img_file_raw.save(sshot_name,\
                        ContentFile(request.FILES['screenshot'].read()))
        sshot.save()
    else:
        sshot = None

    # Create a ``Revision`` instance. Must always have a ``title``, ``author``,
    # and ``summary`` fields; the rest are set automatically, or blank.
    hash_id = md5(post.get('snippet')).hexdigest()
    rev = models.Revision.objects.create(
                            entry = sub,
                            title = snippet.cleaned_data['title'],
                            author = user,
                            sub_license = snippet.cleaned_data['sub_license'],
                            summary = snippet.cleaned_data['summary'],
                            description = None, #post.get('description', ''),
                            screenshot = sshot,
                            hash_id = hash_id,
                            item_url = None
                            )
    # TODO(KGD): add the tags
    rev.tags = []

    # Save the revision
    rev.save()
    logger.info('New snippet: %s [id=%d] and revision id=%d' % (
                                            snippet.cleaned_data['title'],
                                            sub.id,
                                            rev.id))

    # Email the user:
    if authenticated:
        # TODO: Get a link back to the submission and let user know that
        # they have submitted that code
        message = ''
    else:
        # TODO: Get a link to submission.
        # Also send the user a link saying they must create an account in
        # order for their submission to start being displayed on the website.
        message = ''

    send_email(user.email, "Thanks for your submission to SciPy Central",
               message=message)

    return rev

def new_snippet_submission(request):
    """
    Users wants to submit a new item via the web.
    """
    def get_snippet_form(request, unbound=True):
        if unbound:
            snippet = forms.SnippetForm()
        else:
            snippet = forms.SnippetForm(data=request.POST)

        # Rearrange the form order: screenshot and tags at the end
        snippet.fields.keyOrder = ['title', 'summary', 'snippet',
                                   'sub_license', 'screenshot', 'email',
                                   'sub_type']

        if request.user.is_authenticated():
            # Email field not required for signed-in users
            snippet.fields.pop('email')

        return snippet


    if request.method == 'POST':
        extra_messages = []

        # Use the built-in forms checking to validate the fields.
        valid_fields = []
        snippet = get_snippet_form(request, unbound=False)
        sshot = ScreenshotForm(request.POST, request.FILES)
        valid_fields.append(snippet.is_valid())
        valid_fields.append(sshot.is_valid())

        if all(valid_fields):
            # 1. Create user account, if required
            authenticated = True
            if not(request.user.is_authenticated()):
                user = create_new_account_internal(\
                                                snippet.cleaned_data['email'])
                request.user = user
                authenticated = False

            # 2. Create the submission and revision and email the user
            rev = create_new_submission_and_revision(request, snippet,
                                                     authenticated)

            # 3. Create entry on hard drive in a repo
            datenow = datetime.datetime.now()
            year, month = datenow.strftime('%Y'), datenow.strftime('%m')
            repo_path = settings.SPC['storage_dir'] + year + os.sep + month
            repo_path += os.sep + '%06d%s' % (rev.id, os.sep)
            rev.fileset = FileSet.objects.create(repo_path=repo_path)
            rev.save()

            fname = rev.slug.replace('-', '_') + '.py'
            commit_msg = ('SPC: auto add "%s" and license to the repo based '
                          'on the web submission by user "%s"') % (fname,
                                                        request.user.username)
            rev.fileset.add_file_from_string(fname, request.POST['snippet'])

            license_file = settings.SPC['license_filename']
            license_text = get_license_text(rev)
            rev.fileset.add_file_from_string(license_file, license_text,
                                             commit_msg)

            # 4. Thank user and return with any extra messages
            if authenticated:
                extra_messages = ('A confirmation email has been sent to you.')
            else:
                extra_messages  = ('An email has been sent to you to '
                                    'confirm your submission and to create '
                                    'an account (if you do not have one '
                                    'already). <p>Unconfirmed submissions '
                                    'cannot be accepted, and will be '
                                    'deleted after %d days. Please sign-in '
                                    'to avoid having to confirm your '
                                    'valuable submissions in the future.') % \
                                settings.SPC['unvalidated_subs_deleted_after']
            return render_to_response('submission/thank-user.html',
                                      {'extra_message': extra_messages})
        else:
            return render_to_response('submission/new-submission.html', {},
                                  context_instance=RequestContext(request,
                                                {'snippet': snippet}))


    elif request.method == 'GET':
        snippet = get_snippet_form(request)
        #sub_type = forms.CharField(max_length=10, initial='snippet',
        #                       widget=forms.HiddenInput())
        return render_to_response('submission/new-submission.html', {},
                                  context_instance=RequestContext(request,
                                                {'snippet': snippet}))



def get_license_text(rev):
    """
    Generates and returns the license text for the given revision. Uses these
    revision and authorship information from previous revisions, if necessary,
    to create the license.
    """
    return '****\nGENERATE LICENSE TEXT STILL\n****'
#def HTML_for_tagging(request):
    #""" Returns HTML that handles tagging """
    #response = '<h3>Step 3: Help categorize your submission</h3>'
    #response+= ('<p>Please provide subject area labels and categorization '
                #'tags to help other users when searching for your code.')

    #return  HttpResponse(response, status=200)