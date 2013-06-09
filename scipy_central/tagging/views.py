from django.http import HttpResponse
from django.utils import simplejson
from django.template.defaultfilters import slugify
from django.utils.encoding import force_unicode
from django.core.exceptions import ValidationError

import models
from scipy_central.submission.models import TagCreation

import datetime
from collections import defaultdict


def get_tag_uses(start_date=None, end_date=None):
    """
    Returns a list of tuples of the form:  [(n_uses, Tag.pk), ....]
    This allows one to use the builtin ``list.sort()`` function where Python
    orders the list based on the first entry in the tuple.

    The list will be returned in the order of the ``Tag.pk``, but the
    first tuple entry is the number of uses of that tag, allowing for easy
    sorting using Python's ``sort`` method.
    """
    if start_date is None:
        start_date = datetime.date.min
    if end_date is None:
        end_date = datetime.date.max

    tags_created = TagCreation.objects.all().\
                                       filter(date_created__gte=start_date).\
                                       filter(date_created__lte=end_date)

    # Let all the revisions from each submission be grouped, so that duplicate
    # tags across revisions only have a single influence
    uses_by_sub_pk = defaultdict(set)
    for use in tags_created:
        uses_by_sub_pk[use.revision.entry_id].add(use.tag)

    # Then for each set of tags in each submission, iterate a create a dict
    # where the keys are the tag's primary key and the values are the number
    # of uses of that tag
    uses_by_pk = defaultdict(int)
    for tag_set in uses_by_sub_pk.itervalues():
        for tag in tag_set:
            uses_by_pk[tag.pk] += 1

    # Finally, create a list of hit counts, which can be used for sorting
    hit_counts = []
    for key, val in uses_by_pk.iteritems():
        hit_counts.append((val, key))

    return hit_counts


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
    buffer_list = []
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
                if buffer_list:
                    to_be_split.append(u''.join(buffer_list))
                    buffer_list = []
                # Find the matching quote
                open_quote = True
                c = i.next()
                while c != u'"':
                    buffer_list.append(c)
                    c = i.next()
                if buffer_list:
                    word = u''.join(buffer_list).strip()
                    if word:
                        words.append(word)
                    buffer_list = []
                open_quote = False
            else:
                if not saw_loose_comma and c == u',':
                    saw_loose_comma = True
                buffer_list.append(c)
    except StopIteration:
        # If we were parsing an open quote which was never closed treat
        # the buffer_list as unquoted.
        if buffer_list:
            if open_quote and u',' in buffer_list:
                saw_loose_comma = True
            to_be_split.append(u''.join(buffer_list))
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


def get_and_create_tags(tagstring):

    tag_list = []
    for tag in parse_tags(tagstring):
        try:
            tag_obj = models.Tag.objects.get_or_create(name=tag)[0]
        except ValidationError:
            pass
        else:
            # Does the tag really exist or was it found because of the lack of
            # case sensitivity (e.g. "2D" vs "2d"
            if tag_obj.id is None:
                tag_obj = models.Tag.objects.get(slug=slugify(tag))

            tag_list.append(tag_obj)

    return tag_list


def tag_autocomplete(request):
    """
    Filters through all available tags to find those starting with, or
    containing the string ``contains_str``.

    Parts from http://djangosnippets.org/snippets/233/
    """
    # TODO(KGD): cache this lookup for 30 minutes
    # Also, randomize the tag order to prevent only the those with lower
    # primary keys from being shown more frequently

    # TODO(KGD): put the typed text in bold, e.g. typed="bi" then return
    # proba<b>bi</b>lity
    all_tags = [tag.name for tag in models.Tag.objects.all()]

    contains_str = request.REQUEST.get('term', '').lower()

    starts = []
    includes = []
    for item in all_tags:
        index = item.lower().find(contains_str)
        if index == 0:
            starts.append(item)
        elif index > 0:
            includes.append(item)

    # Return tags starting with ``contains_str`` at the top of the list,
    # followed by tags that only include ``contains_str``
    starts.extend(includes)
    return HttpResponse(simplejson.dumps(starts), mimetype='text/text')
