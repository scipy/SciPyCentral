#!/usr/bin/env python
"""
Dump the database to human-readable text file. This script is the equivalent
of typing: ``./manage.py dumpdata -v0 --format=json --indent=2``
in your Django project.

To restore from the database dump, use: ``./manage.py loaddata DUMP.DB``, where
DUMP.DB is the filename of the database dump.
"""

import os
import sys
import errno
import subprocess
from datetime import datetime

if __name__ == "__main__":

    if len(sys.argv) > 1:
        backup_file = sys.argv[1]
    elif len(sys.argv)==1:
        backup_dir = os.path.join(os.path.dirname(__file__), 'site_backup')
        try:
            os.makedirs(backup_dir)
        except OSError, err:
            if err.errno not in [0, getattr(errno, 'EEXIST', 0)]:
                raise IOError("Could not create the backup directory location")

        now = datetime.now()
        fname = datetime.strftime(now, 'backup-%Y-%m-%d-%H-%M-%S.json')
        backup_file = os.path.join(backup_dir, fname)

    # Note: you may have to change the ``python`` entry below to something like
    #       python2.7 if you've multiple Python versions on your machine
    command = ['python', 'manage.py', 'dumpdata', '-v0', '--format=json',
               '--indent=2']
    try:
        out = subprocess.Popen(command, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE,
                               cwd=os.getcwd())

        if out.returncode == 0 or out.returncode is None:
            fh = open(backup_file, 'w')
            fh.write(out.communicate()[0])
            fh.close()
            print('Successfully backup to JSON files in %s' % backup_file)
            sys.exit(0)
        else:
            print('Error code %d returned' % out.returncode)
            sys.exit(out.returncode)

    except OSError:
        print('ERROR: Could NOT backup: to see what the problem might be, try '
               'backing up manually with this command\n\n'
               'python manage.py dumpdata -v0 --format=json --indent=2')






