from django.contrib.auth.models import User, UserManager
from django.db import models
from scipy_central.utils import unique_slugify

import re
# alphanumerics, underscores, spaces, @, . and -
VALID_USERNAME = re.compile('^[\w @.-]*$', re.UNICODE)

class UserProfile(User):
    """
    We are extending Django's built-in authentication. See
    http://scottbarnham.com/blog/2008/08/21/extending-the-django-user-model-
                                                            with-inheritance/
    for guidance.
    """
    # Use UserManager to get the create_user method, etc.
    objects = UserManager()

    # Inherited field entries:

    # username: 30 characters, alphanumeric, underscores, spaces, $, . and -
    #           see ``VALID_USERNAME`` regular expression

    # email: an email address

    # password: a salted and hashed password

    username_slug = models.SlugField(editable=False)

    # i.e. the user's identity has been verified by a challenge/response email
    is_validated = models.BooleanField(default=False, help_text=('User has ',
                                        'validated their account by email'))

    #``is_active``: Django field: set to False to disable user, rather than
    # deleting all their info. This is to keep their previous contributions
    # from disappearing. We can also completely delete user and all their
    # contributions.

    # User's company, university, private. Default = ``None``
    affiliation = models.CharField(max_length=255, null=True, blank=True,
                 help_text="User's affiliation: company, university, private")

    # Country: where the user is based
    country = models.CharField(max_length=255, null=True, blank=True,
                               help_text="User's country")

    # profile: a one-line profile about yourself
    profile = models.CharField(max_length=150, null=True, blank=True,
                               help_text="A one-line profile about yourself")

    # avatar: user uploaded image, or obtained via Gravatar
    # Upload to MEDIA_ROOT + 'avatars'
    #avatar = models.ImageField(upload_to = ..., max_length=255,

    # A user-provided URL to their own site or affiliated company
    uri = models.URLField(null=True, blank=True, verbose_name="User's URL",
       help_text='A URL to your website, affiliated company, or personal page')

    # Number of times the user's profile has been viewed
    n_views = models.IntegerField(default=0,
                                  verbose_name="Number of profile views")

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

    @models.permalink
    def get_absolute_url(self):
        return ('scipycentral-user-profile', [self.username_slug])

    def save(self, *args, **kwargs):
        """ Override the model's saving function to create the slug """
        # http://docs.djangoproject.com/en/dev/topics/db/models/
                                          #overriding-predefined-model-methods
        unique_slugify(self, self.username, 'username_slug')

        # Call the "real" save() method.
        super(UserProfile, self).save(*args, **kwargs)

