"""
Converts user's reStructuredText input to HTML.
"""
# Standard library imports
import os, pickle, time, shutil, re, tempfile
from StringIO import StringIO
import logging
logger = logging.getLogger('scipycentral')

# 3rd party (non-Django) imports
from sphinx.application import Sphinx, SphinxError

# Django import
from django.contrib.sites.models import Site
from django.http import HttpResponse
from django.conf import settings
from django import template

# Internal import
from scipy_central.utils import ensuredir
from scipy_central.screenshot.models import Screenshot


def setup_compile_dir(compile_dir):
    """
    Setup a directory for Sphinx compilation.

    We need certain files in place to compile the comments Copy the
    settings, image extension, and an __init__.py to the appropriate
    places. The original copy of the ``conf.py`` file, found in the
    current directory (copy it to comment destination)
    """

    if Site._meta.installed:
        site = Site.objects.get_current().domain
    else:
        site = ''

    module_dir = os.path.dirname(__file__)

    ext_dir = os.path.abspath(os.path.join(compile_dir, 'ext'))
    ensuredir(compile_dir)
    ensuredir(ext_dir)

    conf_template_file = os.path.join(module_dir, 'sphinx-conf.py')
    conf_file = os.path.join(compile_dir, 'conf.py')

    with file(conf_template_file, 'r') as f:
        conf_template = template.Template(f.read())

    if settings.MEDIA_URL.startswith('http'):
        conf = conf_template.render(template.Context({'FULL_MEDIA_URL':
                                                      settings.MEDIA_URL}))
    else:
        conf = conf_template.render(template.Context({'FULL_MEDIA_URL':
                                                      site + settings.MEDIA_URL}))

    with file(conf_file, 'w') as f:
        f.write(conf)

    fn = os.path.join(module_dir, 'images.py')
    shutil.copyfile(fn, os.path.join(compile_dir, 'ext', 'images.py'))

    fn = os.path.join(module_dir, '__init__.py')
    shutil.copyfile(fn, os.path.join(compile_dir, 'ext', '__init__.py'))

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
        math_role = re.compile(r':math:`(.+?)`')
        math_env = re.compile(r'^\s*.. math::*')
        math_lines = []
        for idx, line in enumerate(raw_rest):
            if raw.match(line):
                raw_rest[idx] = ''

            if math_env.match(line):
                math_lines.append(idx)

            # Fix double \\\\ in :math:` ... `
            outline = ''
            last_pos = 0
            for math_str in math_role.finditer(line):
                outline += line[last_pos:math_str.start()+7]
                outline += math_str.group(1).replace('\\\\', '\\')
                outline += '`'
                last_pos = math_str.end()

            outline += line[last_pos:]
            raw_rest[idx] = outline

        # Are there math environments we need to remove "\\" from?
        for _, line_num in enumerate(math_lines):
            # From http://ucomment.org
            prefix_re = re.compile('^\s*')
            prefix_match = prefix_re.match(raw_rest[line_num])
            prefix = prefix_match.group()

            # Search down to find where the math environment ends
            finished = False
            next_line = ''
            end_line = line_num + 1
            for idx, line in enumerate(raw_rest[line_num+1:]):
                end_line += 1
                bias = idx + 2
                if line.strip() == '':
                    # Keep looking further down
                    for _, next_line in enumerate(raw_rest[line_num+bias:]):
                        if next_line.strip() != '':
                            finished = True
                            break

                if finished:
                    next_prefix = prefix_re.match(next_line.rstrip('\n')).group()

                    # Break if a non-blank line has the same, or lower indent
                    # level than the environment's level (``prefix``)
                    if len(next_prefix.expandtabs()) <= len(prefix.expandtabs()):
                        break
                    else:
                        finished = False

            # All done: replace the \\\\ with \\
            for i, math_str in enumerate(raw_rest[line_num:end_line]):
                math_str = math_str.replace('\\\\', '\\')
                raw_rest[i+line_num] = math_str



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
        working_dir = os.path.abspath(working_dir)
        build_dir = os.path.join(working_dir, '_build')
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

            # We need to access some settings while inside Sphinx
            # This is the easiest way to get them there
            app.env.config.SPC = settings.SPC
            app.env.config.SPC['__Screenshot__'] = Screenshot

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

    # Create a directory where Sphinx will compile the ReST
    ensuredir(settings.SPC['comment_compile_dir'])
    compile_dir = tempfile.mkdtemp(dir=settings.SPC['comment_compile_dir'])
    try:
        setup_compile_dir(compile_dir)
        logger.debug('SPHINX: ' + raw_rest)
        modified_rest = sanitize_raw_rest(raw_rest)
        with open(os.path.join(compile_dir, 'index.rst'), 'w') as fh:
            fh.write(modified_rest)

        # Compile the comment
        call_sphinx_to_compile(compile_dir)

        pickle_f = os.path.join(compile_dir, '_build', 'pickle', 'index.fpickle')
        with open(pickle_f, 'rb') as fhand:
            obj = pickle.load(fhand)
    finally:
        shutil.rmtree(compile_dir)

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
