# SciPy Central (SPC)
#
# This dictionary defines settings that modify the behaviour of the entire
# website.
#
# Variables available to you in this file are the same as those available in
# ``settings.py``.

SPC = {
    # Delete unconfirmed submission after this number of days
    'unvalidated_subs_deleted_after': 7,

    # We only support Mercurial at the moment. Code can support git and
    # other version control systems in the future.
    # Do not change this once files have been added.
    'revisioning_backend': 'hg',

    # Can be left as '', but then we will search for the executable everytime
    # we need to access the repo. Rather specify the full path to the
    # revision control system executable.
    'revisioning_executable': '',

    # Where should files from each submission be stored?
    # Files are stored using revision control in directories as follows:
    #
    # <storage><submission_primary_key>/<submission_slug>.py
    # <storage><submission_primary_key>/LICENSE.txt
    # where <storage> is the variable defined next, as should always end
    # with ``os.sep``
    'storage_dir': MEDIA_ROOT + 'code' + os.sep
}
