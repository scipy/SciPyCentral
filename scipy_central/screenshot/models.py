from django.db import models
from PIL import Image
from django.core.files import File

class Screenshot(models.Model):
    """ Screenshot model. Forces the screeshot to the dimensions,
    and also creates a thumbnail.
    """

    img_file_raw = models.ImageField(upload_to='screenshots/%Y/%m/%d',
                                 max_length=255, blank=True, null=True,
                                 verbose_name="Screenshot",
                        help_text=('Provide, if possible, a screenshot of '
                                   'what your code might produce as output. '
                                   'E.g a histogram, image, etc'))
    img_file = models.ImageField(upload_to='screenshots/%Y/%m/%d')

    def save(self, *args, **kwargs):
        """ Override the model's saving function to resize the screenshot"""

        # TODO(KGD): create a 128x128 thumbnail image that is displayed in site


        # From: http://djangosnippets.org/snippets/978/
        #def resize_image(content, size):

        #img = Image.open(get_file(content))
        #if img.size[0] > size['width'] or img.size[1] > size['height']:
            #if size['force']:
                #target_height = float(size['height'] * img.size[WIDTH]) / size['width']
                #if target_height < img.size[HEIGHT]: # Crop height
                    #crop_side_size = int((img.size[HEIGHT] - target_height) / 2)
                    #img = img.crop((0, crop_side_size, img.size[WIDTH], img.size[HEIGHT] - crop_side_size))
                #elif target_height > img.size[HEIGHT]: # Crop width
                    #target_width = float(size['width'] * img.size[HEIGHT]) / size['height']
                    #crop_side_size = int((img.size[WIDTH] - target_width) / 2)
                    #img = img.crop((crop_side_size, 0, img.size[WIDTH] - crop_side_size, img.size[HEIGHT]))
            #img.thumbnail((size['width'], size['height']), Image.ANTIALIAS)
            #out = StringIO()
            #try:
                #img.save(out, optimize=1)
            #except IOError:
                #img.save(out)
            #return out
        #else:
            #return content


        # Call the "real" save() method.
        super(Screenshot, self).save(*args, **kwargs)


