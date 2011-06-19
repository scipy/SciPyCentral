from django.db import models
from django.db.models import signals
from scipy_central.utils import unique_slugify

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

class Submission(models.Model):
    """
    A single model for all submission types. Most of the information is stored
    in the ``Revision`` for the submission, allowing us to store a history of
    the submission in consecutive revisions.
    """
    # Submission type
    SUBMISSION_TYPE = (
        ('snippet', 'Example code snippet, a cookbook entry, etc.'),
        ('package', 'Code package hosted on this site'),
        ('link',    'Reference to a package hosted elsewhere'),
    )
    sub_type = models.CharField(max_length=10, choices=SUBMISSION_TYPE,
                help_text = 'Your submission should be one of 3 types')

    # Original submitter
    created_by = models.ForeignKey('person.UserProfile', null=True, blank=True)

    # Total dowloads: sum of all downloads (code snippets) and total
    # outgoing clicks (for links)
    tot_downloads_clicks = models.PositiveIntegerField(default=0)

    # Total pageviews: sum of all views
    tot_pageviews = models.PositiveIntegerField(default=0)

    # n_revisions: total number of revisions
    tot_revisions = models.PositiveIntegerField(default=0)

    # frozen: no further revisions allowed
    frozen = models.BooleanField(default=False)

    # Should this submission be displayed? One might decide to remove
    # submissions from display if they violate licenses, or are improper in
    # some way. Also set False for submissions by users that submit when not
    # authenticated.
    is_displayed = models.BooleanField(default=False)

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
    def slug(self):
        return self.last_revision.slug

    def __unicode__(self):
        return self.slug + '::rev-' + str(self.tot_revisions)

class Revision(models.Model):

    # The submission: parent item for this revision
    entry = models.ForeignKey(Submission, related_name="revisions")

    # user-provided submission title.
    title = models.CharField(max_length=150,
                             help_text='Provide a title for your submission')

    # auto-created slug field [*unique field*]
    slug = models.SlugField(max_length=255, unique=True, editable=False)

    # Created on
    date_created = models.DateTimeField(auto_now_add=True, editable=False)

    # List of authors for this submission (usually one), but we are
    # provisioning for collaborative authorship as well
    author = models.ForeignKey('person.UserProfile', null=True, blank=True)

    # Submission license. Only used for code packages. Code snippets are
    # always CC0 licensed, and external links must list their own license.
    # There are just too many licenses out there for us to track them all.
    # We don't expect people to be using this site to screen for code based
    # on license. Use Google for that.
    # The only choices right now are CC0 and simplified-BSD.
    sub_license = models.ForeignKey(License, null=True, blank=True,
                verbose_name="Choose a license for your submission")

    # A short summary [150 chars] describing the submission.
    summary = models.CharField(max_length=255, help_text = ('Explain what '
                    'the submission does in less than 250 characters. Users '
                    'initially see this summary to '
                    'decide if they want to view more information about your '
                    'submission.'))

    # User-provided description of the submission [10000 character limit].
    # Uses reStructuredText
    description = models.TextField(help_text=('Please explain your '
                    'submission in more depth. Let the community know what '
                    'your code or link does, how it solves the problem, '
                    'and/or how it works.'), blank=True, null=True)

    # HTML version of the ReST ``description`` field
    description_html = models.TextField(editable=False)

    # User uploaded image
    screenshot = models.ForeignKey('screenshot.Screenshot', null=True,
                                   blank=True)

    # Code snippet hash
    hash_id = models.CharField(max_length=40, null=True, blank=True,
                               editable=False)

    # Number of downloads
    n_downloads_clicks = models.IntegerField(default=0,
                            verbose_name='Number of downloads or page clicks')

    # number of full-page views of this submission
    n_views = models.IntegerField(default=0,
                                  verbose_name='Number of page views')

    # For link-type submissions
    item_url = models.URLField(verbose_name="URL for link-type submssions",
                               blank=True, null=True,
                help_text=("Link to the code's website, documentation, or "
                           'publication (<a target="_blank" href="http://en.'
                           'wikipedia.org/wiki/Digital_object_identifier">'
                           'DOI preferred</a>)'), max_length=255)

    # fileset
    fileset = models.ForeignKey('filestorage.FileSet', null=True, blank=True)

    # Tags for this revision
    tags = models.ManyToManyField('tagging.Tag', null=True, blank=True)

    # inspired_by: a comma-separated list of previous submissions

    # vote_for_inclusion_in_scipy [ForeignKey]

    # modules (list of modules required to run the code)


    def save(self, *args, **kwargs):
        """ Override the model's saving function to create the slug """
        # http://docs.djangoproject.com/en/dev/topics/db/models/
                                          #overriding-predefined-model-methods
        unique_slugify(self, self.title, 'slug')

        # TODO(KGD):
        self.description_html = 'DESCRIPTION HTML TO BE CREATED STILL'

        # Call the "real" save() method.
        super(Revision, self).save(*args, **kwargs)

    #def get_absolute_url(self):
    #    return(....)
    #get_absolute_url = models.permalink(get_absolute_url)
