from django.http import HttpResponse
from django.shortcuts import render_to_response, redirect
from django.template import RequestContext
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.exceptions import ObjectDoesNotExist
#from django.core.context_processors import csrf
from django.utils import simplejson
from django.template.loader import get_template
from django import template

# Imports from this app and other SPC apps
from scipy_central.screenshot.forms import ScreenshotForm as ScreenshotForm
from scipy_central.screenshot.models import Screenshot as ScreenshotClass
from scipy_central.person.views import create_new_account_internal
from scipy_central.filestorage.models import FileSet
from scipy_central.tagging.models import Tag, parse_tags
from scipy_central.utils import send_email
from scipy_central.rest_comments.views import compile_rest_to_html
import models
import forms

# Python imports
from hashlib import md5
import logging
import os
import datetime
logger = logging.getLogger('scipycentral')
logger.debug('Initializing submission::views.py')


def get_form(request, form_class, field_order, unbound=True):
    """
    Generic function. Used for all submission types. Specify the ``form_class``
    that's given in ``forms.py``. The ``field_order`` is a list of strings that
    indicates the linear order of the fields in the form. An ``unbound`` form
    is an empty form, while a bound form is a function of the information
    provided in the POST field of ``request``.
    """
    if unbound:
        form_output = form_class()
    else:
        form_output = form_class(data=request.POST)

    # Rearrange the form order: screenshot and tags at the end
    form_output.fields.keyOrder = field_order

    if request.user.is_authenticated():
        # Email field not required for signed-in users
        form_output.fields.pop('email')

    return form_output


def create_new_submission_and_revision(request, item, authenticated,
                                       commit=False):
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

    # A new submission
    #sub = models.Submission.objects.create(created_by=user,
    #                                sub_type=item.cleaned_data['sub_type'],
    #                                is_displayed=is_displayed)
    sub = models.Submission.objects.create_without_commit(created_by=user,
                                    sub_type=item.cleaned_data['sub_type'],
                                    is_displayed=is_displayed)

    # Process screenshot:
    if request.FILES.get('screenshot', ''):
        sshot_name = '_raw_' + sub.slug + '__' + \
                                         request.FILES['screenshot'].name
        sshot = ScreenshotClass()
        sshot.img_file_raw.save(sshot_name, \
                        ContentFile(request.FILES['screenshot'].read()))
        sshot.save()
    else:
        sshot = None

    # Process any tags
    tag_list = []
    for tag in parse_tags(item.cleaned_data['sub_tags']):
        tag_list.append(Tag.objects.get_or_create(name=tag)[0])

    # Create a ``Revision`` instance. Must always have a ``title``, ``author``,
    # and ``description`` fields; the rest are set according to the submission
    # type, ``sub.sub_type``
    hash_id = md5(post.get('snippet_code', '')).hexdigest()
    if sub.sub_type == 'link':
        sub_license = None
        item_url = item.cleaned_data['item_url']
        item_code = None
    else:
        sub_license = item.cleaned_data['sub_license']
        item_url = None
        item_code = item.cleaned_data['snippet_code']

    # Convert the raw ReST description to HTML using Sphinx: could include
    # math, paragraphs, <tt>, bold, italics, bullets, hyperlinks, etc.
    description_html = compile_rest_to_html(item.cleaned_data['description'])

    rev = models.Revision.objects.create_without_commit(
                            entry=sub,
                            title=item.cleaned_data['title'],
                            author=user,
                            sub_license=sub_license,
                            description=item.cleaned_data['description'],
                            description_html=description_html,
                            screenshot=sshot,
                            hash_id=hash_id,
                            item_url=item_url,
                            item_code=item_code,
                            )

    if commit:
        sub.save()
        rev.entry_id = sub.id
        rev.save()
        # Add the tags afterwards and save the revision
        for tag in tag_list:
            rev.tags.add(tag)

        #??? required??? rev.save()
        logger.info('New %s: %s [id=%d] and revision id=%d' % (
                                                sub.sub_type,
                                                item.cleaned_data['title'],
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

    return sub, rev, tag_list, message

#------------------------------------------------------------------------------
# Snippets
def new_snippet_submission(request):
    """
    Users wants to submit a new item via the web.
    """
    snippet = get_form(request, forms.SnippetForm,
                       field_order=['title', 'description', 'snippet_code',
                       'sub_license', 'screenshot', 'sub_tags',
                       'email', 'sub_type'])
    return render_to_response('submission/new-submission.html', {},
                              context_instance=RequestContext(request,
                                                        {'snippet': snippet}))


def preview_snippet_submission(request):
    """
    Users wants to preview a new snippet.
    """
    if request.method != 'POST':
        return redirect('spc-new-snippet-submission')

    # Use the built-in forms checking to validate the fields.
    valid_fields = []
    snippet = get_form(request, forms.SnippetForm, unbound=False,
                       field_order=['title', 'description', 'snippet_code',
                       'sub_license', 'screenshot', 'sub_tags',
                       'email', 'sub_type'])
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
        sub, rev, tag_list, _ = create_new_submission_and_revision(request,
                                                                snippet,
                                                                authenticated)

        # Create the 3-button form via a template to account for hyperlinks
        # and CSRF
        context = RequestContext(request)
        context['snippet'] = snippet
        html = ('<div id="spc-preview-edit-submit" class="spc-form">'
                '<form action="{% url spc-new-snippet-submit %}" '
                'method="POST" enctype="multipart/form-data">\n'
                '{% csrf_token %}\n'
                '{{snippet.as_hidden}}'
                '<input type="submit" name="spc-cancel" value="Cancel submission"'
                'id="spc-item-cancel"/>\n'
                '<input type="submit" name="spc-edit"   value="Continue editing"'
                'id="spc-item-edit" "/>\n'
                '<input type="submit" name="spc-submit" value="Submit entry"'
                'id="spc-item-submit" style="margin-left:3em;"/>\n'
                '</form></div>')
        resp = template.Template(html)
        extra_html = resp.render(template.Context(context))
        return render_to_response('submission/snippet.html', {},
                                  context_instance=RequestContext(request,
                                                  {'submission': sub,
                                                   'item': rev,
                                                   'tag_list': tag_list,
                                                   'extra_html': extra_html,
                                                   'wrapper_id': 'preview',
                                          'unvalidated_user': authenticated}))
    else:
        return render_to_response('submission/new-submission.html', {},
                              context_instance=RequestContext(request,
                                            {'snippet': snippet}))


def submit_snippet_submission(request):
    if request.method != 'POST':
        return redirect('spc-new-snippet-submission')

    extra_messages = []

    # Use the built-in forms checking to validate the fields.
    valid_fields = []
    snippet = get_form(request, forms.SnippetForm, unbound=False,
                       field_order=['title', 'description', 'snippet_code',
                       'sub_license', 'screenshot', 'sub_tags',
                       'email', 'sub_type'])
    sshot = ScreenshotForm(request.POST, request.FILES)
    valid_fields.append(snippet.is_valid())
    valid_fields.append(sshot.is_valid())

    if all(valid_fields):
        # 1. Create user account, if required
        authenticated = True
        if not(request.user.is_authenticated()):
            user = create_new_account_internal(snippet.cleaned_data['email'])
            request.user = user
            authenticated = False
            username = '**Not validated**'
        else:
            username = user.username

        # 2. Create the submission and revision and email the user
        sub, rev, _, msg = create_new_submission_and_revision(request,
                                                               snippet,
                                                               authenticated)

        # 3. Create entry on hard drive in a repo
        datenow = datetime.datetime.now()
        year, month = datenow.strftime('%Y'), datenow.strftime('%m')
        repo_path = settings.SPC['storage_dir'] + year + os.sep + month
        repo_path += os.sep + '%06d%s' % (rev.id, os.sep)
        sub.fileset = FileSet.objects.create(repo_path=repo_path)
        sub.is_preview = False
        sub.save()

        fname = rev.slug.replace('-', '_') + '.py'

        commit_msg = ('SPC: auto add "%s" and license to the repo based '
                      'on the web submission by user "%s"') % (fname, username)
        sub.fileset.add_file_from_string(fname, request.POST['snippet_code'])

        license_file = settings.SPC['license_filename']
        license_text = get_license_text(rev)
        sub.fileset.add_file_from_string(license_file, license_text,
                                         commit_msg)

        # 4. Thank user and return with any extra messages
        if authenticated:
            extra_messages = ('A confirmation email has been sent to you.')
        else:
            extra_messages = ('You have been sent an email to '
                                'confirm your submission and to create '
                                'an account (if you do not have one '
                                'already). <p>Unconfirmed submissions '
                                'cannot be accepted, and will be '
                                'deleted after %d days. Please sign-in '
                                'to avoid having to confirm your '
                                'valuable submissions in the future.') % \
                            settings.SPC['unvalidated_subs_deleted_after']

        return render_to_response('submission/thank-user.html', {},
                                  context_instance=RequestContext(request,
                                        {'extra_message': extra_messages}))
    else:
        return render_to_response('submission/new-submission.html', {},
                              context_instance=RequestContext(request,
                                            {'snippet': snippet}))

    send_email(user.email, "Thanks for your submission to SciPy Central",
               message=msg)


def view_snippet(request, snippet_id, slug=None, revision=None):
    """
    Shows a snippet to web users. The ``slug`` is always ignored, but appears
    in the URLs mainly for the sake of search engines.
    The revision, if specified >= 0 will show the particular revision of the
    snippet, rather than than the latest revision (default).
    """
    show_error = False
    try:
        the_snippet = models.Submission.objects.get(id=snippet_id)
    except ObjectDoesNotExist:
        show_error = True

    if show_error or not(the_snippet.is_displayed):
        # Since ``render_to_response`` doesn't yet support status codes, do
        # this manually
        t = get_template('404.html')
        html = t.render(RequestContext(request))
        return HttpResponse(html, status=404)

    the_revision = the_snippet.last_revision
    return render_to_response('submission/snippet.html', {},
                              context_instance=RequestContext(request,
                                                {'submission': the_snippet,
                                                 'item': the_revision,
                                                 'extra_html': ''}))

#------------------------------------------------------------------------------
# Licensing and tagging
def get_license_text(rev):
    """
    Generates and returns the license text for the given revision. Uses these
    revision and authorship information from previous revisions, if necessary,
    to create the license.
    """
    return '****\nGENERATE LICENSE TEXT STILL\n****'


def tag_autocomplete(request):
    """
    Filters through all available tags to find those starting with, or
    containing the string ``contains_str``.

    Parts from http://djangosnippets.org/snippets/233/
    """
    # TODO(KGD): cache this lookup for 30 minutes
    # Also, randomize the tag order to prevent only the those with lower
    # primary keys from being shown more frequently
    all_tags = [tag.name for tag in Tag.objects.all()]

    contains_str = request.REQUEST.get('term', '').lower()

    starts = []
    includes = []
    for item in all_tags:
        index = item.lower().find(contains_str)
        if index == 0:
            starts.append(item)
        elif index > 0:
            includes.append(item)

    # Return tags starting with ``contains_str`` at the top of the list,
    # followed by tags that only include ``contains_str``
    starts.extend(includes)
    return HttpResponse(simplejson.dumps(starts), mimetype='text/plain')

#------------------------------------------------------------------------------
# Link submissions
def new_or_edit_link_submission(request, user_edit=False):
    """
    Users wants to submit a new link item, or continue editing a submission.
    When editing a submission we have ``unbound=False``, because the form is
    bound to the ``request``.
    """
    linkform = get_form(request, forms.LinkForm, field_order=['title',
                            'description', 'item_url', 'screenshot',
                            'sub_tags', 'email', 'sub_type'],
                        unbound=not(user_edit))
    return render_to_response('submission/new-link.html', {},
                              context_instance=RequestContext(request,
                                                    {'item': linkform}))


def preview_or_submit_link_submission(request):
    if request.method != 'POST':
        return redirect('spc-new-link-submission')

    if request.POST.has_key('spc-cancel'):
        return redirect('spc-main-page')

    if request.POST.has_key('spc-edit'):
        return new_or_edit_link_submission(request, user_edit=True)

    if request.POST.has_key('spc-submit'):
        commit = True

    if request.POST.has_key('spc-preview'):
        commit = False

    # Use the built-in forms checking to validate the fields.
    valid_fields = []
    new_submission = get_form(request, forms.LinkForm, unbound=False,
                              field_order=['title', 'description', 'item_url',
                                           'screenshot', 'sub_tags', 'email',
                                           'sub_type'])
    sshot = ScreenshotForm(request.POST, request.FILES)
    valid_fields.append(new_submission.is_valid())
    valid_fields.append(sshot.is_valid())

    if not(all(valid_fields)):
        return render_to_response('submission/new-link.html', {},
                              context_instance=RequestContext(request,
                                            {'snippet': new_submission}))


    # 1. Create user account, if required
    authenticated = True
    if not(request.user.is_authenticated()):
        user = create_new_account_internal(\
                                     new_submission.cleaned_data['email'])
        request.user = user
        authenticated = False

    # 2. Create the submission and revision and email the user
    sub, rev, tag_list, msg = create_new_submission_and_revision(request,
                                                     new_submission,
                                                     authenticated,
                                                     commit=commit)

    # i.e. just previewing ...
    if not(commit):
        # 3. Create a Cancel/Edit/Submit form via a template to account for
        # hyperlinks and CSRF
        context = RequestContext(request)
        context['item'] = new_submission
        html = ('<div id="spc-preview-edit-submit" class="spc-form">'
                '<form action="{% url spc-new-link-submit %}" '
                'method="POST" enctype="multipart/form-data">\n'
                '{% csrf_token %}\n'
                '{{item.as_hidden}}'
                '<div id="spc-preview-edit-submit-button-group">'
                '<input type="submit" name="spc-cancel" value="Cancel"'
                'id="spc-item-cancel" />\n'
                '<input type="submit" name="spc-edit"   value="Resume editing"'
                'id="spc-item-edit" />\n'
                '<input type="submit" name="spc-submit" value="Finish submission"'
                'id="spc-item-submit"/>\n'
                '</div></form></div>')
        resp = template.Template(html)
        extra_html = resp.render(template.Context(context))
        return render_to_response('submission/link.html', {},
                                  context_instance=RequestContext(request,
                                                  {'item': rev,
                                                   'tag_list': tag_list,
                                                   'extra_html': extra_html,
                                                   'wrapper_id': 'preview'}))

    else:
        # 4. Thank user and return with any extra messages
        if authenticated:
            extra_messages = ('A confirmation email has been sent to you.')
        else:
            extra_messages = ('You have been sent an email to '
                              '<i>confirm your submission</i> and to create '
                              'an account (if you do not have one '
                              'already). <p>Unconfirmed submissions '
                              'cannot be accepted, and <b>will be '
                              'deleted</b> after %d days. Please sign-in '
                              'to avoid having to confirm your '
                              'valuable submissions in the future.') % \
                            settings.SPC['unvalidated_subs_deleted_after']

        send_email(user.email, "Thanks for your submission to SciPy Central",
                   message=msg)

        return render_to_response('submission/thank-user.html', {},
                              context_instance=RequestContext(request,
                                    {'extra_message': extra_messages}))




