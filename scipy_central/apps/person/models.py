from django.contrib.auth.models import User
from django.db import models
from scipy_central.apps.utils import unique_slugify
from registration.backends.default import DefaultBackend
from django.contrib.sites.models import Site
from django.contrib.sites.models import RequestSite
from registration import signals
from registration.models import RegistrationProfile
import hashlib

class SciPyRegistrationBackend(DefaultBackend):

    def register(self, request, **kwargs):
        """
        Given a username, email address and password, register a new
        user account, which will initially be inactive.

        Along with the new ``User`` object, a new
        ``registration.models.RegistrationProfile`` will be created,
        tied to that ``User``, containing the activation key which
        will be used for this account.

        An email will be sent to the supplied email address; this
        email should contain an activation link. The email will be
        rendered using two templates. See the documentation for
        ``RegistrationProfile.send_activation_email()`` for
        information about these templates and the contexts provided to
        them.

        After the ``User`` and ``RegistrationProfile`` are created and
        the activation email is sent, the signal
        ``registration.signals.user_registered`` will be sent, with
        the new ``User`` as the keyword argument ``user`` and the
        class of this backend as the sender.

        """
        username, email, password = kwargs['username'], kwargs['email'], kwargs['password1']
        if Site._meta.installed:
            site = Site.objects.get_current()
        else:
            site = RequestSite(request)

        # We are creating a user with the same email address. We have already
        # verified in ``forms.py`` that this isn't a mistake. Go ahead and pull
        # the existing user from the DB and return that user instead.
        if User.objects.filter(email__iexact=email):
            new_user = User.objects.filter(email__iexact=email)[0]
            new_user.username = username
            new_user.set_password(password)
            new_user.save()

            # Resave their profile also (updates the slug)
            new_user_profile = UserProfile.objects.get(user=new_user)
            new_user_profile.save()

            # Complete the activation email part
            registration_profile = RegistrationProfile.objects.create_profile(new_user)
            registration_profile.send_activation_email(site)
        else:

            new_user = RegistrationProfile.objects.create_inactive_user(\
                                               username, email,password, site)

        signals.user_registered.send(sender=self.__class__,
                                     user=new_user,
                                     request=request)
        return new_user


class Country(models.Model):
    """ Model for a country """
    # Country's official name
    name = models.CharField(max_length=255, help_text="Official country name",
                            unique=True)

    # The 2-character code: http://en.wikipedia.org/wiki/ISO_3166-1_alpha-2
    code = models.CharField(max_length=2, help_text="Country code",
                            unique=True)

    def __unicode__(self):
        return self.name


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
                 help_text=("Your <b>affiliation</b> (company name, "
                            "university name, or private)"))

    # Country: where the user is based
    country = models.ForeignKey(Country, null=True, blank=True,
                               help_text="Your <b>country</b>")

    # profile: a profile about yourself
    bio = models.TextField(null=True, blank=True,
                                 help_text="A <b>profile</b> about yourself")

    bio_html = models.TextField(editable=False, null=True, blank=True)

    # A user-provided URL to their own site or affiliated company
    uri = models.URLField(null=True, blank=True, verbose_name="User's URL",
       help_text='A URL to <b>your website</b>, affiliated company, or personal page')

    # List of tags/subject areas that describes the user's interests
    interests = models.ManyToManyField('tagging.Tag', through='InterestCreation')

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

        # Call the "real" save() method.
        super(UserProfile, self).save(*args, **kwargs)

    @models.permalink
    def get_absolute_url(self):
        return ('spc-user-profile', (), {'slug': self.user.profile.slug})

    def get_gravatar_image(self):
        email_hash = hashlib.md5(self.user.email).hexdigest()
        gravatar_url = "http://www.gravatar.com/avatar/"
        return gravatar_url + email_hash

    def __unicode__(self):
        return 'Profile for: ' + self.user.username


class InterestCreation(models.Model):
    """
    Tracks by whom and when tags were created
    """
    user = models.ForeignKey(UserProfile)
    tag = models.ForeignKey('tagging.Tag')
    date_created = models.DateTimeField(auto_now_add=True, editable=False)

    def __unicode__(self):
        return self.tag.name
