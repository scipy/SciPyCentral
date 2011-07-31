from django.conf import settings

# Inpsired by
# https://github.com/ericflo/django-avatar/blob/master/avatar/settings.py

try:
    from PIL import Image
except ImportError:
    import Image

IMG_RESIZE_METHOD = getattr(settings, 'IMG_RESIZE_METHOD', Image.ANTIALIAS)
IMG_MAX_SIZE = getattr(settings, 'IMG_MAX_SIZE', 700)
IMG_QUALITY = getattr(settings, 'IMG_QUALITY', 85)
IMG_DEFAULT_FORMAT = getattr(settings, 'IMG_DEFAULT_FORMAT', "JPEG")
IMG_ACCEPTABLE_FORMATS = getattr(settings, 'IMG_ACCEPTABLE_FORMATS', ["JPG",
                                                                      "PNG"])
