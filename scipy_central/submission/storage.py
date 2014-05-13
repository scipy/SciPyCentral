# django imports
from django.conf import settings
from django.template import Context, Template
from django.template.loader import render_to_string
from django.template.defaultfilters import slugify

# SciPy Central imports
from scipy_central.filestorage.models import FileSet
from scipy_central.utils import ensuredir
from scipy_central.submission import models

# python imports
import logging
import zipfile
import datetime
import shutil
import os

logger = logging.getLogger('scipycentral')
logger.debug('Initializing submission::storage.py')

def get_repo_path(rev_object):
    """
    Creates a new repo path based on `pk` value of `rev_object`
    If the path name already exists, it is appended by `_count_of_path`
    """
    timestamp = datetime.datetime.now()
    repo_path = os.path.join(timestamp.strftime('%Y'), timestamp.strftime('%m'),
                             '%06d' % rev_object.pk)
    # if by chance the path exists
    # append name by `_number` and increment `number` until it does not exist
    path = repo_path
    count = 1
    while os.path.exists(os.path.join(settings.SPC['storage_dir'], path)):
        path = repo_path + '_%d' % count
        count += 1

    return path

def copy_package_file(package_file, dst):
    """
    `package_file` is an in-memory file object created by django
    `dst` is destination file path.

    If object size > 2MB (default limit), it is first stored
    in a temporary directory by django
    """
    destination = open(dst, 'wb+')
    for chunk in package_file.chunks():
        destination.write(chunk)
    destination.close()


class SubmissionStorage(object):
    """
    Class used to handle storage of submissions in file system.
    It is assumed that the application alreay established connection
    with storage directory (or disk) and has all necessary permissions.

    The storage directory is recommended to handle with this class
    """
    def store(self):
        """
        Wrapper method to handle operations

        If is_new is True, creates a new repository or else commit new
        changes in the exisiting repository.
        """
        if self.is_new:
            return self.__create_new_submission()
        else: 
            return self.__create_revision()
        
    def __create_revision(self):
        """
        Creates revision to an existing submission
        """
        # get or create repo
        repo = self.object.entry.fileset.get_repo()

        # commit revision
        if self.object.entry.sub_type == 'snippet':
            snippet_name = self.object.slug.replace('-', '_') + '.py'
            commit_msg = ('Update of file(s) in the repo based on the web submission by'
                          'user "%s"' % (self.object.created_by.username))
            return self.__commit_snippet(snippet_name, self.object.item_code, commit_msg)

        elif self.object.entry.sub_type == 'package':
            # explicit validation is required as revision object does not have
            # `package_file` attribute and is only passed for easy usage instead of passing
            # `form` object!
            if not hasattr(self.object, 'package_file'):
                raise AttributeError('Uploaded file not passed to revision object')

            repo_path = self.object.entry.fileset.repo_path
            full_repo_path = os.path.join(settings.SPC['storage_dir'], repo_path)

            # if not new - has an exisiting repo from previous revision
            # delete all data except revision backend dir
            revision_backend_dir = '.' + settings.SPC['revisioning_backend']
            for path, dirs, files in os.walk(full_repo_path):
                # ignore dir
                if revision_backend_dir in dirs:
                    dirs.remove(revision_backend_dir)
                # remove files in path
                for name in files:
                    os.remove(os.path.join(path, name))
                # remove dirs in path
                for name in dirs:
                    shutil.rmtree(os.path.join(path, name))
            
            # remove deleted files from repo
            repo.remove(['--after'])

            commit_msg = 'Update files from web-uploaded ZIP file, DESCRIPTION.txt'

            return self.__commit_package(self.object.package_file, commit_msg)
            
        else:
            raise TypeError('Unknown submission type')

    def __create_new_submission(self):

        """
        New submission is created
        """
        self.__create_repo()

        if self.object.entry.sub_type == 'snippet':
            snippet_name = slugify(self.object.title).replace('-', '_') + '.py'
            commit_msg = ('Add "%s" to the repo based on the web submission by user "%s"'
                          % (snippet_name, self.object.created_by.username))
            return self.__commit_snippet(snippet_name, self.object.item_code, commit_msg)

        elif self.object.entry.sub_type == 'package':
            if not hasattr(self.object, 'package_file'):
                raise AttributeError('Upload file not passed to revision object')

            commit_msg = 'Add files from web-uploaded ZIP file, DESCRIPTION.txt'
            return self.__commit_package(self.object.package_file, commit_msg)
        else:
            raise TypeError('Unknown submission type')

    def __commit_package(self, package_file, commit_msg):
        """
        Adds files in `package_file` to the repository

        1. The `package_file` object is copied to repo path
        2. All files except repo dirs (.hg, .git, .svn etc) are extracted
        3. DESCRIPTION.txt, LICENSE.txt files are added
        4. Changes committed to repo

        raises DVCSError if new files contain no changes from the existing
        ones
        """
        repo_path = self.object.entry.fileset.repo_path
        full_repo_path = os.path.join(settings.SPC['storage_dir'], repo_path)

        # copy package file to repo
        dst = os.path.join(full_repo_path, package_file.name)
        copy_package_file(package_file, dst)

        # unzip package file
        zip_obj = zipfile.ZipFile(dst, 'r')
        for file_name in zip_obj.namelist():
            # ignore revision backend dirs if present
            # zipfile.ZipFile object ensures seperators are '/'
            base_dir = file_name.split('/')[0]
            if not base_dir in settings.SPC['common_rcs_dirs']:
                zip_obj.extract(zip_obj.getinfo(file_name), full_repo_path)
        zip_obj.close()

        # delete zip file
        os.remove(dst)

        # commit package files
        repo_obj = self.object.entry.fileset.get_repo()
        for path, dirs, files in os.walk(full_repo_path):
            # exclude revision backend dir
            if os.path.split(path)[1] == '.' + settings.SPC['revisioning_backend']:
                for entry in dirs[:]:
                    dirs.remove(entry)
                continue

            all_files = []
            for name in files:
                all_files.append(os.path.join(path, name))

            if all_files:
                repo_obj.add(patterns=all_files, ignore_errors=True)

        # add `description.txt` file
        description_name = os.path.join(full_repo_path, 'DESCRIPTION.txt')
        description_file = file(description_name, 'wb')
        description_file.write(self.object.description)
        description_file.close()

        self.object.entry.fileset.add_file(description_name,
                                           user=self.object.created_by.get_absolute_url(),
                                           commit_msg=commit_msg)

        # add license file
        license_text = self.__get_license_text()
        self.object.entry.fileset.add_file_from_string(settings.SPC['license_filename'],
                                                       license_text, user='SciPy Central',
                                                       commit_msg='SPC: add/update license file')

        # log info
        logger.info('SubmissionStorage:: Commit package to the repo: '
                    'Repo [dir=%s] Revision [pk=%d] User [pk=%d]' 
                    % (repo_path, self.object.pk, self.object.created_by.pk))

        # hash id 
        return self.object.entry.fileset.get_hash()

    def __commit_snippet(self, snippet_name, snippet_text, commit_msg):
        """
        Add snippet text to the repository

        1. Create a file named `snippet_name` with `snippet_text` in it
        2. Add LICENSE.txt to the repo
        3. Commit changes to the repo
        """
        self.object.entry.fileset.add_file_from_string(snippet_name, snippet_text,
                                                       user=self.object.created_by.get_absolute_url(),
                                                       commit_msg=commit_msg)

        # commit license file
        license_text = self.__get_license_text()
        self.object.entry.fileset.add_file_from_string(settings.SPC['license_filename'],
                                                       license_text, user='SciPy Central',
                                                       commit_msg='SPC: add/update license file')

        
        # log info
        logger.info('SubmissionStorage:: Commit snippet to the repo: '
                    'Repo [dir=%s] Revision [pk=%d] User [pk=%d]' 
                    % (self.object.entry.fileset.repo_path, self.object.pk, 
                       self.object.created_by.pk))

        # hash id
        return self.object.entry.fileset.get_hash()

    def __create_repo(self):
        """
        Create empty repository for the fileset object
        """
        if not isinstance(self.object.entry.fileset, FileSet):
            raise TypeError('FileSet object not passed to fileset attribute')

        repo_path = self.object.entry.fileset.repo_path
        ensuredir(os.path.join(settings.SPC['storage_dir'], repo_path))
        repo = self.object.entry.fileset.create_empty()

        # log info
        logger.info('SubmissionStorage:: Created an empty repository: '
                    'Path [dir=%s] Revision [pk=%d] User [pk=%d]' 
                    % (repo_path, self.object.pk, self.object.created_by.pk))
        return repo

    def revert(self, hash_id=None):
        """
        Revert changes made. returns `True` if reverted,
        `False` if not due to any errors.
        """
        fileset = self.object.entry.fileset

        is_reverted = True
        if self.is_new:
            full_repo_path = os.path.join(settings.SPC['storage_dir'], fileset.repo_path)

            # Delete repo path if exists
            if os.path.exists(full_repo_path):
                try:
                    shutil.rmtree(full_repo_path)
                    # log the operation
                    logger.error('SubmissionStorage:: Removed created repo on error')
                except (WindowsError, OSError, IOError), e:
                    # log the error 
                    logger.critical('SubmissionStorage:: Unable to remove repo on error %s' % e)
                    is_reverted = False
        else:
            if not isinstance(hash_id, (str, unicode)):
                raise TypeError('hash_id argument should be str if `is_new` is False')

            repo = fileset.get_repo()
            try:
                # remove all untracked changes
                # Note: need to turn on `purge` extension in hg
                repo.purge()

                # go back to previous commit
                repo.update(['-r%s' % hash_id])

                # log the operation
                logger.error('SubmissionStorage:: Revert repo changes on error')
            except RuntimeError, e:
                # log the error
                logger.critical('SubmissionStorage:: Unable to revert changes in repo %s' % e)
                is_reverted = False

        return is_reverted

    def __get_license_text(self):
        """
        Generates and returns the license text for the given revision. Uses these
        revision and authorship information from previous revisions, if necessary,
        to create the license.
        """
        slug = self.object.sub_license.slug
        if slug == 'cc0':
            license_cc0 = Template(self.object.sub_license.text_template).render(Context())
            sub_license = render_to_string('submission/license-cc0.txt',
                                           {'obj': self.object, 'license_cc0': license_cc0,
                                            'url_domain': settings.SPC['short_URL_root']})
            return sub_license

        elif slug == 'bsd':
            license_bsd = Template(self.object.sub_license.text_template).render(
                Context({
                    'year': datetime.datetime.now().year,
                    'copyright_holder': settings.SPC['short_URL_root'] + \
                                        self.object.created_by.get_absolute_url()
                }))
            sub_license = render_to_string('submission/license-bsd.txt',
                                           {'obj': self.object, 'license_bsd': license_bsd,
                                            'url_domain': settings.SPC['short_URL_root']})
            return sub_license
        else:
            raise NotImplementedError('%s license is not yet implemented' % slug)

    def __init__(self, revision, is_new):
        """
        self.object is instance of `Revision` object
        self.is_new is `True` if for new submission or `False` if not
        """
        self.object = revision
        self.is_new = is_new

    def __setattr__(self, key, value):
        if key == 'object':
            if not isinstance(value, models.Revision):
                raise TypeError('Revision object instance has to be passed')
        if key == 'is_new':
            if not isinstance(value, bool):
                raise TypeError('is_new object only accepts boolean values')
        super(SubmissionStorage, self).__setattr__(key, value)
