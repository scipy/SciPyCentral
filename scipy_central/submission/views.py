from django.http import HttpResponse
from django.shortcuts import render_to_response, redirect
from django.template import RequestContext
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.exceptions import ObjectDoesNotExist
from django.template.defaultfilters import slugify
from django.utils import simplejson
from django import template
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, InvalidPage, EmptyPage

# Imports from this app and other SPC apps
from scipy_central.screenshot.forms import ScreenshotForm as ScreenshotForm
from scipy_central.screenshot.models import Screenshot as ScreenshotClass
from scipy_central.person.views import create_new_account_internal
from scipy_central.filestorage.models import FileSet
from scipy_central.tagging.models import Tag, parse_tags
from scipy_central.utils import send_email
from scipy_central.rest_comments.views import compile_rest_to_html
from scipy_central.pages.views import page_404_error
import models
import forms

# Python imports
from hashlib import md5
import logging
import os
import datetime
logger = logging.getLogger('scipycentral')
logger.debug('Initializing submission::views.py')

def get_form(request, form_class, field_order, bound=False):
    """
    Generic function. Used for all submission types. Specify the ``form_class``
    that's given in ``forms.py``. The ``field_order`` is a list of strings that
    indicates the linear order of the fields in the form. A ``bound`` form
    is a function of the object assigned to ``bound`` (see below). An unbound
    form is simply an empty form.
    """
    if bound:
        if isinstance(bound, models.Revision):
            tags = ','.join([str(tag) for tag in bound.tags.all()])
            fields =  {'item_url': bound.item_url,
                       'title': bound.title,
                       'description': bound.description,
                       'sub_tags': tags,
                       'snippet_code': bound.item_code,
                       'sub_type': 'snippet',
                       'sub_license': bound.sub_license_id,
                       'pk': bound.entry.id,
                       }
            if bound.entry.sub_type == 'link':
                fields['sub_type'] = 'link'
            elif  bound.entry.sub_type == 'code':
                fields['sub_type'] = 'snippet'

            form_output = form_class(fields)
        else:
            form_output = form_class(data=request.POST)
    else:
        form_output = form_class()

    # Rearrange the form order: screenshot and tags at the end
    form_output.fields.keyOrder = field_order

    if request.user.is_authenticated():
        # Email field not required for signed-in users
        form_output.fields.pop('email')

    return form_output


def create_or_edit_submission_revision(request, item, authenticated,
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
        tag_obj = Tag.objects.get_or_create(name=tag)[0]

        # Does the tag really exist or was it found because of the lack of
        # case sensitivity (e.g. "2D" vs "2d"
        if tag_obj.id is None:
            tag_obj = Tag.objects.get(slug=slugify(tag))

        tag_list.append(tag_obj)

    # Create a ``Revision`` instance. Must always have a ``title``, ``created_by``,
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
                            created_by=user,
                            sub_license=sub_license,
                            description=item.cleaned_data['description'],
                            description_html=description_html,
                            screenshot=sshot,
                            hash_id=hash_id,
                            item_url=item_url,
                            item_code=item_code,
                            )

    if commit:
        # Save the submission, then the revision. If we have a primary key
        # (case happens when user is editing a previous submission), then
        # do not save the submission (because the Submission object has fields
        # that will never change once it has been first created). Only set
        # the ``pk`` so that the new revision object is correct.
        if item.cleaned_data['pk']:
            sub.id = item.cleaned_data['pk']
        else:
            sub.save()

        rev.entry_id = sub.id
        rev.save()

        # Once you have the revision you can add tags through the intermediate
        # model instance (which tracks the user that added the tag and when).
        for tag in tag_list:
            tag_intermediate = models.TagCreation(created_by=user,
                                                  revision=rev,
                                                  tag=tag)
            tag_intermediate.save()
            logger.debug('User=%s added tag "%s" to rev.id=%d' % (
                                                user.username_slug,
                                                str(tag), rev.id))


        #
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
    snippet = get_form(request, forms.SnippetForm, bound=False,
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
    snippet = get_form(request, forms.SnippetForm, bound=True,
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
        sub, rev, tag_list, _ = create_or_edit_submission_revision(request,
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
    snippet = get_form(request, forms.SnippetForm, bound=True,
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
        sub, rev, _, msg = create_or_edit_submission_revision(request,
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
    try:
        the_snippet = models.Submission.objects.get(id=snippet_id)
    except ObjectDoesNotExist:
        return page_404_error(request)

    if not(the_snippet.is_displayed):
        return page_404_error(request)

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

    # TODO(KGD): put the typed text in bold, e.g. typed="bi" then return
    # proba<b>bi</b>lity
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
    return HttpResponse(simplejson.dumps(starts), mimetype='text/text')

#------------------------------------------------------------------------------
# Link submissions
def get_items_or_404(view_function):
    """
    Decorator for views that ensures the revision and submission requested
    actually exist. If not, throws a 404, else, it calls the view function
    with the required inputs.
    """
    def decorator(request, item_id, rev_num=None, slug=None):
        """Retrieves the ``Submission`` and ``Revision`` objects when given,
        at a minimum the submission's primary key (``item_id``). Since the
        submission can have more than 1 revision, we can get a specific
        revision, ``rev_num``, otherwise we will always get the latest
        revision. ``slug`` is ignored for now - just used to create good SEO
        URLs.
        """
        try:
            the_submission = models.Submission.objects.get(id=item_id)
        except ObjectDoesNotExist:
            return page_404_error(request)

        the_revision = the_submission.last_revision
        if rev_num: # can be None or '':
            all_revisions = the_submission.revisions.all()
            try:
                the_revision = all_revisions[int(rev_num)]
            except (ValueError, IndexError):
                return page_404_error(request)

        if not isinstance(the_revision, models.Revision):
            return page_404_error(request)

        return view_function(request, the_submission, the_revision)

    return decorator


def new_or_edit_link_submission(request, user_edit=False):
    """
    Users wants to submit a new link item, or continue editing a submission.
    """
    linkform = get_form(request, forms.LinkForm, field_order=['title',
                            'description', 'item_url', 'screenshot',
                            'sub_tags', 'email', 'sub_type', 'pk'],
                        bound=user_edit)
    return render_to_response('submission/new-link.html', {},
                              context_instance=RequestContext(request,
                                                    {'item': linkform}))

@get_items_or_404
def view_link(request, submission, revision):
    """
    Shows a snippet to web users. The ``slug`` is always ignored, but appears
    in the URLs mainly for the sake of search engines.
    The revision, if specified >= 0 will show the particular revision of the
    snippet, rather than than the latest revision (default).
    """
    permalink = settings.SPC['short_URL_root'] + str(submission.id)
    if revision.rev_id > 0:
        permalink += '/' + str(revision.rev_id)

    return render_to_response('submission/link.html', {},
                              context_instance=RequestContext(request,
                                       {'item': revision,
                                        'tag_list': revision.tags.all(),
                                        'permalink': permalink,
                                       }))

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
    new_submission = get_form(request, forms.LinkForm, bound=True,
                              field_order=['title', 'description', 'item_url',
                                           'screenshot', 'sub_tags', 'email',
                                           'sub_type', 'pk'])
    sshot = ScreenshotForm(request.POST, request.FILES)
    valid_fields.append(new_submission.is_valid())
    valid_fields.append(sshot.is_valid())

    if not(all(valid_fields)):
        return render_to_response('submission/new-link.html', {},
                              context_instance=RequestContext(request,
                                            {'item': new_submission}))

    # 1. Create user account, if required
    authenticated = True
    if not(request.user.is_authenticated()):
        user = create_new_account_internal(\
                                     new_submission.cleaned_data['email'])
        request.user = user
        authenticated = False

    # 2. Create the submission and revision or update an existing submission
    #    with a new revision
    sub, rev, tag_list, msg = create_or_edit_submission_revision(request,
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
                                                   'extra_html': extra_html}))

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

        send_email(request.user.email, ("Thank you for your submission to "
                                        "SciPy Central"), message=msg)

        return render_to_response('submission/thank-user.html', {},
                              context_instance=RequestContext(request,
                                    {'extra_message': extra_messages}))

#------------------------------------------------------------------------------
# Editing submissions: decorator order is important!
@login_required
@get_items_or_404
def edit_submission(request, submission, revision):

    # TODO: Check that user is authorized to edit the submission
    # (e.g. link.created_by==user)

    return new_or_edit_link_submission(request, user_edit=revision)


#------------------------------------------------------------------------------
# Show all items in a paginated table
def show_all_items(request):
    entries = paginated_queryset(request, models.Submission.objects.all())
    return render_to_response('submission/entries_list.html', {},
                              context_instance=RequestContext(request,
                                                {'entries': entries}))

def paginated_queryset(request, queryset):
    paginator = Paginator(queryset, 2)
    try:
        page = int(request.GET.get('page', '1'))
    except ValueError:
        page = 1
    try:
        return paginator.page(page)
    except (EmptyPage, InvalidPage):
        return paginator.page(paginator.num_pages)

