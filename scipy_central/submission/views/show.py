# django imports
from django.conf import settings
from django.shortcuts import render_to_response, redirect, HttpResponse
from django.template import RequestContext
from django.template.defaultfilters import slugify
from django.contrib.sites.models import Site
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist

# SciPy Central imports
from scipy_central.utils import paginated_queryset, ensuredir
from scipy_central.pages.views import page_404_error
from scipy_central.pagehit.views import create_hit, get_pagehits
from scipy_central.submission.templatetags.core_tags import top_authors
from scipy_central.submission import models

# Python imports
import logging
import re
import os
import datetime
import zipfile

logger = logging.getLogger('scipycentral')
logger.debug('Initializing submission::views.show.py')

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
        if len(path_split)>4 and path_split[4] in ['download', 'show']:
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

@login_required
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
        zip_dir = os.path.join(settings.MEDIA_ROOT,
                               settings.SPC['ZIP_staging'],
                               'download')
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
        all_revs = models.Revision.objects.most_recent().\
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
