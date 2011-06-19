from django.db import models
from django.template.defaultfilters import slugify
from django.utils.encoding import force_unicode

import logging
logger = logging.getLogger('scipycentral')
logger.debug('Initializing tagging::models.py')

def parse_tags(tagstring):
    """
    Parses tag input, with multiple word input being activated and
    delineated by commas and double quotes. Quotes take precedence, so
    they may contain commas.

    Returns a sorted list of unique tag names.

    Ported from Jonathan Buchanan's `django-tagging
    <http://django-tagging.googlecode.com/>`_

    SPC: took this code from:
        https://github.com/alex/django-taggit/blob/master/taggit/utils.py
    """
    if not tagstring:
        return []

    tagstring = force_unicode(tagstring)

    # SPC: removing this: we require commas to separate multiword tags
    # Special case - if there are no commas or double quotes in the
    # input, we don't *do* a recall... I mean, we know we only need to
    # split on spaces.
    #if u',' not in tagstring and u'"' not in tagstring:
        #words = list(set(split_strip(tagstring, u' ')))
        #words.sort()
        #return words

    if u',' not in tagstring and u'"' not in tagstring:
        tagstring += ','

    words = []
    buffer = []
    # Defer splitting of non-quoted sections until we know if there are
    # any unquoted commas.
    to_be_split = []
    saw_loose_comma = False
    open_quote = False
    i = iter(tagstring)
    try:
        while True:
            c = i.next()
            if c == u'"':
                if buffer:
                    to_be_split.append(u''.join(buffer))
                    buffer = []
                # Find the matching quote
                open_quote = True
                c = i.next()
                while c != u'"':
                    buffer.append(c)
                    c = i.next()
                if buffer:
                    word = u''.join(buffer).strip()
                    if word:
                        words.append(word)
                    buffer = []
                open_quote = False
            else:
                if not saw_loose_comma and c == u',':
                    saw_loose_comma = True
                buffer.append(c)
    except StopIteration:
        # If we were parsing an open quote which was never closed treat
        # the buffer as unquoted.
        if buffer:
            if open_quote and u',' in buffer:
                saw_loose_comma = True
            to_be_split.append(u''.join(buffer))
    if to_be_split:
        if saw_loose_comma:
            delimiter = u','
        else:
            delimiter = u' '
        for chunk in to_be_split:
            words.extend(split_strip(chunk, delimiter))
    words = list(set(words))
    words.sort()
    return words

def split_strip(string, delimiter=u','):
    """
    Splits ``string`` on ``delimiter``, stripping each resulting string
    and returning a list of non-empty strings.

    Ported from Jonathan Buchanan's `django-tagging
    <http://django-tagging.googlecode.com/>`_

    SPC: took this code from:
        https://github.com/alex/django-taggit/blob/master/taggit/utils.py
    """
    if not string:
        return []

    words = [w.strip() for w in string.split(delimiter)]
    return [w for w in words if w]

class Tag(models.Model):
    """
    A tag object: each revision can be have several tags. All tags must have
    a unique slug name.
    """
    TAG_TYPES = (
        ('subject', 'Tags that define a broad subject area (more weight)'),
        ('regular', 'A regular tag'),
    )

    # Name used for URLs and tag blocks
    slug = models.SlugField(unique=True, editable=False)

    # Show this longer name when user hovers their mouse
    name = models.TextField(max_length=50)

    # We may decide to have a page for each tag, where we show these
    # descriptions
    description = models.CharField(max_length=255, blank=True, null=True)
    # and perhaps an image
    image = models.ImageField(upload_to='tags/', blank=True)

    # Tags can be of two types
    tag_type = models.TextField(max_length=10, choices=TAG_TYPES,
                                default='regular')

    def __unicode__(self):
        return self.name

    def save(self, *args, **kwargs):
        """ Slug is a primary key: don't save a new tag if one already exists.
        """
        slug = slugify(self.name)
        if Tag.objects.filter(slug=slug):
            return
        else:
            # Call the "real" save() method.
            self.slug = slug
            logger.info('TAGS: created a new tag: %s', slug)
            super(Tag, self).save(*args, **kwargs)