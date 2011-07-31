"""
Converts user's reStructuredText input to HTML.
"""
# Standard library imports
import os, pickle, time, shutil, re
from StringIO import StringIO
import logging
logger = logging.getLogger('scipycentral')

# 3rd party (non-Django) imports
from sphinx.application import Sphinx, SphinxError

# Django import
from django.http import HttpResponse
from django.conf import settings

# Internal import
from scipy_central.utils import ensuredir

# We need certain files in place to compile the comments
# Copy the settings, image extension, and an __init__.py to the appropriate
# places. The original copy of the ``conf.py`` file, found in the current
# directory (copy it to comment destination)

working_dir = settings.SPC['comment_compile_dir']
ext_dir = os.path.abspath(working_dir + os.sep + 'ext')
ensuredir(working_dir)
ensuredir(ext_dir)

cf = os.path.abspath(__file__ + os.sep + os.path.pardir) + \
                                          os.sep + 'sphinx-conf.py'
shutil.copyfile(cf, settings.SPC['comment_compile_dir'] + os.sep +\
                                                            'conf.py')

cf = os.path.abspath(__file__ + os.sep + os.path.pardir) + \
                                                  os.sep + 'images.py'
shutil.copyfile(cf, settings.SPC['comment_compile_dir'] + os.sep +\
                                        'ext' + os.sep + 'images.py')

cf = os.path.abspath(__file__ + os.sep + os.path.pardir) + \
                                                  os.sep + '__init__.py'
shutil.copyfile(cf, settings.SPC['comment_compile_dir'] + os.sep +\
                                        'ext' + os.sep + '__init__.py')


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
        * Converts string to utf-8 encoding
        * Converts '\\' to '\\\\': i.e. single slash converted to double-slash,
                            because Sphinx converts is back to a single slash
        * Removes hyperlinks to remote images

        Alternative way to prevent csv-table directive, raw directive,
        include directive: if using docutils.
        For more, see: http://docutils.sourceforge.net/docs/user/config.html#file-insertion-enabled
        """

        raw_rest = raw_rest.encode('utf-8')

        # Required: so that things like \( a = \frac{b}{c} \) works as
        # expected, otherwise users have to write  \\ a = \\frac{b}{c} \\)
        raw_rest = raw_rest.replace('\\', '\\\\')


        # Replace tabs with 4 spaces: so that source code listings don't get
        # the default 8 spaces that Sphinx/docutils use.
        raw_rest = raw_rest.replace('\t', '    ')

        raw_rest = raw_rest.split('\r\n')

        # Strip  '.. raw::'' directive
        raw = re.compile(r'^(\s*)..(\s*)raw(\s*)::(\s*)')
        math_env = re.compile(r':math:`(.+?)`')
        for idx, line in enumerate(raw_rest):
            if raw.match(line):
                raw_rest[idx] = ''

            # Fix double \\\\ in :math:` ... `
            outline = ''
            last_pos = 0
            for math_str in math_env.finditer(line):
                outline += line[last_pos:math_str.start()+7]
                outline += math_str.group(1).replace('\\\\', '\\')
                outline += '`'
                last_pos = math_str.end()

            outline += line[last_pos:]
            raw_rest[idx] = outline


        # Remove hyperlinks to remote items: e.g. .. include:: http://badstuff.com
        NO_REMOTE = ['literalinclude', 'include', 'csv-table']
        for item in NO_REMOTE:
            remote_re = re.compile(r'^(\s*)..(\s*)' + item + r'(\s*)::(\s*)http')
            for idx, line in enumerate(raw_rest):
                if remote_re.match(line):
                    raw_rest[idx] = ''


        return '\r\n'.join(raw_rest)

    def call_sphinx_to_compile(working_dir):
        """
        Changes to the ``working_dir`` directory and compiles the RST files to
        pickle files, according to settings in the conf.py file.

        Returns nothing, but logs if an error occurred.
        """
        build_dir = os.path.abspath(working_dir + os.sep + '_build')
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
            app.build(force_all=True)

        except SphinxError as error:
            if warning.tell():
                warning.seek(0)
                for line in warning.readlines():
                    logger.warn('COMMENT: ' + line)

            msg = (('Sphinx error occurred when compiling comment '
                    '(error type = %s): %s'  % (error.category, str(error))))
            logger.error(msg)
            raise SphinxError(msg)

        if app.statuscode != 0:
            logger.error("Non-zero status code when compiling.")

    # Ensure the directory where Sphinx will compile the ReST actually exists
    ensuredir(settings.SPC['comment_compile_dir'])
    logger.debug('SPHINX: ' + raw_rest)
    modified_rest = sanitize_raw_rest(raw_rest)
    with open(settings.SPC['comment_compile_dir'] + os.sep + 'index.rst',
                                                                   'w') as fh:
        fh.write(modified_rest)


    # Compile the comment
    call_sphinx_to_compile(settings.SPC['comment_compile_dir'])

    pickle_f = ''.join([settings.SPC['comment_compile_dir'], os.sep,
                        '_build', os.sep, 'pickle', os.sep, 'index.fpickle'])
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

