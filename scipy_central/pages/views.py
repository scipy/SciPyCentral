from django.shortcuts import render_to_response
from django.template import RequestContext

import logging
logger = logging.getLogger('scipycentral')
logger.debug('Initializing pages::views.py')

def front_page(request):
    return render_to_response('pages/front-page.html', {},
                              context_instance=RequestContext(request))
def about_page(request):
    return render_to_response('pages/about-page.html', {},
                              context_instance=RequestContext(request))

def licence_page(request):
    return render_to_response('pages/about-licenses.html', {},
                              context_instance=RequestContext(request))