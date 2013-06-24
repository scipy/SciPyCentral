from django.http import HttpResponse, Http404
from django.utils import simplejson
import models

from scipy_central.screenshot.forms import ScreenshotForm

def add_screenshot(request):
    """
    Received POST request to add a new screenshot.
    """
    if not (request.method == 'POST' and \
        request.user.is_authenticated() ):
      raise Http404

    img_form = ScreenshotForm(request.POST, request.FILES)
    if img_form.is_valid():

        # Somehow (not sure how yet) the file name is slugified, so that there
        # will never be characters such as ";", "#", "&" etc in the names
        # We benefit from that by allowing the magnifier setting to be
        # specified after a ";" character.
        try:
          img = models.Screenshot(img_file_raw=img_form.\
                                                cleaned_data['spc_image_upload'])
          img.save()
          msg = ('Upload successful. Insert the image in your description as'
                 '&nbsp;&nbsp;&nbsp; <tt>:image:`%s`</tt><br>'
                 '<br>'
                 '<i>Want a smaller image? e.g. scaled down to 40%%:</i> '
                 '&nbsp;<tt>:image:`%s;40`</tt><br>') %\
                              (img.img_file_raw.name.partition('/')[2],
                               img.img_file_raw.name.partition('/')[2])
        except Exception, e:
          msg = 'Error on server, please try again \n' + str(e)

        return HttpResponse(msg)

    else:
        msg = ('<div class="alert alert-error">%s</div>') % img_form.errors.get('spc_image_upload')[0]
        return HttpResponse(msg)
