from scipy_central.thumbs.models import Thumbs
from django.db.models.signals import pre_save, post_save, pre_delete, post_delete
from django.dispatch import receiver
import logging

logger = logging.getLogger("scipycentral")
logger.debug("Initializing Thumbs::signals.py")

def perform_score(thumb_obj):
    ct_obj = thumb_obj.content_object
    if hasattr(ct_obj, "score"):
        ct_obj.score = ct_obj.set_score()
        ct_obj.save()

def perform_reputation(thumb_obj, prev_vote, created):
    ct_obj = thumb_obj.content_object
    # update `reputation` field
    ct_obj.reputation = ct_obj.calculate_reputation(
        vote=thumb_obj.vote,
        prev_vote=prev_vote
    )
    ct_obj.save()

@receiver(pre_save, sender=Thumbs)
def update_reputation(sender, instance, **kwargs):
    """
    Signal receiver function to update `reputation`
    field in Models.

    `thumb_obj` is valid by default. May be we might want to 
    allow admins to approve newbie votes via email where is_valid=False
    for them. This value has to be set to True in this receiver function
    """
    created, prev_vote = True, None
    if instance.pk:
        prev_vote = Thumbs.objects.get(pk=instance.pk).vote
        created = False
    if instance.vote == prev_vote:
        instance.vote = None
    perform_reputation(instance, prev_vote, created)

@receiver(post_save, sender=Thumbs)
def update_wilson_score(sender, instance, **kwargs):
    perform_score(instance)

@receiver(pre_delete, sender=Thumbs)
def remove_reputation(sender, instance, using, **kwargs):
    """
    The method is triggered when `Thumbs` object is deleted.
    The reputation field of content_object is updated
    once the object is set to delete
    """
    created = False
    prev_vote = instance.vote
    instance.vote = None
    perform_reputation(instance, prev_vote, created)

@receiver(post_delete, sender=Thumbs)
def remove_wilson_score(sender, instance, **kwargs):
    """
    Update wilson score after deleting object
    """
    perform_score(instance)
