#!/usr/bin/env python
import os
import sys
import errno
import subprocess
from datetime import datetime

if __name__ == "__main__":

    backup_dir = os.path.join(os.path.dirname(__file__), 'site_backup')
    try:
        os.makedirs(backup_dir)
    except OSError, err:
        if err.errno not in [0, getattr(errno, 'EEXIST', 0)]:
            raise IOError("Could not create the backup directory location")


    # Also see https://docs.djangoproject.com/en/1.3/topics/serialization/
    # to make sure we are backing up all information.
    # Restoring from the backup has NOT BEEN TESTED yet.

    # ./manage.py loaddata site_backup/backup-YYYY-mm-dd-HH-MM-SS.json

    # Equivalent of: ./manage.py dumpdata -v0 --format=json --indent=2
    #
    # Note: you may have to change the ``python`` entry below to something like
    #       python2.7 if you've multiple Python versions on your machine
    command = ['python', 'manage.py', 'dumpdata', '-v0', '--format=json',
               '--indent=2']
    try:
        out = subprocess.Popen(command, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE,
                               cwd=os.getcwd())

        if out.returncode == 0 or out.returncode is None:
            now = datetime.now()
            fname = datetime.strftime(now, 'backup-%Y-%m-%d-%H-%M-%S.json')
            backup_file = os.path.join(backup_dir, fname)
            fh = open(backup_file, 'w')
            fh.write(out.communicate()[0])
            fh.close()
            print('Successfully backup to JSON files in %s' % backup_file)
            sys.exit(0)
        else:
            print('Error code %d returned' % out.returncode)
            sys.exit(out.returncode)

    except OSError as err:
        print('ERROR: Could NOT backup: try manually with this command\n\n'
               'python manage.py dumpdata -v0 --format=json --indent=2')






