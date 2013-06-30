#!/usr/bin/env python

DESCRIPTION = """\
Web application for running scipy-central.org

"""

METADATA = dict(
    name='scipy_central',
    maintainer = "SciPy Developers",
    maintainer_email = "scipy-dev@scipy.org",
    url = "http://github.com/scipy/SciPyCentral",
    download_url = "http://github.com/scipy/SciPyCentral",
    license = 'BSD',
    packages=['scipy_central', 'scipy_central_deploy'],
    package_dir={'scipy_central_deploy': 'deploy'},
)

#----------------------------------------

import os
import subprocess
try:
    import setuptools
except ImportError:
    pass
from distutils.core import setup

def git_version():
    """Return the git revision as a string"""
    def _minimal_ext_cmd(cmd):
        # construct minimal environment
        env = {'LANGUAGE': 'C', 'LANG': 'C', 'LC_ALL': 'C'}
        for k in ['SYSTEMROOT', 'PATH']:
            v = os.environ.get(k)
            if v is not None:
                env[k] = v
        out = subprocess.Popen(cmd, stdout = subprocess.PIPE, env=env).communicate()[0]
        return out
    try:
        out = _minimal_ext_cmd(['git', 'rev-parse', 'HEAD'])
        revision = out.strip().decode('ascii')
    except OSError:
        revision = "Unknown"
    return revision

def get_version():
    with open('scipy_central/__init__.py', 'r') as f:
        source = f.read()
    ns = {}
    exec source in ns
    version = ns['__version__']
    if '.dev' in version:
        version += "-" + git_version()[:6]
    return version

def get_requirements():
    with open('requirements.txt', 'r') as f:
        return [x.strip() for x in f.read().splitlines() if x.strip()]

os.chdir(os.path.abspath(os.path.dirname(__file__)))

setup(version=get_version(),
      description = DESCRIPTION.splitlines()[0],
      long_description = "".join(DESCRIPTION.splitlines()[2:]),
      install_requires=get_requirements(),
      **METADATA)
