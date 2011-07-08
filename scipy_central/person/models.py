from django.contrib.auth.models import User
from django.db import models
from scipy_central.utils import unique_slugify


class UserProfile(models.Model):
    # See https://docs.djangoproject.com/en/1.3/topics/auth/

    user = models.OneToOneField(User, unique=True, related_name="profile")

    # Slug field
    slug = models.SlugField(editable=False)

    # i.e. the user's identity has been verified by a challenge/response email
    is_validated = models.BooleanField(default=False, help_text=('User has ',
                                        'validated their account by email'))

    # User's company, university, private. Default = ``None``
    affiliation = models.CharField(max_length=255, null=True, blank=True,
                 help_text="User's affiliation: company, university, private")

    # Country: where the user is based
    country = models.CharField(max_length=255, null=True, blank=True,
                               help_text="User's country")

    # profile: a one-line profile about yourself
    bio = models.CharField(max_length=1500, null=True, blank=True,
                               help_text="A profile about yourself")

    # A user-provided URL to their own site or affiliated company
    uri = models.URLField(null=True, blank=True, verbose_name="User's URL",
       help_text='A URL to your website, affiliated company, or personal page')

    # List of tags/subject areas that describes the user's interests
    #interests = models.ManyToManyField('Tags')

    # OpenID_URI: user's optional OpenID URI
    openid = models.URLField(null=True, blank=True, max_length=255,
                             verbose_name="OpenID URL")

    # An integer ranking (in the spirit of StackOverflow)
    reputation = models.IntegerField(default=0)

    # User allows being contacted via website by other registered users
    contactable_via_site = models.BooleanField(default=True,
                            help_text = ('User allows being contacted via the '
                                         'website by other registered users'))

    # Allow/disallow user to send emails via the site; used to stop abuse
    allow_user_to_email = models.BooleanField(default=True,
                            help_text=('Allow/disallow user to send emails '
                                       'via this site'))

    class Meta:
        verbose_name_plural = 'users'

    def save(self, *args, **kwargs):
        """ Override the model's saving function to create the slug """
        # http://docs.djangoproject.com/en/dev/topics/db/models/
                                          #overriding-predefined-model-methods
        unique_slugify(self, self.user.username, 'slug')

        # TODO(KGD): ensure a user's email address is unique

        # Call the "real" save() method.
        super(UserProfile, self).save(*args, **kwargs)

    @models.permalink
    def get_absolute_url(self):
        return ('spc-user-profile', (self.user.profile.slug,))

    def __unicode__(self):
        return 'Profile for: ' + self.user.username
