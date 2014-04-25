=============
Scipy Central
=============

This is the web app serving http://scipy-central.org/, a source code
snippet sharing site.


Development setup
=================

Quick start
-----------

To set up a development environment quickly, you can install the Virtualenv
package (https://pypi.python.org/pypi/virtualenv) and then run::

    python quickstart.py

This will create a virtualenv under deploy/env and download, use easy_install
to get correct versions of prerequisites from the Internet, and finally run the
initial database setup.


Prerequisites
-------------

The minimal set of required Python packages and package versions is
listed in ``requirements.txt``. See http://pypi.python.org/ for the
package downloads.

You can also install the required packages automatically with the
command::

    pip install -r requirements.txt --use-mirrors

or, on Windows, by running::

    easy_install "Django >=1.4,<1.5" (...rest of the lines...)

For searching, you can optionally use Xapian instead of Whoosh:

* See the installation instructions at
  http://django-haystack.readthedocs.org/en/latest/installing_search_engines.html

  Installation in a hosted environment will require more work.

* You also need Xapian-haystack: ``pip install xapian-haystack``


Installation
------------

* Clone the SciPy Central code repository:

    ``git clone https://github.com/scipy/SciPyCentral.git``

* Ensure the following Django settings are in your ``settings.py`` file:

  * ``CSRF_FAILURE_VIEW = 'scipy_central.pages.views.csrf_failure'``
  * ``ROOT_URLCONF = 'deploy.urls'``
  * ``INSTALLED_APPS`` contains these apps:

    * ``'django.contrib.auth'``
    * ``'django.contrib.contenttypes'``
    * ``'django.contrib.sessions'``
    * ``'django.contrib.sites'``
    * ``'django.contrib.messages'``
    * ``'django.contrib.staticfiles'``
    * ``'django.contrib.admin'``
    * ``'django.contrib.admindocs'``
    * ``'django.contrib.humanize'``
    * ``'haystack'``
    * ``'registration'``
    * ``'south'``
    * ``'widget_tweaks'``
    * ``'scipy_central.filestorage'``
    * ``'scipy_central.pages'``
    * ``'scipy_central.person'``
    * ``'scipy_central.submission'``
    * ``'scipy_central.tagging'``
    * ``'scipy_central.screenshot'``
    * ``'scipy_central.pagehit'``

  * ``AUTH_PROFILE_MODULE = 'person.UserProfile'``
  * ``ACCOUNT_ACTIVATION_DAYS = 7``
  * ``REGISTRATION_OPEN = True``
  * ``LOGIN_URL = '/user/login/'``
  * ``SPC = { ... }``: see which key-value pairs are required by examing
    the code in the ``settings.py`` file that is part of the SciPy
    Central code repository.
  * ``JQUERY_URL = '...'``
  * ``JQUERYUI_URL = '...'``
  * ``JQUERYUI_CSS = '...'``
  * ``ANALYTICS_SNIPPET = '...'``
  * ``LOGGING = {...}``: you need a logger called ``scipycentral``, see
    more information at http://docs.djangoproject.com/en/dev/topics/logging
    and also see the ``settings.py`` file that is part of the SciPy
    Central code repository.

* To make changes in design
  * Require `less>=1.4.1` for compiling LESS files to css
  * Follow readme.rst in `./deploy/media/less/` for more information

Run::

    ./manage.py syncdb
    ./manage.py migrate            # to run the ``south`` db migrations
    ./manage.py loaddata base      # to load licenses, tags and other basic data
    ./manage.py loaddata sample    # to load a few sample submissions
    ./manage.py rebuild_index      # to rebuild the Haystack search index
    ./manage.py update_index


Backup and restore
------------------

There are 4 components to backup:

1. Database: use ``deploy/backup_site.py``
2. Repositories: use ``rsync`` and mirror ``SPC['storage_dir']``
   directory that you set in ``settings.py``
3. Raw image files: rsync the ``SPC['raw_image_dir']``
4. Resized images: rsync the ``SPC['resized_image_dir']``

To restore:

1. Delete your existing database.

2. Run: ``./manage.py syncdb`` to create the empty tables in the database.

3. ``./manage.py migrate`` to run the ``south`` db migrations

4. ``./manage.py reset contenttypes`` to remove the ``contenttypes``
   objects created by ``syncdb``, which will inevitibly clash with those
   restored from the database dump (in the next step). See
   http://stackoverflow.com/questions/853796/problems-with-contenttypes-when-loading-a-fixture-in-django

5. ``./manage.py loaddata backup-YYYY-MM-DD-HH-MM-SS.json``
   which restores the json database dump created by ``backup_site.py`` in
   step 1 of the backup procedure.

6. Do a full mirror of the rsynced repositories to your new
   ``SPC['storage_dir']`` location. This storage contains hidden
   directories (.hg or .git directories).

7. Similarly, restore the mirror of the resized images (the raw images
   may optionally be restored).


Attribution
-----------

Code from other BSD-licensed applications has been used in this project, and
attributed at the point of use. In summary though, we have used code from:

* `django-taggit <https://github.com/alex/django-taggit>`_
* `djangosnippets.org <https://github.com/coleifer/djangosnippets.org>`_
* `django-registration <https://bitbucket.org/ubernostrum/django-registration/>`_
* `django-avatar <https://github.com/ericflo/django-avatar>`_
* `Sphinx <http://sphinx.pocoo.org/latest/>`)
* `Ace Editor <http://ace.c9.io/>`_

The jQuery Forms extensions is MIT licensed (compatible with BSD);
more information at http://malsup.com/jquery/form/

The Rss Feed icon is taken from Wikipedia and its licensed under GNU
GPL v2, GNU LGPL v2.1, Mozilla Public License v1.1 and is described at
https://en.wikipedia.org/w/index.php?title=File:Feed-icon.svg&oldid=453635063#License
