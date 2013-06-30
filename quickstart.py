#!/usr/bin/env python
"""
quickstart.py

Set up a virtual environment with necessary dependencies installed

"""
import sys
import os
import subprocess
import argparse

ROOT_DIR = os.path.abspath(os.path.dirname(__file__))
DEPLOY_DIR = os.path.join(ROOT_DIR, 'deploy')
VENV_DIR = os.path.abspath(os.path.join(DEPLOY_DIR, 'env'))

PYVER = "%d.%d" % (sys.version_info[0], sys.version_info[1])
MERCURIAL_WIN_BINARY = "http://mercurial.selenic.com/release/windows/mercurial-2.5.2.win32-py%s.exe" % PYVER

def find_python():
    for bindir in ['Scripts', 'bin']:
        for suffix in ['.exe', '']:
            python_bin = os.path.join(VENV_DIR, bindir, 'python' + suffix)
            easy_install_bin = os.path.join(VENV_DIR, bindir, 'easy_install' + suffix)
            if os.path.exists(python_bin) and os.path.exists(easy_install_bin):
                return python_bin, easy_install_bin
    raise RuntimeError("Something went wrong in virtualenv creation: "
                       "python and pip not found!")

def run_cmd(cmd):
    print("$ %s" % " ".join(cmd))
    ret = subprocess.call(cmd)
    if ret != 0:
        print("ERROR: command failed!")
        sys.exit(1)

def main():
    p = argparse.ArgumentParser(usage=__doc__.strip())
    args = p.parse_args()

    try:
        import virtualenv
    except ImportError:
        print("ERROR: You need to install Virtualenv (https://pypi.python.org/pypi/virtualenv) first")
        sys.exit(0)

    try:
        find_python()
    except RuntimeError:
        print("\n-- Creating virtualenv in deploy/env")
        print("$ virtualenv %s" % VENV_DIR)
        virtualenv.create_environment(VENV_DIR)

    python_bin, easy_install_bin = find_python()

    os.chdir(ROOT_DIR)

    print("\n-- Installing required modules")
    with open('requirements.txt', 'r') as f:
        requirements = [x.strip() for x in f.read().splitlines() if x.strip()]

    if sys.platform.startswith('win'):
        # Download the windows binary
        requirements = [MERCURIAL_WIN_BINARY if x.lower().startswith('mercurial')
                        else x for x in requirements]

    run_cmd([easy_install_bin] + requirements)

    print("\n-- Setting up development database")
    print("$ cd deploy")
    os.chdir(DEPLOY_DIR)
    run_cmd([python_bin, 'manage.py', 'syncdb'])
    run_cmd([python_bin, 'manage.py', 'migrate'])
    run_cmd([python_bin, 'manage.py', 'loaddata', 'sample'])
    run_cmd([python_bin, 'manage.py', 'rebuild_index'])

    print(r"""
-- All done!

Now you can do:

* Linux & OSX:

      cd deploy
      source env/bin/activate
      python manage.py runserver

* Windows:

      cd deploy
      env\Scripts\activate
      python manage.py runserver
""")

if __name__ == "__main__":
    main()
