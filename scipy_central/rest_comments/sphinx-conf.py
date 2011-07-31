# -*- coding: utf-8 -*-
#
# DO NOT REMOVE.  This file is used as the "conf.py" file to convert web user
# comments in ReST to HTML.
#
# The user's ReST is written to index.rst, and converted to HTML using the
# settings listed here.
#
# -- General configuration -----------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be extensions
# coming with Sphinx (named 'sphinx.ext.*') or your custom ones.
# Ensure that what ever extensions you add here cannot be maliciously used
# against your website if carefully crafted ReST is entered into the comments
extensions = ['sphinx.ext.mathjax', 'sphinx.ext.extlinks']
mathjax_path = ("http://cdn.mathjax.org/mathjax/latest/MathJax.js?"
                "config=TeX-AMS-MML_HTMLorMML")

# Allows for inline markup as: :tag:`gui`.
# TODO(KGD): modify the extlinks function so the <a..> link can have a class
# set, for CSS styling
extlinks = {'id': ('http://scipy-central.org/item/%s', 'item #'),
            'user': ('http://scipy-central.org/user/%s', 'user #'),
            'tag': ('http://scipy-central.org/item/tag/%s', 'tag: ')}


# Add our own extension for images
import sys, os
sys.path.insert(0, os.path.abspath('.'))
extensions.append('ext.images')
ext_images = {'image': 'http://127.0.0.1:8000/media/images/%s'}

# The suffix of source filenames.
source_suffix = '.rst'

# The master toctree document.
master_doc = 'index'

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
exclude_patterns = ['_build']

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = 'sphinx'

# -- Options for HTML output ---------------------------------------------------

# The theme to use for HTML and HTML Help pages.  Major themes that come with
# Sphinx are currently 'default' and 'sphinxdoc'.
html_theme = 'default'

# Permalinks (those strange characters next to headings)
html_add_permalinks = None