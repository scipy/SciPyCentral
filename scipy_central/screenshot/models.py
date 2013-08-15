from django.db import models
from django.conf import settings
from django.core.files import base
from django.utils import timezone
from django.utils.encoding import force_unicode, smart_str
from settings import (IMG_MAX_WIDTH, IMG_MAX_HEIGHT, IMG_QUALITY,
                      IMG_RESIZE_METHOD, IMG_DEFAULT_FORMAT,
                      IMG_ACCEPTABLE_FORMATS)

from PIL import Image
import os
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

class Screenshot(models.Model):
    """ Screenshot model. Forces the screeshot to the dimensions,
    and also creates a thumbnail.
    """
    #help_text=('Provide, if possible, a screenshot of '
    #           'what your code might produce as output. '
    #           'E.g a histogram, image, etc'))

    date_added = models.DateTimeField(auto_now=True)
    img_file_raw = models.ImageField(upload_to=settings.SPC['raw_image_dir'],
                                     max_length=1024)
    img_file = models.ImageField(upload_to=settings.SPC['resized_image_dir'],
                                 max_length=1024)


    def __unicode__(self):
        return self.img_file_raw.name

    def save(self, *args, **kwargs):
        """ Override the model's saving function to resize the screenshot
        """
        # Code inspired by:
        # https://github.com/ericflo/django-avatar/blob/master/avatar/models.py

        # Create image that are no more than 700 pixels wide
        # for use in the website
        self.img_file_raw.seek(0)
        orig = self.img_file_raw.read()
        image = Image.open(StringIO(orig))
        if image.format in IMG_ACCEPTABLE_FORMATS:
            format_used = image.format
        else:
            format_used = IMG_DEFAULT_FORMAT

        (w, h) = image.size
        if w > IMG_MAX_WIDTH:
            h = int(h*IMG_MAX_WIDTH/(w+0.0))
            w = IMG_MAX_WIDTH
            if image.mode != "RGB" and image.mode != "RGBA":
                image = image.convert("RGB")
            image = image.resize((w, h), IMG_RESIZE_METHOD)
            thumb = StringIO()
            image.save(thumb, format_used, quality=IMG_QUALITY)
            thumb_file = base.ContentFile(thumb.getvalue())
        if h > IMG_MAX_HEIGHT:
            w = int(w*IMG_MAX_HEIGHT/(h+0.0))
            h = IMG_MAX_HEIGHT
            if image.mode != "RGB" and image.mode != "RGBA":
                image = image.convert("RGB")
            image = image.resize((w, h), IMG_RESIZE_METHOD)
            thumb = StringIO()
            image.save(thumb, format_used, quality=IMG_QUALITY)
            thumb_file = base.ContentFile(thumb.getvalue())
        else:
            thumb_file = base.ContentFile(orig)

        dirname = force_unicode(timezone.now().strftime(
            smart_str(settings.SPC['resized_image_dir'])))
        location = os.path.normpath(dirname + self.img_file_raw.name)
        self.img_file = self.img_file.storage.save(location, thumb_file)

        super(Screenshot, self).save(*args, **kwargs)
