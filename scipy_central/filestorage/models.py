from django.db import models
from django.conf import settings
from scipy_central import utils
from dvcs_wrapper import DVCSError, DVCSRepo
# Python imports
import os
import logging

storage_dir = settings.SPC['storage_dir']
backend = settings.SPC['revisioning_backend']
revisioning_executable = settings.SPC['revisioning_executable']

logger = logging.getLogger('scipycentral')
logger.debug('Initializing filestorage::models.py')

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

        utils.ensuredir(storage_dir + self.repo_path)
        super(FileSet, self).save(*args, **kwargs)

    def create_empty(self):
        """
        Create an empty repo (``init``)
        """
        repo = DVCSRepo(backend, storage_dir + self.repo_path, do_init=True,
                        dvcs_executable=revisioning_executable)
        # Save the location for next time
        globals()['revisioning_executable'] = repo.executable


    def add_file_from_string(self, filename, list_strings, commit_msg='',
                                 user=None):
        """
        Add a ``filename`` to the repo using the list of strings to create
        the file. A commit will be written to the repo is ``commit_msg`` is not
        empty.
        """
        fname = storage_dir + self.repo_path + filename
        f = open(fname, 'w')
        f.writelines(list_strings)
        f.close()

        repo = DVCSRepo(backend, storage_dir + self.repo_path,
                             dvcs_executable=revisioning_executable)
        # Save the location for next time
        globals()['revisioning_executable'] = repo.executable

        # Only add this file
        try:
            repo.add(fname)
        except DVCSError as e:
            # Happens if a file with the same name already exists in the repo
            if e.value == 'Could not add one or more files to repository.':
                pass
            else:
                raise

        if commit_msg:
            repo.commit(commit_msg, user=user)


    def add_file(self, filename, commit_msg='', user=None):
        """
        Add a sequence of file to the repo

        A commit will be written to the repo is ``commit_msg`` is not
        empty.
        """
        repo = DVCSRepo(backend, storage_dir + self.repo_path, do_init=False,
                        dvcs_executable=revisioning_executable)

        # Only add this file
        try:
            repo.add(filename)
        except DVCSError as e:
            logger.error('DVCS error: %s' % e.original_message)


        if commit_msg:
            repo.commit(commit_msg, user=user)

    def __unicode__(self):
        return '<storage_dir>/' + self.repo_path

