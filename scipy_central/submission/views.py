# All of Django's wonderful imports
from django.http import HttpResponse
from django.shortcuts import render_to_response, redirect
from django.template import RequestContext
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.template.defaultfilters import slugify
from django.template.loader import render_to_string
from django.utils import simplejson
from django import template
from django.contrib.auth.decorators import login_required
from django.contrib.sites.models import Site
from django.views.generic.list_detail import object_list
from django.utils.hashcompat import sha_constructor

# Imports from this app and other SPC apps
from scipy_central.screenshot.forms import ScreenshotForm as ScreenshotForm
from scipy_central.screenshot.models import Screenshot as ScreenshotClass
from scipy_central.person.views import create_new_account_internal
from scipy_central.filestorage.models import FileSet
from scipy_central.tagging.models import Tag, parse_tags
from scipy_central.utils import send_email, paginated_queryset, highlight_code
from scipy_central.rest_comments.views import compile_rest_to_html
from scipy_central.pages.views import page_404_error, not_implemented_yet
from scipy_central.pagehit.views import create_hit, get_pagehits
import models
import forms

# Python imports
from hashlib import md5
from collections import namedtuple
import random
import logging
import os
import re
import datetime
logger = logging.getLogger('scipycentral')
logger.debug('Initializing submission::views.py')


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
            # Use the Submissions manager's ``all()`` function
            the_submission = models.Submission.objects.all().filter(id=item_id)
        except ObjectDoesNotExist:
            return page_404_error(request)

        if len(the_submission) == 0:
            return page_404_error(request)

        the_submission = the_submission[0]
        the_revision = the_submission.last_revision
        if rev_num: # can be None or '':
            all_revisions = the_submission.revisions.all()
            try:
                the_revision = all_revisions[int(rev_num)]
            except (ValueError, IndexError):
                return page_404_error(request)

        # Don't return revisions that are not approved for display yet
        if not isinstance(the_revision, models.Revision) or\
                                              not(the_revision.is_displayed):
            return page_404_error(request)

        if slug is None or rev_num is None:
            return redirect('/'.join(['/item',
                                      item_id,
                                      str(the_revision.rev_id),
                                      the_submission.slug]),
                            permanent=True)

        return view_function(request, the_submission, the_revision)

    return decorator


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
    index = 1
    for field_name, field in form_output.fields.iteritems():
        field.widget.attrs['tabindex'] = str(index)
        index += 1

    if request.user.is_authenticated():
        # Email field not required for signed-in users
        form_output.fields.pop('email')

    return form_output


def create_or_edit_submission_revision(request, item, is_displayed,
                                             user, commit=False, ):
    """
    Creates a new ``Submission`` and ``Revision`` instance. Returns these in
    a tuple.
    """
    post = request.POST

    # NOTE: the ``user`` will always be a valid entry in our database. Code
    # posted by users that have not yet validated themselves is not displayed
    # until they do so.

    # A new submission
    sub = models.Submission.objects.create_without_commit(created_by=user,
                                    sub_type=item.cleaned_data['sub_type'])

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
        try:
            tag_obj = Tag.objects.get_or_create(name=tag)[0]
        except ValidationError:
            pass
        else:
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
    elif sub.sub_type == 'snippet':
        sub_license = item.cleaned_data['sub_license']
        item_url = None
        item_code = item.cleaned_data['snippet_code']

    # Convert the raw ReST description to HTML using Sphinx: could include
    # math, paragraphs, <tt>, bold, italics, bullets, hyperlinks, etc.
    #raw_rest =
    description_html = compile_rest_to_html(item.cleaned_data['description'])
    item_highlighted_code = highlight_code(item.cleaned_data.get(\
                                                           'snippet_code',''))
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
                            item_highlighted_code=item_highlighted_code,
                            is_displayed=is_displayed,
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
        if not is_displayed:
            rev.validation_hash = create_validation_code(rev)

        rev.save()

        if sub.sub_type == 'snippet':
            datenow = datetime.datetime.now()
            year, month = datenow.strftime('%Y'), datenow.strftime('%m')
            repo_path = settings.SPC['storage_dir'] + year + os.sep + month
            repo_path += os.sep + '%06d%s' % (rev.id, os.sep)
            sub.fileset = FileSet.objects.create(repo_path=repo_path)
            sub.save()

            fname = rev.slug.replace('-', '_') + '.py'

            commit_msg = ('SPC: auto add "%s" and license to the repo based '
                          'on the web submission by user "%d"') % (fname, user.id)
            sub.fileset.add_file_from_string(fname, request.POST['snippet_code'])

            license_file = settings.SPC['license_filename']
            license_text = get_license_text(rev)
            sub.fileset.add_file_from_string(license_file, license_text,
                                             commit_msg)


        # Once you have the revision you can add tags through the intermediate
        # model instance (which tracks the user that added the tag and when).
        for tag in tag_list:
            tag_intermediate = models.TagCreation(created_by=user,
                                                  revision=rev,
                                                  tag=tag)
            tag_intermediate.save()
            logger.debug('User "%s" added tag "%s" to rev.id=%d' % (
                                                user.profile.slug,
                                                str(tag), rev.id))


        # log the new submission and revision
        logger.info('New %s: %s [id=%d] and revision id=%d' % (
                                                sub.sub_type,
                                                item.cleaned_data['title'],
                                                sub.id,
                                                rev.id))

    return sub, rev, tag_list

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
# All submissions: have a form associated with them, as well as a number of
# fields that must appear in a certain order
Item = namedtuple('Item', 'form field_order')
SUBS = {'snippet': Item(forms.SnippetForm, field_order=['title',
                        'snippet_code', 'description', 'sub_license',
                        'sub_tags', 'email', 'sub_type', 'pk']),
        'package': Item(forms.PackageForm, field_order=['title',
                        'description', 'package_file', 'sub_license',
                        'sub_tags', 'email', 'sub_type', 'pk']),
        'link': Item(forms.LinkForm, field_order=['title', 'description',
                        'item_url', 'sub_tags', 'email',
                        'sub_type', 'pk']),
        }


def new_or_edit_submission(request, bound_form=False):
    """
    Users wants to submit a new link item, or continue editing a submission.
    """
    # User is going to edit their submission
    sub_type = None
    if isinstance(bound_form, models.Revision):
        new_item_or_edit = True
        sub_type = bound_form.entry.sub_type # for later on...

    # Cancel button, or a GET request
    elif request.method != 'POST' or request.POST.has_key('spc-cancel'):
        return redirect('spc-main-page')

    else:
        new_item_or_edit = False


    # Find which button was pressed on the front page submission form
    buttons = [key.rstrip('.x') for key in request.POST.keys()]

    if 'snippet' in buttons:
        itemtype = 'snippet'
        new_item_or_edit = True # we're coming from the front page
    elif 'package' in buttons:
        #itemtype = 'package'
        #new_item_or_edit = True # we're coming from the front page
        return not_implemented_yet(request, 48)
    elif 'link' in buttons:
        itemtype = 'link'
        new_item_or_edit = True # we're coming from the front page
    else:
        itemtype = request.POST.get('sub_type', sub_type)


    if request.POST.has_key('spc-edit'):
        new_item_or_edit = True
        bound_form = True

    if request.POST.has_key('spc-submit'):
        bound_form = True
        commit = True

    if request.POST.has_key('spc-preview'):
        bound_form = True
        commit = False

    theform = get_form(request, form_class=SUBS[itemtype].form,
                       field_order=SUBS[itemtype].field_order,
                       bound=bound_form)

    if new_item_or_edit:
        return render_to_response('submission/new-item.html', {},
                              context_instance=RequestContext(request,
                                                    {'item': theform}))



    # OK, having all that out of the way, lets process the user's submission

    # 0. Use the built-in forms checking to validate the fields.
    valid_fields = []
    #new_submission = get_form(request, bound=True,
    #                          form_class=SUBS[itemtype].form,
    #                          field_order=SUBS[itemtype].field_order)
    sshot = ScreenshotForm(request.POST, request.FILES)
    valid_fields.append(sshot.is_valid())
    valid_fields.append(theform.is_valid())


    if not(all(valid_fields)):
        return render_to_response('submission/new-item.html', {},
                              context_instance=RequestContext(request,
                                            {'item': theform}))

    # 1. Create user account, if required
    if request.user.is_authenticated():
        user = request.user
        authenticated = True
    else:
        user = create_new_account_internal(\
                                     theform.cleaned_data['email'])
        authenticated = False

    # 2. Create the submission and revision or update an existing submission
    #    with a new revision
    _, rev, tag_list = create_or_edit_submission_revision(request,
                                                    item=theform,
                                                    is_displayed=authenticated,
                                                    user=user,
                                                    commit=commit)

    # i.e. just previewing ...
    if not(commit):
        # 3. Create a Cancel/Edit/Submit form via a template to account for
        # hyperlinks and CSRF
        context = RequestContext(request)
        context['item'] = theform
        html = ('<div id="spc-preview-edit-submit" class="spc-form">'
                '<form action="{% url spc-new-submission %}" '
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
        return render_to_response('submission/item.html', {},
                                  context_instance=RequestContext(request,
                                                  {'item': rev,
                                                   'tag_list': tag_list,
                                                   'extra_html': extra_html}))

    else:
        # 4. Thank user and return with any extra messages, and send an email
        ctx_dict = {'user': user,
                    'item': rev,
                    'site': Site.objects.get_current()
                    }

        if authenticated:
            extra_messages = ('A confirmation email has been sent to you.')
            message = render_to_string('submission/email_user_thanks.txt',
                                   ctx_dict)
        else:
            extra_messages = ('You have been sent an email to '
                              '<i>confirm your submission</i> and to create '
                              'an account (if you do not have one '
                              'already). <p>Unconfirmed submissions '
                              'cannot be accepted, and <b>will be '
                              'deleted</b> after %d days. Please sign in '
                              'to avoid having to confirm your '
                              'valuable submissions in the future.') % \
                            settings.SPC['unvalidated_subs_deleted_after']

            if rev.validation_hash:
                message = render_to_string(\
                  'submission/email_validated_user_unvalidated_submission.txt',
                   ctx_dict)
            else:
                # TODO: register user, get validation link
                # TODO(KGD): add authentication to the message also
                message = render_to_string(\
                'submission/email_unvalidated_user_unvalidated_submission.txt',
                   ctx_dict)

        send_email((user.email,), ("Thank you for your contribution "
                                        "to SciPy Central"), message=message)

        return render_to_response('submission/thank-user.html', {},
                              context_instance=RequestContext(request,
                                    {'extra_message': extra_messages}))


def create_validation_code(revision):
    """
    From BSD licensed code, James Bennett
    https://bitbucket.org/ubernostrum/django-registration/src/58eef8330b0f/registration/models.py
    """
    salt = sha_constructor(str(random.random())).hexdigest()[:5]
    slug = revision.slug
    if isinstance(slug, unicode):
        slug = slug.encode('utf-8')
    return sha_constructor(salt+slug).hexdigest()

def validate_submission(request, code):
    """
    Validate a submission (via an emailed link to the user).

    From BSD licensed code, James Bennett
    https://bitbucket.org/ubernostrum/django-registration/src/58eef8330b0f/registration/models.py
    """
    SHA1_RE = re.compile('^[a-f0-9]{40}$')
    if SHA1_RE.search(code):
        try:
            rev = models.Revision.objects.get(validation_hash=code)
        except ObjectDoesNotExist:
            return page_404_error(request, ('That validation code was invalid'
                                            ' or used already.'))

        rev.is_displayed = True
        rev.validation_hash = None
        rev.save()
        return redirect(rev.get_absolute_url())
    else:
        return page_404_error(request, ('That validation code is invalid.'))

#------------------------------------------------------------------------------
# Viewing existing submissions:
@get_items_or_404
def view_link(request, submission, revision):
    """
    Shows a submitted item to web users. The ``slug`` is always ignored, but
    appears in the URLs for the sake of search engines. The revision, if
    specified >= 0 will show the particular revision of the item, rather than
    the latest revision (default).
    """
    create_hit(request, submission)
    permalink = settings.SPC['short_URL_root'] + str(submission.id) + '/' + \
                                                          str(revision.rev_id)

    return render_to_response('submission/item.html', {},
                              context_instance=RequestContext(request,
                                       {'item': revision,
                                        'tag_list': revision.tags.all(),
                                        'permalink': permalink,
                                       }))


#------------------------------------------------------------------------------
# Editing submissions: decorator order is important!
@login_required
@get_items_or_404
def edit_submission(request, submission, revision):

    # TODO: Check that user is authorized to edit the submission
    # (e.g. link.created_by==user)

    # if by POST, we are in the process of editing, so don't send the revision
    if request.POST:
        return new_or_edit_submission(request, bound_form=False)
    else:
        return new_or_edit_submission(request, bound_form=revision)


#------------------------------------------------------------------------------
def sort_items_by_page_views(all_items, item_module_name):
    # TODO(KGD): Cache this reordering of ``items`` for a period of time

    today = datetime.datetime.now()
    start_date = today - datetime.timedelta(days=settings.SPC['hit_horizon'])
    page_order = get_pagehits(item_module_name, start_date=start_date,
                                                               end_date=today)
    page_order.reverse()

    #``page_order`` is a list of tuples; the 2nd entry in each tuple is the
    # primary key, that must exist in ``items_pk``.
    all_items = list(all_items)
    items_pk = [item.pk for item in all_items]
    entry_order = []
    count_list = []
    for count, pk in page_order:
        try:
            idx = items_pk.index(pk)
        except ValueError:
            pass
        else:
            items_pk[idx] = None
            entry_order.append(all_items[idx])
            count_list.append(count)

    # Items that have never been viewed get added to the bottom:
    for idx, pk in enumerate(items_pk):
        if pk is not None:
            entry_order.append(all_items[idx])
            count_list.append(0)

    return entry_order, count_list


def show_items(request, tag=None, user=None):
    """ Shows all items in the database, sorted from most most page views to
    least page views.
    """
    if tag is None:
        all_subs = models.Submission.objects.all()
        page_title = 'All submissions'
    else:
        all_revs = models.Revision.objects.filter(tags__slug=slugify(tag))
        all_subs = set()
        page_title = 'All entries tagged: "%s"' % tag
        for rev in all_revs:
            all_subs.add(rev.entry)

    # This code isn't quite right: a user can create a revision: we should show
    # the particular revision which that user created, not necessarily the
    # latest revision of that submission.
    #if user is not None:
        #all_revisions = models.Revision.objects.filter(created_by__username_slug=user)
        #all_subs = set()
        #for rev in all_revisions:
            #all_subs.add(rev.entry)

    entry_order, count_list = sort_items_by_page_views(all_subs, 'submission')
    entries = paginated_queryset(request, entry_order)
    return render_to_response('submission/show-entries.html', {},
                              context_instance=RequestContext(request,
                                                {'entries': entries,
                                                 'count_list': count_list,
                                                 'page_title': page_title}))