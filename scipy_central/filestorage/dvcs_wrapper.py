"""
Wraps the standard DVCS commands: for mercurial.


Hg wrapper: modified from: https://bitbucket.org/kevindunn/ucommentapp
"""
import re, subprocess

hg_executable = '/usr/local/bin/hg'
git_executable = '/usr/bin/git'
bzr_executable = '/usr/bin/bzr'
testing = False

class DVCSError(Exception):
    """
    Exception class that must be used to raise any errors related to the DVCS
    operations.
    """
    pass

class DVCSRepo(object):
    """
    A class for dealing with a DVCS repository.
    """
    def __init__(self, backend, repo_dir, do_init=True):
        """
        Creates and report a DVCSRepo object in the ``repo_dir`` directory.
        If ``do_init`` is True, it will create this directory and initialize
        an empty repository at that location.

        A ``DCVSError`` is raised if the directory cannot be written to.
        """
        self.backend = backend
        if backend == 'hg':
            # Dictionary of Mercurial verbs:  key=internal verb, value = list:
            # First list entry is the actual verb to use at the command line,
            # Second entry contains any command line arguments
            # Third entry: dict of error codes and corresponding error messages
            self.verbs = {
                'pull':     ['pull',     ['-u'], {}],
                'checkout': ['checkout', ['-r'], {1: 'Unresolved files.'}],
                'merge':    ['merge',    [], {255: 'Conflicts during merge'}],
                'clone':    ['clone',    [], {}],
                'init':     ['init',     [], {}],
                'add':      ['add',      [], {}],
                'heads':    ['heads',    [], {0: '<string>'}],
                'commit':   ['commit',   ['-m',], {1: 'Nothing changed'}],
                'push':     ['push',     [], {}],
                'summary':  ['summary',  [], {0: '<string>'}],# return stdout
                         }
            self.executable = hg_executable
            self.local_prefix = 'file://'

        elif backend == 'git':
            self.executable = git_executable
            self.local_prefix = ''
            self.verbs = {}
            raise NotImplementedError('Git DVCS is not implemented yet.')
        elif backend == 'bzr':
            self.executable = bzr_executable
            self.local_prefix = ''
            self.verbs = {}
            raise NotImplementedError('Bazaar DVCS is not implemented yet.')
        else:
            raise NotImplementedError('That DVCS is not implemented yet.')


        self.local_dir = repo_dir
        if do_init:
            self.init(repo_dir)

    def run_dvcs_command(self, command, repo_dir=''):
        """
        Runs the given command, as if it were typed at the command line, in the
        directory ``repo_dir``.
        """
        verb = command[0]
        actions = self.verbs[verb][2]
        if repo_dir == '':
            repo_dir = self.local_dir
        try:
            command[0] = self.verbs[verb][0]
            command.insert(0, self.executable)
            out = subprocess.Popen(command, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE,
                                   cwd=repo_dir)
            if testing:
                # For some strange reason, unit tests fail if we don't have
                # a small pause here.
                import time
                time.sleep(0.1)

            stderr = out.stderr.readlines()
            if stderr:
                return stderr

            if out.returncode == 0 or out.returncode is None:
                if actions.get(0, '') == '<string>':
                    return out.communicate()[0]
                else:
                    return out.returncode
            else:
                return out.returncode

        except OSError as err:
            if err.strerror == 'No such file or directory':
                raise DVCSError(('The DVCS executable file was not found, or '
                                 'the repo directory is invalid'))

    def set_remote(self, remote_repo):
        """ Sets the remote repository. Only used when pushing.
        Remote path must already exist. If the repository is on a remote
        server, then we expect that repository to be created (init) already.
        """
        self.remote_dir = remote_repo

    def get_revision_info(self, repo_dir=''):
        """
        Returns the unique hexadecimal string the represents the current
        changeset.
        """
        command = [self.verbs['summary'][0],]
        command.extend(self.verbs['summary'][1])
        output = self.run_dvcs_command(command, repo_dir=repo_dir)

        # Used to signal that a repo does not exist yet:
        if output[0][0:5] == 'abort':
            raise(DVCSError(output[0]))
        source = output.split('\n')[0].split(':')
        return source[2].split()[0]

    def init(self, dest):
        """
        Creates a repository in the destination directory, ``dest``.
        """
        command = [self.verbs['init'][0],]
        command.extend(self.verbs['init'][1])
        command.extend([dest,])
        out = self.run_dvcs_command(command, repo_dir=dest)
        if out != None and out != 0:
            raise DVCSError('Could not initialize repository at %s' % dest)

    def add(self, *patterns):
        """
        Adds one or more files to the repository, using Mercurial's syntax for
        ``hg add``.  See ``hg help patterns`` for the syntax.
        """
        command = [self.verbs['add'][0],]
        command.extend(self.verbs['add'][1])
        command.extend(patterns)
        out = self.run_dvcs_command(command)
        if out != None and out != 0:
            raise DVCSError('Could not add one or more files to repository.')

    def check_out(self, rev='tip'):
        """
        Operates on the local repository to check out the revision
        to the given revision number.  The default revision is the `tip`.

        Returns the revision info after check out.
        """
        # Use str(0), because 0 by itself evaluates to None in Python logical checks
        command = [self.verbs['checkout'][0],]
        command.extend(self.verbs['checkout'][1])
        command.extend(str(rev))
        self.run_dvcs_command(command)
        return self.get_revision_info()

    def clone(self, destination):
        """ Creates a clone of ``self`` and places it at the destination
        location given by ``dest``.

        Returns the hexadecimal revision number of the destination repo.
        """
        command = [self.verbs['clone'][0],]
        command.extend(self.verbs['clone'][1])
        command.extend([self.local_prefix + self.local_dir,])
        command.extend(['.'])
        out = self.run_dvcs_command(command, repo_dir=destination)
        if out != None and out != 0:
            raise DVCSError(('Could not clone ``selff`` to %s' % (
                                        self.local_prefix + self.local_dir)))
        return DVCSRepo(destination)


    def commit(self, message):
        """
        Commit changes to the ``repo`` repository, with the given commit ``message``
        Returns the hexadecimal revision number.
        """
        command = [self.verbs['commit'][0],]
        command.extend(self.verbs['commit'][1])
        command.extend([message,])
        self.run_dvcs_command(command)
        return self.get_revision_info()

    def push(self):
        """Push local repo to the remote location. The ``self.set_remote(...)``
        function must be called prior to set the remote location.
        """
        command = [self.verbs['push'][0],]
        command.extend(self.verbs['push'][1])
        command.extend([self.remote_dir,])
        out = self.run_dvcs_command(command)
        if out != None and out != 0:
            raise DVCSError(('Could not push changes to the source repository: '
                              'additional info = %s' % out[0].strip()))

        return self.get_revision_info()

    def pull(self):
        """Pull updates from the remote location to the local repo.
        """
        command = [self.verbs['pull'][0],]
        command.extend(self.verbs['pull'][1])
        out = self.run_dvcs_command(command)
        if out != None and out != 0:
            raise DVCSError(('Could not pull changes from the remote'
                        ' repository; additional info = %s' % out[0].strip()))

        return self.get_revision_info()


    def commit_and_push_updates(self, message):
        """
        After making changes to file(s), programatically commit them to the
        local repository, with the given commit ``message``; then push changes
        back to the source repository from which the local repo was cloned.
        """
        # Update in the local repo first: can happen when, for example a
        # comment is resubmitted on the same node and the first commit has not
        # been pushed through to the remote server.
        output = self.check_out()
        if output is not None:
            return False

        # Then commit the changes
        self.commit(message)

        # Try pushing the commit
        out = self.push()
        if out != None and out != 0:
            raise DVCSError(('Could not push changes to the source repository: '
                              'additional info = %s' % out[0].strip()))

        return self.get_revision_info()

    def pull_update_and_merge(self):
        """
        Pulls, updates and merges changes from the other ``remote`` repository into
        the ``local`` repository.

        If the "pull" results on more than one head, then we will merge.
        See: http://hgbook.red-bean.com/read/a-tour-of-mercurial-merging-work.html

        After merging, it will automatically commit and leave the local repo at
        this tip revision.

        We cannot handle the case where merging fails!  In that case we will return
        a DVCSError.
        """

        # Performs the equivalent of "hg pull -u; hg merge; hg commit"

        # Pull in all changes from the remote repo and update.
        self.pull()
        # Above will return a message: "not updating, since new heads added"
        # if we require merging.

        # Anything to merge?  Are there more than one head?
        output_heads = self.run_dvcs_command(['heads'])
        num_heads = len(re.findall('changeset:   (\d)+', output_heads))

        # Merge any changes:
        if num_heads > 1:
            merge_error = self.run_dvcs_command(['merge'])

            # Commit any changes from the merge
            if not merge_error:
                self.commit(('Auto commit - dvcs_wrapper: updated and merged changes.'))
            else:
                raise DVCSError(('Could not automatically merge during update. '
                                 'More info = %s' % merge_error[0].strip()))