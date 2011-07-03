from django.db import models
from django.db.models import signals
from django.core.urlresolvers import reverse

from django.template.defaultfilters import slugify
from pygments import formatters, highlight, lexers

class License(models.Model):
    """
    License for the submission
    """
    name = models.CharField(max_length=255,
                            help_text="License used for code submissions.")
    slug = models.SlugField(max_length=255, editable=False)

    description = models.TextField(help_text="Short description of license")
    text_template = models.TextField(help_text=('Full license text with ',
                                                'template fields'))

    def __unicode__(self):
        return self.name

    class Meta:
        permissions = (("can_edit", "Can edit this license"),)


class SubmissionManager(models.Manager):
    def create_without_commit(self, **kwargs):
        """
        Uses code from django.db.models.create(...) to create a new instance
        without writing to the database.

        To save the object to the database (presumably after validating it, or
        doing some other checks), you can call the ``obj.save()`` method. E.g.:

            obj = models.Submission.objects.create_without_commit(....)
            ...
            ...
            obj.save(force_insert=True, using=models.Submission.objects.db)
            # or
            obj.save(force_insert=True)
        """
        qs = self.get_query_set()
        obj = qs.model(**kwargs)
        self._for_write = True
        #obj.save(force_insert=True, using=self.db)
        return obj

    def all(self):
        return self.filter(is_displayed=True) #.filter(is_preview=False)

    def all__for_backup(self):
        """ Sometimes we really do need all the submission objects."""
        return super(SubmissionManager, self).all()


class Submission(models.Model):
    """
    A single model for all submission types. Most of the information is stored
    in the ``Revision`` for the submission, allowing us to store a history of
    the submission in consecutive revisions.
    """
    objects = SubmissionManager()
    # Submission type
    SUBMISSION_TYPE = (
        ('snippet', 'Code snippet'),
        ('package', 'Code library/package'),
        ('link',    'Remote link'),
    )
    sub_type = models.CharField(max_length=10, choices=SUBMISSION_TYPE,
                help_text = 'Your submission should be one of 3 types')

    # Original submitter
    created_by = models.ForeignKey('person.UserProfile', null=True, blank=True)
    date_created = models.DateTimeField(auto_now_add=True, editable=False)

    # fileset: for revisioning of the submission
    fileset = models.ForeignKey('filestorage.FileSet', null=True, blank=True)

    # frozen: no further revisions allowed
    frozen = models.BooleanField(default=False)

    # Should this submission be displayed? One might decide to remove
    # submissions from display if they violate licenses, or are improper in
    # some way.
    # Also set False for submissions by users that submit when not
    # authenticated.
    is_displayed = models.BooleanField(default=False)

    # For submissions created only for previewing. Is set to False once the
    # submission is actually submitted.
    # TODO(KGD): remove this eventually
    #is_preview = models.BooleanField(default=True)

    # FUTURE
    # ------
    # cloned_from = models.ForeignKey('self', null=True, blank=True)
    # vote_for_inclusion_in_scipy [ForeignKey] to ThumbsUpDown model
    # modules_required  [list of modules required to run the code]

    @property
    def last_revision(self):
        try:
            return self.revisions.order_by('-id')[0]
        except (KeyError, IndexError):
            return None

    @property
    def num_revisions(self):
        return self.revisions.count()

    @property
    def slug(self):
        return self.last_revision.slug

    def __unicode__(self):
        return self.slug

class RevisionManager(models.Manager):
    def create_without_commit(self, **kwargs):
        """
        Uses code from django.db.models.create(...) to create a new instance
        without writing to the database.

        To save the object to the database (presumably after validating it, or
        doing some other checks), you can call the ``obj.save()`` method. E.g.:

            obj = models.Revision.objects.create_without_commit(....)
            ...
            ...
            obj.save(force_insert=True, using=models.Revision.objects.db)
            # or
            obj.save(force_insert=True)
        """
        qs = self.get_query_set()
        obj = qs.model(**kwargs)
        self._for_write = True
        #obj.save(force_insert=True, using=self.db)
        return obj

    def objects_for_search():
        """
        Returns only the objects used for searching.
        """
        return [sub.last_revision for sub in Submission.objects.all()]


class Revision(models.Model):

    objects = RevisionManager()

    # The submission: parent item for this revision
    entry = models.ForeignKey(Submission, related_name="revisions")

    # user-provided submission title.
    title = models.CharField(max_length=150,
                        help_text='Provide a <b>title</b> for your submission')

    # auto-created slug field
    slug = models.SlugField(max_length=155, editable=False)

    # Created on
    date_created = models.DateTimeField(auto_now_add=True, editable=False)

    # Users that created this submission
    created_by = models.ForeignKey('person.UserProfile', null=True, blank=True)

    # Submission license. Only used for code packages. Code snippets are
    # always CC0 licensed, and external links must list their own license.
    # There are just too many licenses out there for us to track them all.
    # We don't expect people to be using this site to screen for code based
    # on license. Use Google for that.
    # The only choices right now are CC0 and simplified-BSD.
    sub_license = models.ForeignKey(License, null=True, blank=True,
                verbose_name="Choose a license for your submission")

    # User-provided description of the submission. Uses reStructuredText.
    # Is blank for URL (link) submissions.
    description = models.TextField(help_text=('<b>Explain</b> your '
                    'submission'))

    # HTML version of the ReST ``description`` field
    description_html = models.TextField()

    # User uploaded image
    screenshot = models.ForeignKey('screenshot.Screenshot', null=True,
                                   blank=True)

    # Code snippet hash (will use ssdeep later on: 57 characters)
    hash_id = models.CharField(max_length=60, null=True, blank=True,
                               editable=False)

    # For snippet submissions
    item_code = models.TextField(null=True, blank=True)
    item_highlighted_code = models.TextField(editable=False, null=True,
                                             blank=True)

    # For link-type submissions
    item_url = models.URLField(verbose_name="URL for link-type submssions",
                               blank=True, null=True,
                help_text=("Link to the code's website, documentation, or "
                           'publication (<a target="_blank" href="http://en.'
                           'wikipedia.org/wiki/Digital_object_identifier">'
                           'DOI preferred</a>)'), max_length=255)

    # Tags for this revision
    tags = models.ManyToManyField('tagging.Tag', through='TagCreation')

    # FUTURE: inspired_by: a comma-separated list of previous submissions
    # FUTURE: list of modules required to run the code

    def __unicode__(self):
        return self.title[0:50] + '::' + str(self.created_by.username)

    @property
    def rev_id(self):
        """ Determines which revision of the submission this is, given the
        ``revision`` object.
        """
        return list(self.entry.revisions.all()).index(self)

    def save(self, *args, **kwargs):
        """ Override the model's saving function to create the slug """
        # http://docs.djangoproject.com/en/dev/topics/db/models/
                                          #overriding-predefined-model-methods
        self.slug = slugify(self.title)

        #from pygments.style import Style
        #from pygments.token import Comment
        #from pygments import formatters
        #get_style_by_name('default')
        #class ScipyStyle(Style):
            #default_style = "default"
            #styles = {
                #Comment: 'italic #888',
                #}
        #formatters.HtmlFormatter(style=ScipyStyle).get_style_defs('div#spc-section-body .highlight')
        if self.item_code:
            self.item_highlighted_code = highlight(self.item_code,
                                                   lexers.PythonLexer(),
                                       formatters.HtmlFormatter(linenos=True))


        # Call the "real" save() method.
        super(Revision, self).save(*args, **kwargs)


class TagCreation(models.Model):
    """
    Tracks by whom and when tags were created
    """
    created_by = models.ForeignKey('person.UserProfile')
    revision = models.ForeignKey(Revision)
    tag = models.ForeignKey('tagging.Tag')
    date_created = models.DateTimeField(auto_now_add=True, editable=False)
