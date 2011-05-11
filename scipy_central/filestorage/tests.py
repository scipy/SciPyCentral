from django.test import TestCase
from scipy_central import utils

# Python imports
import os
import shutil
import tempfile

import scipy_central.filestorage.dvcs_wrapper as dvcs

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

    def tearDown(self):
        """ Remove temporary files. """
        pass
        shutil.rmtree(self.tempdir)

    def test_dvcs(self):
        pass

        backends = ['hg']
        for backend in backends:

            # Start from scratch every time
            shutil.rmtree(self.tempdir)
            utils.ensuredir(self.tempdir)
            utils.ensuredir(self.local_path)
            utils.ensuredir(self.remote_path)


            f = open(self.remote_path + 'index.rst', 'w')
            f.writelines(['Header\n','======\n', '\n', 'Paragraph 1\n', '\n',
                          'Paragraph 2\n', '\n', 'Paragraph 3\n'])
            f.close()

            remote_repo = dvcs.DVCSRepo(backend, self.remote_path)
            remote_repo.add('.')
            remote_repo.commit('Initial commit')
            remote_hash = remote_repo.get_revision_info()

            ## Create, add and commit to the remote repo

            ## Verify that we cannot expect to query the remote repo:
            ##self.assertRaises(dvcs.DVCSError, dvcs.get_revision_info, remote=True)

            local_repo = remote_repo.clone(self.local_path)
            local_hash = local_repo.check_out(rev='tip')
            self.assertEqual(local_hash, remote_hash)

            # Now, in the local repo, make some changes to test

            # Add a comment for paragraph 2; commit
            f = open(self.local_path + 'index.rst', 'w')
            f.writelines(['Header\n','======\n', '\n', 'Paragraph 1\n', '\n',
                          'Paragraph 2\n', '\n', '.. ucomment:: aaaaaa: 11,\n',
                           '\n', 'Paragraph 3\n'])
            f.close()
            self.assertRaises(dvcs.DVCSError, local_repo.push)
            local_repo.set_remote(self.remote_path)
            rev1 = local_repo.update_commit_and_push_updates(message='Para 2')

            # Check out an old revision to modify, rather than the latest revision
            new_hash = local_repo.check_out(rev=local_hash)
            self.assertEqual(new_hash, local_hash)

            # Now add a comment to paragraph 3, but from the initial revision
            f = open(self.local_path + 'index.rst', 'w')
            f.writelines(['Header\n','======\n', '\n', 'Paragraph 1\n', '\n',
                          'Paragraph 2\n', '\n', 'Paragraph 3\n', '\n',
                          '.. ucomment:: bbbbbb: 22,\n'])
            f.close()
            rev2 = local_repo.update_commit_and_push_updates(message='Para 3')

            # Add a comment above on the local repo, again starting from old version
            hex_str = local_repo.check_out(rev=local_hash)

            # Now add a comment to paragraph 1
            f = open(self.local_path + 'index.rst', 'w')
            f.writelines(['Header\n','======\n', '\n', 'Paragraph 1\n', '\n',
                          '.. ucomment:: cccccc: 33,\n', '\n', 'Paragraph 2\n',
                           '\n', 'Paragraph 3\n'])
            f.close()
            rev3 = local_repo.update_commit_and_push_updates(message='Para 1')

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

            remote_repo.commit(message='Remote update.')
            local_repo.pull_update_and_merge()

            with open(self.local_path + 'index.rst', 'r') as f_handle:
                local_lines = f_handle.readlines()
            self.assertEqual(local_lines, final_result)
