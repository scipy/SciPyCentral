from django.test import TestCase
from scipy_central import utils

# Python imports
import os
import shutil
import tempfile

import scipy_central.filestorage.dvcs_wrapper_git as dvcs

class SimpleTest(TestCase):
    def test_basic_addition(self):
        """
        Tests that 1 + 1 always equals 2.
        """
        self.assertEqual(1 + 1, 2)

class DVCS_Tests(TestCase):
    def setUp(self):
        """ Use a known testing file; write it to a temporary location for
        the test.
        """
        self.tempdir = tempfile.mkdtemp()
        self.local_path = self.tempdir + os.sep + 'local' + os.sep
        self.remote_path = self.tempdir + os.sep + 'remote' + os.sep

        utils.ensuredir(self.tempdir)
        utils.ensuredir(self.local_path)
        utils.ensuredir(self.remote_path)

        f = open(self.remote_path + 'index.rst', 'w')
        f.writelines(['Header\n','======\n', '\n', 'Paragraph 1\n', '\n',
                      'Paragraph 2\n', '\n', 'Paragraph 3\n'])
        f.close()

        self.local_repo = self.local_path
        self.remote_repo = self.remote_path
        #dvcs.local_repo_physical_dir = self.local_path


    def tearDown(self):
        """ Remove temporary files. """
        shutil.rmtree(self.tempdir)

    def test_hg_dvcs(self):

        # Create, add and commit to the remote repo
        dvcs.init(dest=self.remote_repo)
        dvcs.add(self.remote_path, 'index.rst')
        dvcs.commit(message='First commit', repo_dir=self.remote_path)

        # Verify that we cannot expect to query the remote repo:
        #self.assertRaises(dvcs.DVCSError, dvcs.get_revision_info, remote=True)

        # Clone the remote repo to the local repo
        #r_hex = dvcs.clone_repo(source=self.remote_repo, dest=self.local_repo)
        # Redundant, but tests the code in this file
        rev0 = dvcs.check_out(rev='tip')
        self.assertEqual(rev0, r_hex)

        # Now, in the local repo, make some changes to test

        # Add a comment for paragraph 2; commit
        f = open(self.local_path + 'index.rst', 'w')
        f.writelines(['Header\n','======\n', '\n', 'Paragraph 1\n', '\n',
                      'Paragraph 2\n', '\n', '.. ucomment:: aaaaaa: 11,\n', '\n'
                      'Paragraph 3\n'])
        f.close()
        rev1 = dvcs.commit_and_push_updates(message='Auto comment on para 2')

        # Check out an old revision to modify, rather than the latest revision
        hex_str = dvcs.check_out(rev=rev0)
        self.assertEqual(hex_str, rev0)

        # Now add a comment to paragraph 3, but from the initial revision
        f = open(self.local_path + 'index.rst', 'w')
        f.writelines(['Header\n','======\n', '\n', 'Paragraph 1\n', '\n',
                      'Paragraph 2\n', '\n', 'Paragraph 3\n', '\n',
                      '.. ucomment:: bbbbbb: 22,\n'])
        f.close()
        rev2 = dvcs.commit_and_push_updates(message='Auto comment on para 3')

        # Add a comment above on the local repo, again starting from old version
        hex_str = dvcs.check_out(rev=rev0)
        # Now add a comment to paragraph 1
        f = open(self.local_path + 'index.rst', 'w')
        f.writelines(['Header\n','======\n', '\n', 'Paragraph 1\n', '\n',
                      '.. ucomment:: cccccc: 33,\n', '\n', 'Paragraph 2\n', '\n',
                      'Paragraph 3\n'])
        f.close()
        hex_str = dvcs.commit_and_push_updates(message='Auto comment on para 1')

        f = open(self.local_path + 'index.rst', 'r')
        lines = f.readlines()
        f.close()
        final_result = ['Header\n', '======\n', '\n', 'Paragraph 1\n',
                                 '\n', '.. ucomment:: cccccc: 33,\n', '\n',
                                 'Paragraph 2\n', '\n',
                                 '.. ucomment:: aaaaaa: 11,\n', '\n',
                                 'Paragraph 3\n', '\n',
                                 '.. ucomment:: bbbbbb: 22,\n']
        self.assertEqual(lines, final_result)

        # Now test the code in dvcs.pull_update_and_merge(...).
        # Handles the basic case when the author makes changes (they are pushed
        # to the remote repo) and they should be imported imported into the
        # local repo without requiring a merge.
        final_result.insert(3, 'A new paragraph.\n')
        final_result.insert(4, '\n')
        with open(self.remote_path + 'index.rst', 'w') as f_handle:
            f_handle.writelines(final_result)

        dvcs.commit(override_dir = self.remote_path, message='Remote update.')
        dvcs.pull_update_and_merge()

        with open(self.local_path + 'index.rst', 'r') as f_handle:
            local_lines = f_handle.readlines()
        self.assertEqual(local_lines, final_result)
