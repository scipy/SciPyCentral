"""
Wraps the standard DVCS commands: for mercurial only (at the moment).
Simplified BSD-license. (c) Kevin Dunn, 2011.

Hg wrapper: modified from: https://bitbucket.org/kevindunn/ucommentapp
"""
import re, subprocess, os

# http://code.activestate.com/recipes/52224-find-a-file-given-a-search-path/
def search_file(filename, search_path):
    """Given a search path, find file
    """
    file_found = 0
    paths = search_path.split(os.pathsep)
    for path in paths:
        if os.path.exists(os.path.join(path, filename)):
            file_found = 1
            break
    if file_found:
        return os.path.abspath(os.path.join(path, filename))
    else:
        return None

testing = False

class DVCSError(Exception):
    """ Exception class used to raise errors related to the DVCS operations."""
    def __init__(self, value):
        self.value = value

class DVCSRepo(object):
    """
    A class for dealing with a DVCS repository.
    """
    def __init__(self, backend, repo_dir, do_init=True, dvcs_executable=''):
        """
        Creates and report a DVCSRepo object in the ``repo_dir`` directory.
        If ``do_init`` is True, it will create this directory and initialize
        an empty repository at that location.

        A ``DCVSError`` is raised if the directory cannot be written to, but
        only if the directory does not already contain a repository.
        i.e. if a ``.hg`` directory exists within ``repo_dir``, then an
        exception will not be raised.
        """
        self.backend = backend
        self.remote_dir = ''
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
                'commit':   ['commit',   ['-m', '-u'], {1: 'Nothing changed'}],
                'push':     ['push',     [], {}],
                'summary':  ['summary',  [], {0: '<string>'}],# return stdout
            }
            self.local_prefix = 'file://'

        elif backend == 'git':
            self.local_prefix = ''
            self.verbs = {}
            raise NotImplementedError('Git DVCS is not implemented yet.')
        elif backend == 'bzr':
            self.local_prefix = ''
            self.verbs = {}
            raise NotImplementedError('Bazaar DVCS is not implemented yet.')
        else:
            raise NotImplementedError('That DVCS is not implemented yet.')

        self.executable = dvcs_executable
        if not self.executable:
            if os.name == 'posix':
                self.executable = search_file(self.backend,
                                              os.environ['PATH'])
            elif os.name == 'windows':
                self.executable = search_file(self.backend + '.exe',
                                              os.environ['PATH'])
        if not self.executable:
            raise DVCSError(('Please provide the full path to the executable '
                             'for %s.' % self.backend))
        if not os.path.exists(self.executable):
            raise DVCSError(('The given executable file (%s) for %s does not '
                             'exist.' % (dvcs_executable, self.backend)))

        self.local_dir = repo_dir
        if do_init:
            try:
                self.init(repo_dir)
            except DVCSError:
                if repo_dir[-1] != os.sep:
                    repo_dir += os.sep
                if os.path.exists(repo_dir + '.' + backend):
                    pass
                else:
                    raise

    def __repr__(self):
        """ String representation of self """
        return '%s repo [%s]: revision %s' % (self.backend, self.local_dir,
                                               self.get_revision_info())

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
        if output[0] and output[0][0:5] == 'abort':
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
        # Use str(0), because 0 by itself evaluates to None in Python
        # logical checks
        command = [self.verbs['checkout'][0],]
        command.extend(self.verbs['checkout'][1])
        command.extend([str(rev),])
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
        return DVCSRepo(self.backend, destination, do_init=False,
                        dvcs_executable=self.executable)

    def commit(self, message, user=None):
        """
        Commit changes to the ``repo`` repository, with the given commit
        ``message`` and commit as ``user``. If ``user`` is None, then it
        commits as the user set in the .hgrc file.

        Returns the hexadecimal revision number.
        """
        command = [self.verbs['commit'][0],]
        command.append(self.verbs['commit'][1][0])
        command.extend([message,])
        if user:
            command.append(self.verbs['commit'][1][1])
            command.extend([user,])

        self.run_dvcs_command(command)
        return self.get_revision_info()

    def push(self):
        """Push local repo to the remote location. The ``self.set_remote(...)``
        function must be called prior to set the remote location.
        """
        if not self.remote_dir:
            raise DVCSError(('The remote repo location has not been set yet. '
                             'Use ``self.set_remote(location)`` first.'))
        command = [self.verbs['push'][0],]
        command.extend(self.verbs['push'][1])
        command.extend([self.remote_dir,])
        out = self.run_dvcs_command(command)
        if out != None and out != 0:
            raise DVCSError(('Could not push changes to the source repository: '
                             'additional info = %s' % out[0].strip()))
        return out

    def pull(self):
        """Pull updates from the remote location to the local repo.
        """
        command = [self.verbs['pull'][0],]
        command.extend(self.verbs['pull'][1])
        out = self.run_dvcs_command(command)
        if out != None and out != 0:
            raise DVCSError(('Could not pull changes from the remote'
                             ' repository; additional info = %s' %\
                             out[0].strip()))

        return self.get_revision_info()

    def heads(self):
        """ Returns a list of strings containing the revision hashes for each
        head."""
        command = [self.verbs['heads'][0],]
        command.extend(self.verbs['heads'][1])
        output_heads = self.run_dvcs_command(command)
        head_list = re.findall('changeset:   (\d:\w*)+', output_heads)
        return [h.split(':')[1] for h in head_list]

    def merge(self):
        """ Merges all heads. Returns ``None`` if successful, otherwise it
        returns the command line error message.
        """
        command = [self.verbs['merge'][0],]
        command.extend(self.verbs['merge'][1])
        merge_text = self.run_dvcs_command(command)
        if merge_text:
            raise DVCSError(('Could not automatically merge during update. '
                              'More info = %s' % merge_text[0].strip()))

    def update_commit_and_push_updates(self, message):
        """
        After making changes to file(s), programatically commit them to the
        local repository, with the given commit ``message``; then push changes
        back to the source repository from which the local repo was cloned.
        """
        # Update the local repo first to the 'tip' version
        self.check_out()

        # Then commit the changes
        self.commit(message)

        # Try pushing the commit
        out = self.push()
        if out != None and out != 0:
            raise DVCSError(('Could not push changes to the remote repo;'
                             'additional info = %s' % out[0].strip()))

        return self.get_revision_info()

    def pull_update_and_merge(self):
        """
        Pulls, updates and merges changes from the other ``remote`` repository
        into the ``local`` repository.

        If the "pull" results on more than one head, then we will merge. See
        http://hgbook.red-bean.com/read/a-tour-of-mercurial-merging-work.html

        After merging, it will automatically commit and leave the local repo at
        this tip revision.

        We cannot handle the case where merging fails! In that case we will
        return a DVCSError.
        """

        # Performs the equivalent of "hg pull -u; hg merge; hg commit"

        # Pull in all changes from the remote repo and update.
        self.pull()
        # Above will return a message: "not updating, since new heads added"
        # if we require merging.

        # Anything to merge?  Are there more than one head? If so, merge
        # and commit.
        if len(self.heads()) > 1:

            try:
                self.merge()
            except DVCSError:
                raise
            else:
                self.commit(('AUTO COMMIT - dvcs_wrapper with %s backend: '
                             'updated and merged changes.') % self.backend)