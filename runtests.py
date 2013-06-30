#!/usr/bin/env python
"""
runtests.py

Run all scipy_central tests in the current Python environment.

"""
import sys
import os
import subprocess
import argparse

def main():
    p = argparse.ArgumentParser(usage=__doc__.strip())
    p.add_argument("--verbose", "-v", action='store_true',
                   help="show more verbose output")
    args = p.parse_args()

    # Grab the list of our local apps from Django

    base_dir = os.path.abspath(os.path.dirname(__file__))

    os.chdir(base_dir)

    os.environ['DJANGO_SETTINGS_MODULE'] = 'spc_site.settings.development'
    __import__('spc_site.settings.development')
    mod = sys.modules['spc_site.settings.development']
    del os.environ['DJANGO_SETTINGS_MODULE']

    apps = [x.replace('scipy_central.', '') for x in mod.INSTALLED_APPS
            if x.startswith('scipy_central.')]

    if not apps:
        print("No apps found to run tests for!")
        sys.exit(1)


    # Run tests

    verbosity = '2' if args.verbose else '1'

    cmd = [sys.executable, 'manage.py',
           'test', '-v', verbosity, '--noinput', '--traceback'] + apps

    sys.exit(subprocess.call(cmd))

if __name__ == "__main__":
    main()
