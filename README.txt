Prerequisites
-------------

Please ensure these Python packages are available on your server:

*   http://djangoproject.com: ``easy_install -U pygments`

    We developed on Django 1.3.0; earlier versions may also work.

*   `Pygments <http://pygments.org>`_: ``easy_install -U pygments``

    We used version 1.4 during development; earlier versions may also work.


Not required yet (might be as we add more functionality to the site):

*   Python Imaging Library (for screenshot handling)
*   easy_install python-openid

Installation
--------------

After Django installation and cloning this git repository on your server:

#.	``./manage.py syncdb``
#.	``./manage.py loaddata sample``


Attribution
-----------

Code from other BSD-licensed applications has been used in this project, and
attributed at the point of use. In summary though, we have used code from:

* `django-taggit <https://github.com/alex/django-taggit>`_
* `djangosnippets.org <https://github.com/coleifer/djangosnippets.org>`_


