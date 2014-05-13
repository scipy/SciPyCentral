# django imports
from django.conf import settings
from django.http import Http404, HttpResponse
from django.template import RequestContext
from django.template.loader import render_to_string
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.contrib.sites.models import Site
from django.forms.models import model_to_dict
from django.views.generic.edit import FormView
from django.views.decorators.csrf import csrf_protect
from django.shortcuts import get_object_or_404, render_to_response

# scipy central imports
from scipy_central.tagging.views import get_and_create_tags
from scipy_central.filestorage.models import FileSet
from scipy_central.utils import send_email
from scipy_central.submission import forms, models, storage

# python imports
import logging

logger = logging.getLogger('scipycentral')
logger.debug('Initializing submission::views.create.py')

def email_after_submission(instance):
    """
    Send email notifications to created user and admin
    for new/ edited submissions
    """
    if not isinstance(instance, models.Revision):
        raise TypeError('Revision object should be passed as argument')

    email_context = {
        'user': instance.created_by,
        'item': instance,
        'site': Site.objects.get_current()
    }

    # signed in users
    if instance.is_displayed:
        message = render_to_string('submission/email_user_thanks.txt',
                                   email_context)
    else:
        # if user registered but not signed in
        if instance.created_by.profile.is_validated:
            message = render_to_string(
                'submission/email_validated_user_unvalidated_submission.txt',
                email_context)

        # unknown users
        else:
            message = render_to_string(
                'submission/email_unvalidated_user_unvalidated_submission.txt',
                email_context)

    # email submitted user
    send_email((instance.created_by.email,), ('Thank you for your contribution to '
                                              'SciPy Central'), message=message)

    # email admin
    message = render_to_string('submission/email_website_admin.txt')
    send_email((settings.SERVER_EMAIL,), ('A new/edited submission '
                                          'was made on SciPy Central'),
               message=message)

class BaseSubmission(FormView):
    """
    Base class for views creating/ editing submission

    Provides common functionality
    """
    template_name = 'submission/new-item.html'

    @method_decorator(csrf_protect)
    def dispatch(self, request, *args, **kwargs):
        return super(BaseSubmission, self).dispatch(request, *args, **kwargs)

    def get_form(self, form_class):
        """ Pass `request` object to form
        """
        return form_class(self.request, **self.get_form_kwargs())


class NewSubmission(BaseSubmission):
    """
    View for creating new submission
    """
    def form_valid(self, form):
        # create submission or revision
        instance = form.save(commit=False)

        # create `package_file` attribute (not saved anyway)
        # required for passing to `SubmissionStorage` module
        if self.kwargs['item_type'] == 'package':
            instance.package_file = form.cleaned_data['package_file']

        # create new submission object
        sub_obj = models.Submission(sub_type=self.kwargs['item_type'], 
                                    created_by=instance.created_by)
        sub_obj.save()

        instance.entry = sub_obj

        # save revison object
        instance.save()

        # store data in repository
        # create FileSet object
        if sub_obj.sub_type == 'snippet' or sub_obj.sub_type == 'package':
            fileset_obj = FileSet(repo_path=storage.get_repo_path(instance))
            fileset_obj.save()

            sub_obj.fileset = fileset_obj
            sub_obj.save()

            # store obj in repo
            rev_storage = storage.SubmissionStorage(instance, is_new=True)
            try:
                hash_id = rev_storage.store()
            except Exception, e:
                logger.error('SERVER ERROR: Submission storage error:: %s' % e)
                instance.delete()
                sub_obj.delete()
                fileset_obj.delete()
                rev_storage.revert()
                return HttpResponse(status=500)

            instance.hash_id = hash_id

        # add tags
        tags_list = get_and_create_tags(form.cleaned_data['sub_tags'])
        for tag in tags_list:
            tag_intermediate = models.TagCreation(created_by=instance.created_by, 
                                                  revision=instance, tag=tag)
            tag_intermediate.save()

            # log the database action
            logger.info('User "%s" added tag "%s" to rev.id="%d"' 
                         % (instance.created_by.username, str(tag), instance.pk))

        # save revision object
        instance.save()

        # log the new submission 
        logger.info('New %s: %s [id=%d] and revision id=%d' 
                     % (sub_obj.sub_type, instance.title, sub_obj.pk, instance.pk))

        email_after_submission(instance)

        context = {
            'authenticated': self.request.user.is_authenticated(),
            'days_deleted_after': settings.SPC['unvalidated_subs_deleted_after'],
            'item': instance
        }

        return render_to_response('submission/thank-user.html', context,
                                  context_instance=RequestContext(self.request))

    def get_context_data(self, **kwargs):
        kwargs.update({
            'item_type': self.kwargs.get('item_type', None)
        })
        return super(NewSubmission, self).get_context_data(**kwargs)

    def get_form_class(self):
        item_type = self.kwargs.get('item_type', None)
        if item_type == 'snippet':
            return forms.SnippetForm
        elif item_type == 'link':
            return forms.LinkForm
        elif item_type == 'package':
            return forms.PackageForm
        else:
            raise Http404


class EditSubmission(BaseSubmission):
    """
    View for editing submission
    """
    def form_valid(self, form):
        # Resend if there are no changes in the form
        if not form.has_changed():
            return self.get(self.request)

        # create revision object
        instance = form.save(commit=False)

        instance.entry = self.sub_obj

        # save revison object
        instance.save()

        # create `package_file` attribute (not saved anyway)
        # required for passing to `SubmissionStorage` modelsule
        if self.sub_obj.sub_type == 'package':
            instance.package_file = form.cleaned_data['package_file']

        # store data in repository
        if self.sub_obj.sub_type == 'snippet' or self.sub_obj.sub_type == 'package':
            rev_storage = storage.SubmissionStorage(instance, is_new=False)
            try:
                hash_id = rev_storage.store()
            except Exception, e:
                logger.error('Submission Storage Error: %s' % e)
                instance.delete()
                rev_storage.revert(hash_id=self.rev_obj.hash_id)
                return HttpResponse(status=500)

            instance.hash_id = hash_id

        # add tags
        tags_list = get_and_create_tags(form.cleaned_data['sub_tags'])
        for tag in tags_list:
            tag_intermediate = models.TagCreation(created_by=instance.created_by, 
                                                  revision=instance, tag=tag)
            tag_intermediate.save()

            # log the database action
            logger.info('User "%s" added tag "%s" to rev.id="%d"' 
                         % (instance.created_by.username, str(tag), instance.pk))

        # save revision object
        instance.save()

        # log the new submission 
        logger.info('New %s: %s [id=%d] and revision id=%d' 
                     % (self.sub_obj.sub_type, instance.title, self.sub_obj.pk, instance.pk))

        email_after_submission(instance)

        context = {
            'authenticated': self.request.user.is_authenticated(),
            'days_deleted_after': settings.SPC['unvalidated_subs_deleted_after'],
            'item': instance
        }

        return render_to_response('submission/thank-user.html', context,
                                  context_instance=RequestContext(self.request))

    def get_context_data(self, **kwargs):
        kwargs.update({'item_type': self.sub_obj.sub_type})
        return super(EditSubmission, self).get_context_data(**kwargs)

    def get_initial(self):
        initial = super(EditSubmission, self).get_initial()
        initial.update(model_to_dict(self.rev_obj))
        # `sub_tags` is char field, each object is taken as a string
        # seperated by ','
        initial.update({
            'sub_tags': ','.join([str(tag) for tag in self.rev_obj.tags.all()])
        })
        return initial

    def get_form_class(self):
        if self.sub_obj.sub_type == 'snippet':
            return forms.SnippetForm
        elif self.sub_obj.sub_type == 'link':
            return forms.LinkForm
        elif self.sub_obj.sub_type == 'package':
            return forms.PackageForm
        else:
            raise Http404

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        sub_id = kwargs.get('item_id')
        rev_id = kwargs.get('rev_id')

        # find submission, revision objects or raise 404
        self.sub_obj = get_object_or_404(models.Submission, pk=sub_id)
        try:
            self.rev_obj = self.sub_obj.revisions.all()[int(rev_id) - 1]
        except (IndexError, AssertionError):
            raise Http404

        # only authors can edit packages
        if self.sub_obj.sub_type == 'package':
            if request.user != self.rev_obj.created_by:
                raise Http404

        return super(EditSubmission, self).dispatch(request, *args, **kwargs)
