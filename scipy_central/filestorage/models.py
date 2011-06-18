from django.db import models
from django.conf import settings
from scipy_central import utils
import dvcs_wrapper as dvcs
# Python imports
import os

storage_dir = settings.SPC['storage_dir']
backend = settings.SPC['revisioning_backend']
revisioning_executable = settings.SPC['revisioning_executable']

class FileSet(models.Model):
    """
    Every file-based submission is stored under revision control. This class
    defines where those files are stored, creates that storage, and has
    class methods to add files to the storage location.
    """

    # Where will the files be stored. Path name should always end with a slash
    repo_path = models.CharField(max_length=500)
    created = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        """ Override the model's saving function to ensure the repo dir is
        created. """

        utils.ensuredir(self.repo_path)
        super(FileSet, self).save(*args, **kwargs)

    def add_file_from_string(self, filename, list_strings, commit_msg=''):
        """
        Add a ``filename`` to the repo using the list of strings to create
        the file. An automatic commit message will be created, unless provided.
        """
        if not commit_msg:
            commit_msg = 'AUTO: added %s to repo.' % filename

        fname = self.repo_path + filename
        f = open(fname, 'w')
        f.writelines(list_strings)
        f.close()

        repo = dvcs.DVCSRepo(backend, self.repo_path,
                             dvcs_executable=revisioning_executable)
        repo.add('.')
        repo.commit(commit_msg)
        # Save the location for next time
        globals()['revisioning_executable'] = repo.executable

