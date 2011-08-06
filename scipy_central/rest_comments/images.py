# -*- coding: utf-8 -*-
"""
Based on the sphinx.ext.extlinks.py, from the Sphinx documentation software.
BSD licensed: see http://sphinx.pocoo.org/latest/

    Extension to save typing and prevent hard-coding of base URLs in the reST
    files.

    This adds a config value called ``ext_images`` that is created like this::

       ext_images = {'image': 'http://127.0.0.1:8000/media/images/%s'}

    Now you can use e.g. :image:`201107/pic.png` in the ReST and it will create
    a link to ``http://scipy-central.org/images/201107/pic.png``.
"""
import re, os
from docutils import nodes, utils

def make_link_role(base_url, app):
    def role(typ, rawtext, text, lineno, inliner, options=None, content=None):
        text = utils.unescape(text)
        text_part = text.partition(';')
        text_rest = text_part[2].strip()
        specs = {'scaling': None, 'imgname': text_part[0],
                 'wspec': None, 'hspec': None}
        if re.search(r'(?P<scaling>\d+)', text_rest):
            specs['scaling'] = abs(float(text_rest))
            # Don't allow image sizes smaller than 15% of maximum width or
            # height. Also, not greater than 100%
            specs['scaling'] = max(15.0, min(100, specs['scaling']))

        img_dir = app.env.config.SPC['resized_image_dir'].partition(os.sep)[0]
        img_file = os.path.join(img_dir, text_part[0])
        img_obj = app.env.config.SPC['__Screenshot__'].objects.\
                                                     filter(img_file=img_file)

        if img_obj:
            img = img_obj[0]

            if specs['scaling'] and specs['scaling'] < 100.0:
                # We guaranteed that image is already either at max height
                # or max width. Since ``scaling`` is a number <= 100, we can
                # be sure that we are only shrinking the image
                specs['wspec'] = img.img_file.width * specs['scaling'] / 100.
                specs['hspec'] = img.img_file.height * specs['scaling'] / 100.

        try:
            full_url = base_url % text_part[0]
        except (TypeError, ValueError):
            env = inliner.document.settings.env
            env.warn(env.docname, 'unable to expand %s ext_images with base '
                     'URL %r, please make sure the base contains \'%%s\' '
                     'exactly once' % (typ, base_url))
            full_url = base_url + text_part[0]

        # See "docutils.parsers.rst.directives.images.py" and then ``Image``
        options = {'uri': full_url}
        if specs['wspec']:
            options['width'] = str(int(specs['wspec'])) + 'px'
        if specs['hspec']:
            options['height'] = str(int(specs['hspec'])) + 'px'

        image_node = nodes.image(full_url, **options)
        return [image_node], []
    return role

def setup_link_roles(app):
    for name, base_url in app.config.ext_images.iteritems():
        app.add_role(name, make_link_role(base_url, app))

def setup(app):
    app.add_config_value('ext_images', {}, 'env')
    app.connect('builder-inited', setup_link_roles)
