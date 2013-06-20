# All of Django's wonderful imports
from django.shortcuts import render_to_response, redirect, HttpResponse
from django.template import RequestContext
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.template.defaultfilters import slugify
from django.template.loader import render_to_string
from django import template
from django.contrib.auth.decorators import login_required
from django.contrib.sites.models import Site
from django.utils.hashcompat import sha_constructor
from django.core.files.uploadedfile import UploadedFile
from django.utils.encoding import force_unicode, smart_str

# Imports from this app and other SPC apps
from scipy_central.person.views import create_new_account_internal
from scipy_central.filestorage.models import FileSet
from scipy_central.tagging.views import get_and_create_tags
from scipy_central.utils import (send_email, paginated_queryset,
                                 highlight_code, ensuredir)
from scipy_central.rest_comments.views import compile_rest_to_html
from scipy_central.pages.views import page_404_error
from scipy_central.pagehit.views import create_hit, get_pagehits
from scipy_central.submission.templatetags.core_tags import top_authors
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
import shutil
import zipfile
import tempfile
import mimetypes; mimetypes.init()
from pygments.lexers import guess_lexer_for_filename
from pygments.util import ClassNotFound

logger = logging.getLogger('scipycentral')
logger.debug('Initializing submission::views.py')

def get_items_or_404(view_function):
    """
    Decorator for views that ensures the revision and submission requested
    actually exist. If not, throws a 404, else, it calls the view function
    with the required inputs.
    """
    def decorator(request, item_id, rev_id=None, slug=None, filename=None):
        """Retrieves the ``Submission`` and ``Revision`` objects when given,
        at a minimum the submission's primary key (``item_id``). Since the
        submission can have more than 1 revision, we can get a specific
        revision, ``rev_id``, otherwise we will always get the latest
        revision. ``slug`` is ignored for now - just used to create good SEO
        URLs.
        """
        try:
            # Use the Submissions manager's ``all()`` function
            the_submission = models.Submission.objects.all().filter(id=item_id)
        except ObjectDoesNotExist:
            return page_404_error(request, 'You request a non-existant item')

        if len(the_submission) == 0:
            return page_404_error(request, 'This item does not exist yet')

        the_submission = the_submission[0]
        the_revision = the_submission.last_revision
        if rev_id: # can be None or '':
            all_revisions = the_submission.revisions.all()
            rev_index = int(rev_id)-1
            if rev_index < 0:
                rev_index = len(all_revisions)-1

            try:
                the_revision = all_revisions[rev_index]
            except (ValueError, IndexError):
                return page_404_error(request, ('The requested revision is '
                                                 'non-existant.'))

        # Don't return revisions that are not approved for display yet
        if not isinstance(the_revision, models.Revision) or\
                                              not(the_revision.is_displayed):
            return page_404_error(request, "That revision isn't available yet.")

        # Is the URL of the form: "..../NN/MM/edit"; if so, then edit the item
        path_split = request.path.split('/')
        if len(path_split)>4 and path_split[4] in ['edit', 'download', 'show']:
            if path_split[4] == 'show' and len(path_split)>=6:
                return view_function(request, the_submission, the_revision,
                                     filename=path_split[5:])
            else:
                return view_function(request, the_submission, the_revision)

        # Is the URL not the canonical URL for the item? .... redirect the user
        else:
            if rev_id is None:
                rev_id_str = '0'
                do_redirect = True
            else:
                rev_id_str = str(the_revision.rev_id+1)
                do_redirect = False

            if slug is None or the_revision.slug != slug or do_redirect:
                return redirect('/'.join(['/item',
                                          item_id,
                                          rev_id_str,
                                          the_revision.slug]),
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
            elif bound.entry.sub_type == 'package':
                fields['sub_type'] = 'package'
            elif  bound.entry.sub_type == 'code':
                fields['sub_type'] = 'snippet'

            form_output = form_class(fields)
        else:
            if request.POST['sub_type'] == 'package':
                # Create a fake "UploadedFile" object, so the user can resume
                # editing or finish their submission, without being told
                # they have to reenter this field.
                zip_hash = request.POST.get('package_hash', '')
                zip_file = models.ZipFile.objects.filter(zip_hash=zip_hash)
                if zip_file:
                    zip_name = zip_file[0].raw_zip_file.name
                    uploaded_file = UploadedFile(zip_name, name=zip_name,
                                        content_type='application/zip',
                                        size=zip_file[0].raw_zip_file.size)
                    uploaded_file.skip_validation = True # see ``forms.py``
                    request.FILES['package_file'] = uploaded_file
            form_output = form_class(request.POST, request.FILES)

            if request.POST['sub_type'] == 'package' and zip_file:
                form_output.fields['package_file'].initial = uploaded_file

    else:
        form_output = form_class()

    # Rearrange the form order
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

    # NOTE: the ``user`` will always be a valid entry in our database. Code
    # posted by users that have not yet validated themselves is not displayed
    # until they do so.

    if item.cleaned_data['pk']:
        # We are editing an existing submission: pull it from the DB
        try:
            sub = models.Submission.objects.get(id=item.cleaned_data['pk'])
        except ObjectDoesNotExist:
            logger.error('Submission was not found when requesting "%s"' %\
                         request.path)
            page_404_error(request, ('You requested an invalid submission to '
                                     'edit'))
    else:
        # A new submission
        sub = models.Submission.objects.create_without_commit(created_by=user,
                                    sub_type=item.cleaned_data['sub_type'])


    # Process any tags
    tag_list = get_and_create_tags(item.cleaned_data['sub_tags'])

    # Create a ``Revision`` instance. Must always have a ``title``,
    # ``created_by``, and ``description`` fields; the rest are set according
    # to the submission type, ``sub.sub_type``
    hash_id = ''
    if sub.sub_type == 'link':
        sub_license = None
        item_url = item.cleaned_data['item_url']
        item_code = None
    elif sub.sub_type == 'snippet':
        sub_license = item.cleaned_data['sub_license']
        item_url = None
        item_code = item.cleaned_data['snippet_code']
    elif sub.sub_type == 'package':
        sub_license = item.cleaned_data['sub_license']
        item_url = None
        item_code = None

        # Handle the ZIP file more completely only when the user commits.
        # ZIP file has been validated: OK to save it to the server
        # However, this might be the second time around, so skip saving it
        # (happens after preview, or if user resumes editing submission)
        if not hasattr(request.FILES['package_file'], 'skip_validation'):
            zip_f = models.ZipFile(raw_zip_file=request.FILES['package_file'],
                                zip_hash=request.POST.get('package_hash', ''))
            zip_f.save()


    # Convert the raw ReST description to HTML using Sphinx: could include
    # math, paragraphs, <tt>, bold, italics, bullets, hyperlinks, etc.
    description_html = compile_rest_to_html(item.cleaned_data['description'])
    item_highlighted_code = highlight_code(item.cleaned_data.get(\
                                                        'snippet_code', None))
    rev = models.Revision.objects.create_without_commit(
                            entry=sub,
                            title=item.cleaned_data['title'],
                            created_by=user,
                            sub_license=sub_license,
                            description=item.cleaned_data['description'],
                            description_html=description_html,
                            hash_id=hash_id,
                            item_url=item_url,
                            item_code=item_code,
                            item_highlighted_code=item_highlighted_code,
                            is_displayed=is_displayed,
                            )

    user_url = settings.SPC['short_URL_root'] + 'user/' + str(user.id)
    if commit:
        # Save the submission, then the revision. If we have a primary key
        # (case happens when user is editing a previous submission), then
        # do not save the submission (because the Submission object has fields
        # that will never change once it has been first created). Only set
        # the ``pk`` so that the new revision object is correct.
        if item.cleaned_data['pk']:
            # We are updating an existing ``sub`` item (see code above)
            pass
        else:
            sub.save()

        rev.entry_id = sub.id
        if not is_displayed:
            rev.validation_hash = create_validation_code(rev)

        rev.save()

        # Storage location: if we do save files it will be here
        datenow = datetime.datetime.now()
        year, month = datenow.strftime('%Y'), datenow.strftime('%m')
        repo_path = os.path.join(year, month, '%06d'% sub.id)
        full_repo_path = os.path.join(settings.SPC['storage_dir'], repo_path)


        if sub.sub_type == 'package':
            # Save the uploaded file to the server. At this point we are sure
            # it's a valid ZIP file, has no malicious filenames, and can be
            # unpacked to the hard drive. See validation in ``forms.py``.


            if os.path.exists(full_repo_path) and sub.fileset.repo_path == \
                                                                     repo_path:
                # Make a temporary directory and copy the existing package
                # repository to that location
                temp_dir = tempfile.mkdtemp(prefix='tmp_spc_')
                src = os.path.join(full_repo_path, '.' + \
                                           settings.SPC['revisioning_backend'])
                shutil.move(src, temp_dir)
                shutil.rmtree(full_repo_path, ignore_errors=True)
            else:
                temp_dir = None

            # Create/ensure destination directory exists
            ensuredir(full_repo_path)

               # Copy ZIP file
            zip_file = request.FILES['package_file']
            dst = os.path.join(full_repo_path, zip_file.name)
            src = os.path.join(settings.SPC['ZIP_staging'], zip_file.name)
            shutil.copyfile(src, dst)
            # os.remove(src) Keep the original ZIP file, for now

            # Remove the entry from the database
            zip_hash = request.POST.get('package_hash', '')
            zip_objs = models.ZipFile.objects.filter(zip_hash=zip_hash)
            if zip_objs:
                zip_objs[0].delete()

            # Unzip file and commit contents to the repo
            zip_f = zipfile.ZipFile(dst, 'r')
            zip_f.extractall(full_repo_path)
            zip_f.close()
            os.remove(dst) # but delete the copy

            # Delete common RCS directories that might have been in the ZIP
            for path, dirs, files in os.walk(full_repo_path):
                if os.path.split(path)[1] in settings.SPC['common_rcs_dirs']:
                    shutil.rmtree(path, ignore_errors=True)


            if temp_dir:
                src = os.path.join(temp_dir, '.' + \
                                           settings.SPC['revisioning_backend'])
                dst = os.path.join(full_repo_path , '.' + \
                                           settings.SPC['revisioning_backend'])
                try:
                    os.rename(src, dst)
                except os.error, e:
                    # For cases when /tmp is on a different filesystem
                    # (usually production servers)
                    import errno
                    if e.errno == errno.EXDEV:
                        shutil.copytree(src, dst, symlinks=True)
                        shutil.rmtree(src)
                    else:
                        raise

                shutil.rmtree(temp_dir, ignore_errors=True)
                repo = sub.fileset.get_repo()
            else:
                # Create the repo
                sub.fileset = FileSet.objects.create(repo_path=repo_path)
                repo = sub.fileset.create_empty()
                sub.save()


            # Then add all files from the ZIP file to the repo. Add directories
            # at a time rather than file-by-file.
            for path, dirs, files in os.walk(full_repo_path):
                if os.path.split(path)[1] == '.' + \
                                          settings.SPC['revisioning_backend']:
                    for entry in dirs[:]:
                        dirs.remove(entry)

                    continue

                all_files = []
                for name in files:
                    all_files.append(os.path.join(path, name))

                if all_files:
                    repo.add(patterns=all_files, ignore_errors=True)


            # Add "DESCRIPTION.txt"
            descrip_name = os.path.join(full_repo_path, 'DESCRIPTION.txt')
            descrip_file = file(descrip_name, 'w')
            descrip_file.write(rev.description)
            descrip_file.close()
            sub.fileset.add_file(descrip_name, user=user_url,
                            commit_msg=('Added/updated files from web-uploaded '
                                    'ZIP file. Added DESCRIPTION.txt also.'))

        if sub.sub_type == 'snippet':
            fname = rev.slug.replace('-', '_') + '.py'
            if not item.cleaned_data['pk']:
            # Create a new repository for the files

                sub.fileset = FileSet.objects.create(repo_path=repo_path)
                sub.save()
                commit_msg = ('Add "%s" to the repo '
                              'based on the web submission by user "%s"') %\
                                                              (fname, user_url)
            else:
                commit_msg = ('Update of file(s) in the repo '
                              'based on the web submission by user "%s"') %\
                                                              (user_url)


            sub.fileset.add_file_from_string(fname,
                                             request.POST['snippet_code'],
                                             user=user_url,
                                             commit_msg=commit_msg)

        if sub.sub_type in ['snippet', 'package']:
            license_file = settings.SPC['license_filename']
            license_text = get_license_text(rev)
            sub.fileset.add_file_from_string(license_file, license_text,
                                             user="SciPy Central",
                            commit_msg="SPC: added/updated license file" )
            rev.hash_id = sub.fileset.get_hash()


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

        # Update the search index so that the tags are included in the search
        rev.save()

        # log the new submission and revision
        logger.info('New %s: %s [id=%d] and revision id=%d' % (
                                                sub.sub_type,
                                                item.cleaned_data['title'],
                                                sub.id,
                                                rev.id))

    return sub, rev, tag_list

#------------------------------------------------------------------------------
# Licensing
def get_license_text(rev):
    """
    Generates and returns the license text for the given revision. Uses these
    revision and authorship information from previous revisions, if necessary,
    to create the license.
    """
    # See http://wiki.creativecommons.org/CC0_FAQ for all the details
    if rev.entry.num_revisions > 1:
        update_list = ['', 'Subsequent updates by:']
    else:
        update_list = []
    for idx, item in enumerate(rev.entry.revisions.all()):
        if idx > 0:
            url = settings.SPC['short_URL_root'] + 'user/'
            url += str(item.created_by.id) + '/'
            date = datetime.datetime.strftime(item.date_created, '%d %B %Y')
            update_list.append('%s on %s' % (url, date))

    update_string = '\n'.join(update_list)

    if rev.sub_license.slug == 'cc0':
        return """%s
-----
Originally written on %s by %s
%s

To the extent possible under law, the author(s) have dedicated all copyright
and related and neighboring rights to this software to the public domain
worldwide. This software is distributed without any warranty.

You should have received a copy of the CC0 Public Domain Dedication along with
this software (see below).

Also see http://creativecommons.org/publicdomain/zero/1.0/
-----
%s
""" % \
            (rev.title, datetime.datetime.strftime(rev.entry.date_created,
                                                   '%d %B %Y'),
            settings.SPC['short_URL_root'] + 'users/' +\
                                           rev.entry.created_by.profile.slug,
            update_string, rev.sub_license.text_template)

    if rev.sub_license.slug == 'bsd':

        creator_url = settings.SPC['short_URL_root'] + 'user/' + \
                                                str(rev.created_by.id) + '/'
        text = ('{{title}}\n'
                'Copyright holder: {{copyright_holder}} (full details at this page)\n'
                '-----\n') + rev.sub_license.text_template
        context = {}
        context['title'] = rev.title
        context['copyright_holder'] = creator_url
        context['year'] = datetime.datetime.now().year
        resp = template.Template(text)
        return resp.render(template.Context(context))

#------------------------------------------------------------------------------
# All submissions: have a form associated with them, as well as a number of
# fields that must appear in a certain order
Item = namedtuple('Item', 'form field_order')
SUBS = {'snippet': Item(forms.SnippetForm, field_order=['title',
                        'snippet_code', 'description', 'sub_tags',
                        'sub_license', 'email', 'sub_type', 'pk']),
        'package': Item(forms.PackageForm, field_order=['title',
                        'description', 'sub_license',
                        'package_file', 'package_hash',
                        'sub_tags', 'email', 'sub_type', 'pk']),
        'link': Item(forms.LinkForm, field_order=['title', 'description',
                        'item_url', 'sub_tags', 'email', 'sub_type', 'pk']),
        }


def new_or_edit_submission(request, item_type, bound_form=False):
    """
    Users wants to submit a new link item, or continue editing a submission.
    There are multiple possible paths through the logic here. Careful about
    making changes.
    """
    # User is going to edit their submission
    sub_type = None
    if isinstance(bound_form, models.Revision):
        new_item_or_edit = True
        sub_type = bound_form.entry.sub_type # for later on...

    # Cancel button, or a GET request
    elif request.POST.has_key('spc-cancel'):
        return redirect('spc-main-page')

    else:
        new_item_or_edit = False

    commit = False
    if request.POST.has_key('spc-edit'):
        new_item_or_edit = True
        bound_form = True

    if request.POST.has_key('spc-submit'):
        bound_form = True
        commit = True

    if request.POST.has_key('spc-preview'):
        bound_form = True

    buttontext_extra = ''
    if item_type == 'snippet' and request.method == 'GET':
        itemtype = 'snippet'
        new_item_or_edit = True
    elif item_type == 'package' and request.method == 'GET':
        itemtype = 'package'
        buttontext_extra = '(Upload ZIP file on next page)'
        new_item_or_edit = True
        #return not_implemented_yet(request, 48)
    elif item_type == 'link' and request.method == 'GET':
        itemtype = 'link'
        new_item_or_edit = True
    else:
        itemtype = request.POST.get('sub_type', sub_type)

    # Important: make a copy of ``field_order``, since it may be altered
    field_order = SUBS[itemtype].field_order[:]

    theform = get_form(request, form_class=SUBS[itemtype].form,
                       field_order=field_order, bound=bound_form)

    # OK, having all that out of the way, lets process the user's submission
    # 0. Use the built-in forms checking to validate the fields.
    if new_item_or_edit or not(theform.is_valid()):
        return render_to_response('submission/new-item.html', {},
                              context_instance=RequestContext(request,
                                    {'item': theform,
                                     'buttontext': 'Preview your submission',
                                     'buttontext_extra': buttontext_extra,
                                     'autocomplete_field': 'id_sub_tags',
                                     'autocomplete_url': r'"spc-tagging-ajax"',
                                     'pagetitle': 'Create a new submission'}))


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
        context['finish_button_text'] = 'Finish submission'
        # %% is required in below string to correctly format
        html = ("""<div id="spc-preview-edit-submit" class="spc-form">
                <form action="{%% url spc-new-submission item_type='%s' %%}" 
                method="POST" enctype="multipart/form-data">\n
                {%% csrf_token %%}\n
                {{item.as_hidden}}
                <div id="spc-preview-edit-submit-button-group">
                <input class="btn btn-primary" type="submit" name="spc-cancel" value="Cancel"
                id="spc-item-cancel" />\n
                <input class="btn btn-primary" type="submit" name="spc-edit"   value="Resume editing"
                id="spc-item-edit" />\n
                <input class="btn btn-success" type="submit" name="spc-submit"
                value="{{ finish_button_text }}"
                id="spc-item-submit"/>\n
                </div></form></div>""" % itemtype)
        resp = template.Template(html)
        extra_html = resp.render(template.Context(context))
        return render_to_response('submission/item.html', {},
                                  context_instance=RequestContext(request,
                                                  {'item': rev,
                                                   'tag_list': tag_list,
                                                   'extra_html': extra_html,
                                                   'preview': True,
                                                   }))

    else:
        # 4. Thank user and return with any extra messages, and send an email
        ctx_dict = {'user': user,
                    'item': rev,
                    'site': Site.objects.get_current()
                    }

        # User is signed in
        if authenticated:
            show_url = True
            extra_messages = 'A confirmation email has been sent to you.'
            message = render_to_string('submission/email_user_thanks.txt',
                                   ctx_dict)
        else:
            show_url = False
            extra_messages = ('You have been sent an email to '
                              '<i>confirm your submission</i> and to create '
                              'an account (if you do not have one '
                              'already). <p>Unconfirmed submissions '
                              'cannot be accepted, and <b>will be '
                              'deleted</b> after %d days. Please sign in '
                              'to avoid having to confirm your '
                              'valuable submissions in the future.') % \
                            settings.SPC['unvalidated_subs_deleted_after']

            # User is not signed in, but they have validated their email address
            if user.profile.is_validated:
                message = render_to_string(\
                  'submission/email_validated_user_unvalidated_submission.txt',
                   ctx_dict)
            else:
                # User is told they first need to create account before their
                # submission shows in the website
                message = render_to_string(\
                'submission/email_unvalidated_user_unvalidated_submission.txt',
                   ctx_dict)

        send_email((user.email,), ("Thank you for your contribution "
                                        "to SciPy Central"), message=message)

        message = render_to_string('submission/email_website_admin.txt',
                                   ctx_dict)
        send_email((settings.SERVER_EMAIL,), ('A new/edited submission was '
                       'made on SciPy Central'), message=message)

        return render_to_response('submission/thank-user.html', ctx_dict,
                              context_instance=RequestContext(request,
                                    {'extra_message': extra_messages,
                                     'show_url': show_url}))


def create_validation_code(revision):
    """
    From BSD licensed code, James Bennett
    https://bitbucket.org/ubernostrum/django-registration/src/58eef8330b0f/
                                                         registration/models.py
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
# View and download existing submissions:
@get_items_or_404
def view_item(request, submission, revision):
    """
    Shows a submitted item to web users. The ``slug`` is always ignored, but
    appears in the URLs for the sake of search engines. The revision, if
    specified >= 0 will show the particular revision of the item, rather than
    the latest revision (default).
    """
    create_hit(request, submission)
    permalink = settings.SPC['short_URL_root'] + str(submission.id) + '/' + \
                                                  str(revision.rev_id+1) + '/'
    latest_link = settings.SPC['short_URL_root'] + str(submission.id) + '/'


    pageviews = get_pagehits('submission', start_date=datetime.datetime.now()\
                        -datetime.timedelta(days=settings.SPC['hit_horizon']),
                        item_pk=submission.id)

    package_files = []
    if submission.sub_type == 'package':
        # Update the repo to the version required
        submission.fileset.checkout_revision(revision.hash_id)
        package_files = list(submission.fileset.list_iterator())


    return render_to_response('submission/item.html', {},
                              context_instance=RequestContext(request,
                                {'item': revision,
                                 'tag_list': revision.tags.all(),
                                 'permalink': permalink,
                                 'latest_link': latest_link,
                                 'pageviews': pageviews,
                                 'pageview_days': settings.SPC['hit_horizon'],
                                 'package_files': package_files,
                                }))


def get_display(submission, revision, filename):
    """
    Determines how to display a filetype, given its name
    """
    fname = filename[-1]
    mime_guess = mimetypes.guess_type(fname)[0]
    mime_type, mime_file = mime_guess.split('/')

    # Set the repo to the correct revision
    repo = submission.fileset.checkout_revision(revision.hash_id)
    src = os.path.join(repo.local_dir, os.sep.join(filename))

    if str(mime_type).startswith('image'):
        # We only dislay certain image types
        VALID_IMAGE_TYPES = ['gif', 'jpeg', 'png', 'bmp']
        if mime_file in VALID_IMAGE_TYPES:
            disp_type = 'image'
            # Copy image over to media location; we must make a copy, incase
            # a later user views a different revision of the document
            disp_obj = os.path.normpath(force_unicode(datetime.datetime.now()\
            .strftime(smart_str(settings.SPC['resized_image_dir']))))\
                    + os.sep + fname
            dst = os.path.join(settings.SPC['storage_dir'], disp_obj)
            idx = 1
            while os.path.exists(dst):
                disp_obj = disp_obj.split(fname)[0] + '%s_%d.%s' % \
                               (fname.lower().split('.'+mime_file)[0], idx,
                                mime_file)
                dst = os.path.join(settings.SPC['storage_dir'], disp_obj)
                idx += 1

            # Finally, copy the file across to the web storage area
            shutil.copy2(src, dst)

        return disp_type, disp_obj


    if not repo:
        # Something went wrong when checking out the repo
        logger.error('Could not checked out revision "%s" for '
                             'rev.id=%d' % (revision.hash_id, revision.id))
        return 'none', None


    if str(mime_type).startswith('text'):

        # Read the first 10kb to send to the lexer guessing mechanism
        if os.path.exists(src):
            fh = open(src, 'rb')
            file_content = fh.readlines(10*1024)
            amount_read = fh.tell()
            fh.close()
        else:
            return 'none', None

        try:
            lexer = guess_lexer_for_filename(fname.lower(),
                                             ''.join(file_content))
        except ClassNotFound:
            pass

        else:
            disp_type = 'html'
            # Only re-read the file if we didn't read it all the first time
            if os.path.getsize(src) == amount_read:
                file_content = ''.join(file_content)
            else:
                fh = open(src, 'rb')
                file_content = fh.read()
                fh.close()

            # TODO(KGD): consider wrapping long text lines for text files

            # Return the highlighted code, if we know the lexer
            return disp_type, highlight_code(file_content,
                                             lexer=lexer.mimetypes[0])

    # All other file types are assumed to be binary
    disp_type = 'binary'
    #disp_obj = link to file (add this capability to ``FileSet``)

    return disp_type, disp_obj

@get_items_or_404
def show_file(request, submission, revision, filename):
    """
    Display a ``filename`` from a given ``submission`` and ``revision``
    """
    key_parts = [str(submission.id), str(revision.id)]
    key_parts.extend(filename)
    key = md5('-'.join(key_parts)).hexdigest()

    display = models.DisplayFile.objects.filter(fhash=key)
    if display:
        # Get the displayed item from the database rather than checking out
        # the repository, determining the file type and HTML to display
        obj = display[0]
    else:
        # Create the displayed item and store it in the database
        disp_type, disp_obj = get_display(submission, revision, filename)
        obj = models.DisplayFile.objects.create(fhash=key,
                                                display_type=disp_type,
                                                display_obj=disp_obj)

    # Now return ``obj``
    if obj.display_type == 'image':
        return HttpResponse(u'<img = ...')
    elif obj.display_type == 'html':
        return HttpResponse(obj.display_obj)
    elif obj.display_type == 'binary':
        return HttpResponse(u'<a href="%s">%s</a>' % (obj.display_obj,
                                                      filename[-1]))
    elif obj.display_type == 'none':
        return HttpResponse(filename[-1])

@get_items_or_404
def download_submission(request, submission, revision):

    create_hit(request, submission, extra_info="download")
    if submission.sub_type == 'snippet':
        response = HttpResponse(mimetype="application/x-python")
        fname = submission.slug.replace('-', '_') + '.py'
        response["Content-Disposition"] = "attachment; filename=%s" % fname
        source = Site.objects.get_current().domain + \
                                                 submission.get_absolute_url()
        response.write('# Source: ' + source + '\n\n' + revision.item_code)
        return response

    if submission.sub_type == 'package':
        zip_dir = os.path.join(settings.SPC['ZIP_staging'], 'download')
        ensuredir(zip_dir)
        response = HttpResponse(mimetype="attachment; application/zip")
        zip_name = '%s-%d-%d.zip' % (submission.slug, submission.id,
                                     revision.rev_id_human)
        response['Content-Disposition'] = 'filename=%s' % zip_name
        full_zip_file = os.path.join(zip_dir, zip_name)
        if not os.path.exists(full_zip_file):

            # Set the repo's state to the state when that particular revision
            # existed
            out = submission.fileset.checkout_revision(revision.hash_id)
            if out:
                logger.info('Checked out revision "%s" for rev.id=%d' % \
                            (revision.hash_id, revision.id))
            else:
                logger.error('Could not checked out revision "%s" for '
                             'rev.id=%d' % (revision.hash_id, revision.id))
                return page_404_error(request, ('Could not create the ZIP '
                                                'file. This error has been '
                                                'reported.'))

            zip_f = zipfile.ZipFile(full_zip_file, "w", zipfile.ZIP_DEFLATED)
            src_dir = os.path.join(settings.SPC['storage_dir'],
                                   submission.fileset.repo_path)
            for path, dirs, files in os.walk(src_dir):
                for name in files:
                    file_name = os.path.join(path, name)
                    file_h = open(file_name, "r")
                    zip_f.write(file_name, file_name.partition(src_dir)[2])
                    file_h.close()

            for file_h in zip_f.filelist:
                file_h.create_system = 0

            zip_f.close()

            # Return the repo checkout back to the most recent revision
            out = submission.fileset.checkout_revision(submission.\
                                                       last_revision.hash_id)

        # Return the ZIP file
        zip_data = open(full_zip_file, "rb")
        response.write(zip_data.read())
        zip_data.close()
        return response


#------------------------------------------------------------------------------
# Editing submissions: decorator order is important!
@login_required
@get_items_or_404
def edit_submission(request, submission, revision):

    if submission.sub_type in ['link', 'package'] and \
                                        request.user != submission.created_by:
        return page_404_error(request, ('You are not authorized to edit that '
                                        'submission. Only the original author '
                                        'may edit it.'))

    # if by POST, we are in the process of editing, so don't send the revision
    if request.POST:
        return new_or_edit_submission(request, submission.sub_type, bound_form=False)
    else:
        return new_or_edit_submission(request, submission.sub_type,bound_form=revision)


#------------------------------------------------------------------------------
def sort_items_by_page_views(all_items, item_module_name):
    # TODO(KGD): Cache this reordering of ``items`` for a period of time

    today = datetime.datetime.now()
    start_date = today - datetime.timedelta(days=settings.SPC['hit_horizon'])
    page_order = get_pagehits(item_module_name, start_date=start_date,
                                                               end_date=today)
    page_order.sort(reverse=True)

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


def show_items(request, what_view='', extra_info=''):
    """ Show different views onto all **revision** items (not submissions)
    """
    what_view = what_view.lower()
    extra_info = extra_info.lower()
    entry_order = []
    page_title = ''
    template_name = 'submission/show-entries.html'
    if what_view == 'tag':
        all_revs = models.Revision.objects.all().\
                                        filter(tags__slug=slugify(extra_info))
        page_title = 'All entries tagged'
        entry_order = list(all_revs)
    elif what_view == 'show' and extra_info == 'all-tags':
        page_title = 'All tags'
        template_name = 'submission/show-tag-cloud.html'
    elif what_view == 'show' and extra_info == 'all-revisions':
        # Show all submissions in reverse time order
        all_revs = models.Revision.objects.all().order_by('-date_created')
        page_title = 'All revisions'
        extra_info = ''
        entry_order = list(all_revs)
    elif what_view == 'show' and extra_info == 'all-unique-revisions':
        all_subs = models.Submission.objects.all().order_by('-date_created')
        page_title = 'All submissions'
        extra_info = ' (only showing the latest revision)'
        entry_order = [sub.last_revision for sub in all_subs if sub.last_revision.is_displayed]
    elif what_view == 'sort' and extra_info == 'most-viewed':
        page_title = 'All submissions in order of most views'
        extra_info = ''
        all_subs = set()
        for rev in models.Revision.objects.all():
            all_subs.add(rev.entry)
        entry_order, _ = sort_items_by_page_views(all_subs, 'submission')
        entry_order = [entry.last_revision for entry in entry_order]
    elif what_view == 'show' and extra_info == 'top-contributors':
        page_title = 'Top contributors'
        extra_info = ''
        entry_order = top_authors('', 0)
    elif what_view == 'validate':
        return validate_submission(request, code=extra_info)

    entries = paginated_queryset(request, entry_order)
    return render_to_response(template_name, {},
                              context_instance=RequestContext(request,
                                                {'entries': entries,
                                                 'page_title': page_title,
                                                 'extra_info': extra_info,
                                                 'what_view' : what_view,}))
