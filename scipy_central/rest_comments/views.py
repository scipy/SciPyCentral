"""
Converts user's reStructuredText input to HTML.
"""
# Standard library imports
import os, pickle, time, shutil
from StringIO import StringIO
import logging
logger = logging.getLogger('scipycentral.rest_comments')

# 3rd party (non-Django) imports
from sphinx.application import Sphinx, SphinxError

# Django import
from django.http import HttpResponse
from django.conf import settings

# Internal import
from scipy_central.utils import ensuredir

def compile_rest_to_html(raw_rest):
    """ Compiles the RST string, ``raw_RST`, to HTML.  Performs no
    further checking on the RST string.

    If it is a comment, then we don't modify the HTML with extra class info.
    But we do filter comments to disable hyperlinks.

    Also copy over generated MATH media to the correct directory on the server.
    """
    def sanitize_raw_rest(raw_rest):
        """
        Performs any sanitizing of the user's input.

        Currently performs:
        """
        # Converts '\\' to '\\\\': i.e. single slash converted to double-slash,
        #                    because Sphinx converts is back to a single slash

        out = raw_rest.replace('\\', '\\\\')

        # Replace tabs with 4 spaces: so that source code listings don't get
        # the default 8 spaces that Sphinx/docutils use.
        out = raw_rest.replace('\t', '    ')

        # Perform any other filtering here, if required.
        return out

    def call_sphinx_to_compile(working_dir):
        """
        Changes to the ``working_dir`` directory and compiles the RST files to
        pickle files, according to settings in the conf.py file.

        Returns nothing, but logs if an error occurred.
        """
        build_dir = os.path.abspath(working_dir + os.sep + '_build')
        ensuredir(working_dir)
        ensuredir(build_dir)
        status = StringIO()
        warning = StringIO()
        try:
            app = Sphinx(srcdir=working_dir, confdir=working_dir,
                         outdir = build_dir + os.sep + 'pickle',
                         doctreedir = build_dir + os.sep + 'doctrees',
                         buildername = 'pickle',
                         status = status,
                         warning = warning,
                         freshenv = True,
                         warningiserror = False,
                         tags = [])

            # Call the ``pickle`` builder
            app.build()

        except SphinxError as error:
            if warning.tell():
                warning.seek(0)
                for line in warning.readlines():
                    logger.warn('COMMENT: ' + line)

            msg = (('Sphinx error occurred when compiling comment '
                    '(error type = %s): %s'  % (error.category, str(error))))
            raise(msg)

        if app.statuscode != 0:
            logger.error("Non-zero status code when compiling.")

    # Ensure the directory where Sphinx will compile the ReST actually exists
    ensuredir(settings.COMMENT_COMPILE_DIR)
    modified_rest = sanitize_raw_rest(raw_rest)
    with open(settings.COMMENT_COMPILE_DIR + os.sep + 'index.rst', 'w') as fh:
        fh.write(modified_rest)

    try:
        # Does a ``conf.py`` file exist there?
        conf_file = settings.COMMENT_COMPILE_DIR + os.sep + 'conf.py'
        conf_file_hdl = file(conf_file, 'r')
    except IOError:
        # Use a fresh copy of the ``conf.py`` file, found in the current
        # directory, and copy it to comment destination.
        cf = os.path.abspath(__file__ + os.sep + os.path.pardir) + \
                                                      os.sep + 'sphinx-conf.py'
        shutil.copyfile(cf, settings.COMMENT_COMPILE_DIR + os.sep + 'conf.py')
    else:
        conf_file_hdl.close()

    # Compile the comment
    call_sphinx_to_compile(settings.COMMENT_COMPILE_DIR)

    pickle_f = ''.join([settings.COMMENT_COMPILE_DIR, os.sep, '_build', os.sep,
                        'pickle', os.sep, 'index.fpickle'])
    with open(pickle_f, 'r') as fhand:
        obj = pickle.load(fhand)

    return obj['body'].encode('utf-8')

def rest_to_html_ajax(request, field_name='rst_comment'):
    """
    The user has typed in a comment and wants to preview it in HTML.
    """
    if request.method != 'GET':
        return HttpResponse('', status=404)

    # Response back to user, if everything goes OK
    response = HttpResponse(status=200)
    response['SPC-comment'] = 'Comment-OK'

    start_time = time.time()
    rst_comment = request.GET[field_name]
    logger.debug("Compile:: %s" % rst_comment)
    html_comment = compile_rest_to_html(rst_comment)
    end_time = time.time()
    if (end_time-start_time) > 3:
        logger.warning(('Comment compile time exceeded 3 seconds; server'
                          'load too high?'))

    logger.debug("Successfully compiled user's comment.")
    return HttpResponse(html_comment, status=200)

