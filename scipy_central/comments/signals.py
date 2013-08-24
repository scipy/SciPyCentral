import logging
from django.conf import settings
from django.core.mail import EmailMessage, BadHeaderError
from django.dispatch import receiver
from django.template import Context
from django.template.loader import get_template
from django.contrib.comments.signals import comment_was_flagged
from django.contrib.auth.models import User

logger = logging.getLogger('scipycentral')
logger.debug('Initializing comments::signals.py')

@receiver(comment_was_flagged)
def comment_after_flag_callback(signal, **kwargs):
    """
    Method receives signal after a flag has been posted.
    This method has to be loaded before hand for not missing any signals.
    So, its imported into __init__

    Description:
        Email all 'CommentModerators' group after a user flagged comment
    """
    try:
        comment = kwargs['comment']
        flag = kwargs['flag']
        context_var = {
            'flag_author': flag.user.username,
            'flag_date': flag.flag_date,
            'flag_pk': flag.pk,
            'comment_author': comment.user.username,
            'comment_url': comment.get_absolute_url(),
            'comment_pk': comment.pk,
            'comment_submit_date': comment.submit_date,
            'prev_flagged': kwargs['created'],
            'comment_msg': comment.comment,
            'team_email': settings.SCIPY_CENTRAL_TEAM,
        }
        mail_template = get_template('comments/comment-after-flag-email.html')
        mail = mail_template.render(Context(context_var))
        to_email = [user.email for user in User.objects.filter(groups__name='CommentModerators')]
        try:
            EmailMessage('Comment Flags', mail, to_email).send()
        except BadHeaderError:
            logger.error('Unable to email CommentModerators')

    except (KeyError, IndexError):
        logger.error('Error while sending email to CommentModerators')
