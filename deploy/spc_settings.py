# SciPy Central (SPC)
#
# This dictionary defines settings that modify the behaviour of the entire
# website.


SPC = {
    # Delete unconfirmed submission after this number of days
    'unvalidated_subs_deleted_after': 7,

    # We only support Mercurial at the moment. Code can support git and
    # other version control systems in the future.
    # Do not change this once files have been added.
    'revisioning_backend': 'hg',

    # Where should files be stored?
    'storage': parent_dir + os.sep + 'deploy' + os.sep + 'code' + os.sep
}
