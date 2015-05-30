from django.db import models
from django.conf import settings
from scipy_central import utils

from dvcs_wrapper import DVCSError, DVCSRepo
# Python imports
import os
import logging
import shutil
import json
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

        utils.ensuredir(os.path.join(storage_dir, self.repo_path))
        super(FileSet, self).save(*args, **kwargs)


    def create_empty(self):
        """
        Create an empty repo (``init``) and returns it.
        """
        repo = DVCSRepo(backend, os.path.join(storage_dir, self.repo_path), do_init=True,
                        dvcs_executable=revisioning_executable)
        # Save the location for next time
        globals()['revisioning_executable'] = repo.executable
        return repo


    def add_file_from_string(self, filename, list_strings, commit_msg='',
                                 user=None):
        """
        Add a ``filename`` to the repo using the list of strings to create
        the file. A commit will be written to the repo is ``commit_msg`` is not
        empty.
        """
        fname = os.path.join(storage_dir, self.repo_path, filename)
        f = open(fname, 'w')
        f.writelines(list_strings)
        f.close()

        repo = DVCSRepo(backend, os.path.join(storage_dir, self.repo_path),
                             dvcs_executable=revisioning_executable)
        # Save the location for next time
        globals()['revisioning_executable'] = repo.executable

        # Only add this file
        try:
            repo.add([fname])
        except DVCSError as e:
            # Happens if a file with the same name already exists in the repo
            if e.value == 'Could not add one or more files to repository.':
                pass
            else:
                raise

        if commit_msg:
            repo.commit(commit_msg, user=user)


    def add_file(self, pattern, commit_msg='', user=None, repo=None):
        """
        Add a single file, or a file ``pattern``, to the repo.
        A commit will be written to the repo if ``commit_msg`` is not empty.
        """
        if repo is None:
            repo = DVCSRepo(backend, os.path.join(storage_dir, self.repo_path),
                            do_init=False,
                            dvcs_executable=revisioning_executable)


        try:
            repo.add([pattern])
        except DVCSError as e:
            logger.error('DVCS error: %s' % e.original_message)


        if commit_msg:
            repo.commit(commit_msg, user=user)


    def get_hash(self):
        """
        Returns the current repo hash for this fileset
        """
        repo = DVCSRepo(backend, os.path.join(storage_dir, self.repo_path),
                            do_init=False,
                            dvcs_executable=revisioning_executable)
        return repo.get_revision_info()[0:60]


    def get_repo(self):
        """
        Returns the DVCS repo object
        """
        return DVCSRepo(backend, os.path.join(storage_dir, self.repo_path),
                         dvcs_executable=revisioning_executable)


    def checkout_revision(self, hash_id):
        """ Set the repo state to the revision given by ``hash_id``

        Equivalent, for e.g., to ``hg checkout 28ed0c6faa19`` for that hash_id.
        """
        repo = DVCSRepo(backend, os.path.join(storage_dir, self.repo_path),
                    do_init=False,
                    dvcs_executable=revisioning_executable)
        hash_str = repo.check_out(hash_id)
        if hash_str==hash_id:
            return repo
        else:
            return None


    def list_iterator(self):
        """
        Returns a list of all files in a repo. For example, if the repo has:
            /dir1/abc.png
            /dir1/def.png
            /dir2/            <-- empty dir
            /dir3/dir4/frg.png
            /dir3/tyr.png
            ghw.png
            yqr.png

        This function will return Python dictionary data structure:
        {
            "test": [
                {
                    "dir1": [ "abc.txt","def.txt"]
                },
                {
                    "dir2": []
                },
                {
                    "dir3": [
                        {
                            "dir4": ["frg.txt"]
                        },
                        "tyr.txt"
                    ]
                },
                "fil1.txt",
                "fil2.txt"
            ]
        }
        """
        def path_to_dict(root):
            if not os.path.isdir(root):
                return os.path.split(root)[1]
            pdic = {}
            pdic[os.path.split(root)[1]] = [path_to_dict(os.path.join(root, x)) for x in os.listdir(root) \
                                            if x not in settings.SPC['common_rcs_dirs']]
            return pdic

        base_dir = os.path.join(storage_dir, self.repo_path)
        return json.dumps(path_to_dict(base_dir))
        
    def __unicode__(self):
        return '<storage_dir>/' + self.repo_path
