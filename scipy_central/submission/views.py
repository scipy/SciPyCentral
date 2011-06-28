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
    sub = models.Submission.objects.create(created_by=user,
                                    sub_type=snippet.cleaned_data['sub_type'],
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
    for tag in parse_tags(snippet.cleaned_data['sub_tags']):
        tag_list.append(Tag.objects.get_or_create(name=tag)[0])

    # Create a ``Revision`` instance. Must always have a ``title``, ``author``,
    # and ``description`` fields; the rest are set automatically, or blank.
    hash_id = md5(post.get('snippet')).hexdigest()
    rev = models.Revision.objects.create(
                            entry=sub,
                            title=snippet.cleaned_data['title'],
                            author=user,
                            sub_license=snippet.cleaned_data['sub_license'],
                            description=snippet.cleaned_data['description'],
                            screenshot=sshot,
                            hash_id=hash_id,
                            item_url=None,
                            item_code=snippet.cleaned_data['snippet'],
                            )

    # Add the tags afterwards and save the revision
    for tag in tag_list:
        rev.tags.add(tag)

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

    return sub, rev, message


def new_snippet_submission(request):
    """
    Users wants to submit a new item via the web.
    """
    snippet = get_form(request, forms.SnippetForm,
                       field_order=['title', 'description', 'snippet',
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
                       field_order=['title', 'description', 'snippet',
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
        sub, rev, _ = create_new_submission_and_revision(request,
                                                         snippet,
                                                         authenticated)

        extra_html = """
        <form action="/item/new-snippet-preview"
  method="POST" class="spc-ul-form" enctype="multipart/form-data">

          <input type="submit" name="spc-cancel" value="Cancel"
          id="spc-item-cancel" />
          <input type="submit" name="spc-edit"   value="Edit"
          id="spc-item-edit" />
          <input type="submit" name="spc-submit" value="Submit entry"
          id="spc-item-submit" />
        </div>
        """
        # Create the 3-button form via a template to account for hyperlinks
        # and CSRF
        context = RequestContext(request)
        context['snippet'] = snippet
        html = ('<div id="spc-preview-edit-submit" class="spc-form">'
                '<form action="{% url spc-new-snippet-submit %}" '
                'method="POST" enctype="multipart/form-data">\n'
                '{% csrf_token %}\n'
                '{{snippet.as_hidden}}'
                '<input type="submit" name="spc-cancel" value="Cancel"'
                'id="spc-item-cancel" />\n'
                '<input type="submit" name="spc-edit"   value="Edit"'
                'id="spc-item-edit" />\n'
                '<input type="submit" name="spc-submit" value="Submit entry"'
                'id="spc-item-submit" />\n'
                '</form></div>')
        resp = template.Template(html)
        extra_html = resp.render(template.Context(context))
        return render_to_response('submission/snippet.html', {},
                                  context_instance=RequestContext(request,
                                                  {'submission': sub,
                                                   'item': rev,
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
                       field_order=['title', 'description', 'snippet',
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
            username = '**Not validated**'
        else:
            username = user.username

        # 2. Create the submission and revision and email the user
        sub, rev, message = create_new_submission_and_revision(request,
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
        sub.fileset.add_file_from_string(fname, request.POST['snippet'])

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
               message=message)


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


def get_license_text(rev):
    """
    Generates and returns the license text for the given revision. Uses these
    revision and authorship information from previous revisions, if necessary,
    to create the license.
    """
    return '****\nGENERATE LICENSE TEXT STILL\n****'

#autocomplete = cache_page(autocomplete, 60 * 60)


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


def new_link_submission(request):
    """
    Users wants to submit a new link item.
    """
    linkform = get_form(request, forms.LinkForm, field_order=['title',
                            'description', 'link', 'screenshot', 'sub_tags',
                            'email', 'sub_type'])
    return render_to_response('submission/new-link.html', {},
                              context_instance=RequestContext(request,
                                                    {'linkform': linkform}))

    #user = create_new_account_internal('mik2@smith.com')

    #sub = models.Submission.objects.create(created_by=user,
                                    #sub_type='link',
                                    #is_displayed=False)

    #rev = models.Revision.objects.create(
                            #entry=sub,
                            #title='Visvis library for data visualization',
                            #author=user,
                            #sub_license=None,
                            #description='Visvis is a pure Python library for visualization of 1D to 4D data in an object oriented way combining the power of OpenGL with the usability of Python. A MATLAB-like interface in the form of a set of functions allows easy creation of objects.',
                            #screenshot=None,
                            #hash_id=None,
                            #item_url='http://code.google.com/p/visvis/',
                            #item_code=None,
                            #)
    #return HttpResponse('STILL TO DO')


def preview_link_submission(request):
    return HttpResponse('STILL COMING')