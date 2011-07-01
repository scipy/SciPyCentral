from django.shortcuts import render_to_response
from django.template import RequestContext
from django.template.loader import get_template
from django.http import HttpResponse


from scipy_central.utils import get_IP_address

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

def page_404_error(request):
    """ Override Django's 404 handler, because we want to log this also.
    """
    ip = get_IP_address(request)
    logger.info('404 from %s for request "%s"' % (ip, request.path))
    t = get_template('404.html')
    html = t.render(RequestContext(request))
    return HttpResponse(html, status=404)

def page_500_error(request):
    """ Override Django's 500 handler, because we want to log this also.
    """
    ip = get_IP_address(request)
    logger.error('500 from %s for request "%s"' % (ip, request.path))
    t = get_template('500.html')
    html = t.render(RequestContext(request))
    return HttpResponse(html, status=500)


