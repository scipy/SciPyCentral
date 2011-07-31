# -*- coding: utf-8 -*-
"""
Based on the sphinx.ext.extlinks.py, from the Sphinx documentation software.
BSD licensed: see http://sphinx.pocoo.org/latest/

    Extension to save typing and prevent hard-coding of base URLs in the reST
    files.

    This adds a new config value called ``ext_images`` that is created like this::

       ext_images = {'image': 'http://127.0.0.1:8000/media/images/%s'}

    Now you can use e.g. :image:`201107/pic.png` in the ReST and it will create
    a link to ``http://scipy-central.org/images/201107/pic.png``.
"""

from docutils import nodes, utils

from sphinx.util.nodes import split_explicit_title


def make_link_role(base_url):
    def role(typ, rawtext, text, lineno, inliner, options={}, content=[]):
        text = utils.unescape(text)
        has_explicit_title, title, part = split_explicit_title(text)
        try:
            full_url = base_url % part
        except (TypeError, ValueError):
            env = inliner.document.settings.env
            env.warn(env.docname, 'unable to expand %s ext_images with base '
                     'URL %r, please make sure the base contains \'%%s\' '
                     'exactly once' % (typ, base_url))
            full_url = base_url + part

        # See "docutils.parsers.rst.directives.images.py" and then ``Image``
        options = {'uri': full_url}
        image_node = nodes.image(full_url, **options)
        return [nodes.paragraph(), image_node, nodes.paragraph()], []
    return role

def setup_link_roles(app):
    for name, base_url in app.config.ext_images.iteritems():
        app.add_role(name, make_link_role(base_url))

def setup(app):
    app.add_config_value('ext_images', {}, 'env')
    app.connect('builder-inited', setup_link_roles)
