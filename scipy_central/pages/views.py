from django.shortcuts import render_to_response
from django.template import RequestContext
from django.template.loader import get_template
from django.http import HttpResponse

from scipy_central.utils import get_IP_address

from haystack.views import SearchView

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


def search(request):
    """
    Calls Haystack, but allows us to first log the search query
    """
    # Avoid duplicate logging if search request results in more than 1 page
    if 'page' not in request.GET:
        logger.info('SEARCH [%s]: %s' % (get_IP_address(request),
                                         request.GET['q']))
    return SearchView().__call__(request)


def markup_help(request):
    return not_implemented_yet(request, 39)
    #return render_to_response('pages/markup-help.html', {},
    #                          context_instance=RequestContext(request))


def csrf_failure(request, reason=''):
    """ Provides a better output to the user when they don't have cookies
    enabled on their computer.
    """
    ip = get_IP_address(request)
    logger.info('CSRF failure from %s for request "%s", coming from "%s"' %\
                (ip, request.path, request.META['HTTP_REFERER']))
    return render_to_response('pages/please-enable-cookies.html', {},
                              context_instance=RequestContext(request))


def not_implemented_yet(request, issue_number=None):
    """ Track how often users uncover items that haven't been implemented, so
    we can prioritize them
    """
    ip = get_IP_address(request)
    logger.info('Not implemented yet [%s] for request "%s"' % (ip, request.path))
    return render_to_response('pages/not-implemented-yet.html',
                              {'issue_number': issue_number},
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


