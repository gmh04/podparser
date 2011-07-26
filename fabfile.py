from fabric.api import cd, local, settings

import fabfile
import os
import sys
import types


def upload():
    """Upload new package to pypi"""

    code_check()
    run_tests()

    local('python setup.py sdist upload', capture=False)


def build_docs():
    """Create parser documentation"""

    # set up environment
    sys.path.append(local('pwd').strip())
    import setup

    print setup.version

    with cd('docs'):
        fname = 'docs.zip'

        with settings(warn_only=True):
            local('rm %s' % fname)

        local('make clean html', capture=False)

        # copy current version to root and versioned directory
        local('cp -rf _build/html html/%s' % setup.version)
        local('cp -rf _build/html .')

        with cd('html'):
            local('zip -r ../%s .' % fname)


def code_check():
    """Run code style checker"""

    local('find . -name "*.py" | xargs pep8 --ignore=E221 --exclude=tests.py,conf.py,fabfile.py,',
          capture=False)
    #local('find . -name "fabfile.py" | xargs pep8', capture=False)


def run_tests():
    """Run parser tests"""
    local('python -m unittest test.tests', capture=False)
