from django.db import models

class Thumbs(models.Model):
    """
    Class for handling thumbs up/thumbs down voting
    """

    # Who is voting? Null for anonymous users.
    person = models.ForeignKey('scipy_central.apps.Person', null=True, blank=True)

    # submission: if voting for a submission, otherwise Null.
    submission = models.ForeignKey('scipy_central.apps.Submission', null=True,
                                   blank=True)

    # Which comment is being voted on. Can be null.
    comment = models.ForeignKey('scipy_central.apps.Comment', null=True,
                                blank=True)

    # When the vote was cast
    date_time = models.DateField(auto_now=True)

    # IP_address: for abuse prevention
    ip_address = models.IPAddressField()

    # user_agent: web browser's user agent: for abuse prevention
    user_agent = models.CharField(max_length=255)

    # vote: ``True`` is thumbs up and ``False`` is thumbs down
    vote = models.BooleanField()
