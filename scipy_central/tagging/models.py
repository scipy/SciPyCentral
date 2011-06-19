from django.db import models

class Tag(models.Model):
    """
    A tag object: each revision can be have several tags. All tags must have
    a unique slug name.
    """
    TAG_TYPES = (
        ('subject', 'Tags that define a broad subject area (more weight)'),
        ('regular', 'A regular tag'),
    )

    # Name used for URLs and tag blocks
    slug = models.SlugField(unique=True)

    # Show this longer name when user hovers their mouse
    name = models.TextField(max_length=50)

    # We may decide to have a page for each tag, where we show these
    # descriptions
    description = models.CharField(max_length=255, blank=True, null=True)
    # and perhaps an image
    image = models.ImageField(upload_to='tags/', blank=True)

    # Tags can be of two types
    tag_type = models.TextField(max_length=10, choices=TAG_TYPES,
                                default='regular')


    def __unicode__(self):
        return self.name