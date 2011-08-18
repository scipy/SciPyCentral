from django.template.defaultfilters import slugify
from django.conf import settings
from django.core.mail import send_mail, BadHeaderError
from django.core.paginator import Paginator, InvalidPage, EmptyPage

from pygments import formatters, highlight, lexers

import re, os, errno, logging
logger = logging.getLogger('scipy_central')

rest_help_extra = """Use <a href="http://sphinx.pocoo.org/latest/rest.html">reStructuredText</a>.
<div class="spc-markup-help"><ul>
<li class="spc-odd">Use linebreaks between paragraphs</li>
<li class="spc-even"><tt>*</tt><i>italics</i><tt>*</tt> and <tt>**</tt><b>bold</b><tt>**</tt></li>
<li class="spc-odd"><tt>`Hyperlinks &lt;http://example.com&gt;`_</tt></li>
<li class="spc-even"><tt>``monospaced text``</tt></li>
<li class="spc-odd"><tt>\(</tt><tt>e^{i \pi}+1=0</tt><tt>\)</tt> shows as \(e^{i \pi}+1=0\)</li>
<li class="spc-even"><a href="/markup-help" target="_blank">More help</a> with bulleted lists, math, hyperlinks and other features</li>
</div>"""


def ensuredir(path):
    """Ensure that a path exists."""
    # Copied from sphinx.util.osutil.ensuredir(): BSD licensed code, so it's OK
    # to add to this project.
    EEXIST = getattr(errno, 'EEXIST', 0)
    try:
        os.makedirs(path)
    except OSError, err:
        # 0 for Jython/Win32
        if err.errno not in [0, EEXIST]:
            raise


def get_IP_address(request):
    """
    Returns the visitor's IP address as a string given the Django ``request``.
    """
    # Catchs the case when the user is on a proxy
    ip = request.META.get('HTTP_X_FORWARDED_FOR', '')
    if ip == '' or ip.lower() == 'unkown':
        ip = request.META.get('REMOTE_ADDR', '')   # User is not on a proxy
    return ip

# From: http://djangosnippets.org/snippets/690/
def unique_slugify(instance, value, slug_field_name='slug', queryset=None,
                   slug_separator='-'):
    """
    Calculates and stores a unique slug of ``value`` for an instance.

    ``slug_field_name`` should be a string matching the name of the field to
    store the slug in (and the field to check against for uniqueness).

    ``queryset`` usually doesn't need to be explicitly provided - it'll default
    to using the ``.all()`` queryset from the model's default manager.
    """
    slug_field = instance._meta.get_field(slug_field_name)

    slug = getattr(instance, slug_field.attname)
    slug_len = slug_field.max_length

    # Sort out the initial slug, limiting its length if necessary.
    slug = slugify(value)
    if slug_len:
        slug = slug[:slug_len]
    slug = _slug_strip(slug, slug_separator)
    original_slug = slug

    # Create the queryset if one wasn't explicitly provided and exclude the
    # current instance from the queryset.
    if queryset is None:
        queryset = instance.__class__._default_manager.all()
    if instance.pk:
        queryset = queryset.exclude(pk=instance.pk)

    # Find a unique slug. If one matches, at '-2' to the end and try again
    # (then '-3', etc).
    next = 2
    while not slug or queryset.filter(**{slug_field_name: slug}):
        slug = original_slug
        end = '%s%s' % (slug_separator, next)
        if slug_len and len(slug) + len(end) > slug_len:
            slug = slug[:slug_len-len(end)]
            slug = _slug_strip(slug, slug_separator)
        slug = '%s%s' % (slug, end)
        next += 1

    setattr(instance, slug_field.attname, slug)


def _slug_strip(value, separator='-'):
    """
    Cleans up a slug by removing slug separator characters that occur at the
    beginning or end of a slug.

    If an alternate separator is used, it will also replace any instances of
    the default '-' separator with the new separator.
    """
    separator = separator or ''
    if separator == '-' or not separator:
        re_sep = '-'
    else:
        re_sep = '(?:-|%s)' % re.escape(separator)
    # Remove multiple instances and if an alternate separator is provided,
    # replace the default '-' separator.
    if separator != re_sep:
        value = re.sub('%s+' % re_sep, separator, value)
    # Remove separator from the beginning and end of the slug.
    if separator:
        if separator != '-':
            re_sep = re.escape(separator)
        value = re.sub(r'^%s+|%s+$' % (re_sep, re_sep), '', value)
    return value


def highlight_code(code):
    """ Uses Pygments to provide syntax highlighting.
    """
# See this page for help with colouring: http://pygments.org/docs/tokens/
#
#from pygments.styles.default import DefaultStyle
#from pygments.style import Style
#from pygments.styles import get_style_by_name
#from pygments.token import Comment, Keyword, Name, String, Operator, Number
#from pygments import formatters
#class SciPyStyle(Style):
    #default_style = ""
    #styles = {
        ##Comment:                '#888',
        ##Keyword:                'bold #080',
        ##Name:                   '#080',
        ##Name.Function:          '#00F',
        ##Name.Class:             'bold #00F',
        ##String:                 '#BA2121',
        #Comment:                '#008000',
        #Keyword:                'bold #000080',
        #Name:                   '#000',
        #Name.Builtin:           '#407090',
        #Name.Function:          'bold #008080',
        #Name.Class:             'bold #00F',
        #Name.Namespace:         '#000000',
        #Number:                 '#008080',
        #String:                 '#800080',
        #String.Doc:             '#800000',
        #Operator:               '#000000',
        #Operator.Word:          'bold #AA22FF',
    #}

#formatter = formatters.HtmlFormatter(style=SciPyStyle)
#print(formatter.get_style_defs('.highlight'))

    if code is None:
        return None
    else:
        return highlight(code, lexers.PythonLexer(),
                                      formatters.HtmlFormatter(linenos=True,
                                                               linenostep=1,))


def send_email(to_addresses, subject, message, from_address=None):
    """
    Basic function to send email according to the four required string inputs.
    Let Django send the message; it takes care of opening and closing the
    connection, as well as locking for thread safety.
    """
    if from_address is None:
        from_address = settings.SERVER_EMAIL

    if subject and message and from_address:
        try:
            send_mail(subject, message, from_address, to_addresses,
                      fail_silently=True)
        except BadHeaderError:
            logger.error(('An error occurred when sending email to %s, with'
                          'subject [%s]') % (str(to_addresses), subject))


def paginated_queryset(request, queryset):
    """
    Show items in a paginated table.
    """
    queryset = list(queryset)
    paginator = Paginator(queryset, settings.SPC['entries_per_page'])
    try:
        page = int(request.GET.get('page', '1'))
    except ValueError:
        page = 1
    try:
        return paginator.page(page)
    except (EmptyPage, InvalidPage):
        return paginator.page(paginator.num_pages)


