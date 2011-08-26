from fabric.api import cd, local, settings

import fabfile
import os
import podparser
import sys
import types


def build_docs():
    """Create parser documentation"""

    with cd('docs'):
        fname = 'docs.zip'

        with settings(warn_only=True):
            local('rm %s' % fname)
            local('rm -rf html/%s' % podparser.get_version())

        local('make clean html', capture=False)

        # copy current version to root and versioned directory
        local('cp -rf _build/html html/%s' % podparser.get_version())
        local('cp -rf _build/html .')

        with cd('html'):
            local('zip -r ../%s .' % fname)

def upload():
    """Upload new package to pypi"""

    code_check()
    run_tests()

    local('python setup.py sdist upload', capture=False)

def upload_docs():
    """Upload sphinx documentation to pypi"""

    build_docs()
    local('python setup.py upload_sphinx --upload-dir=docs/html')

def code_check():
    """Run code style checker"""

    local('find podparser -name "*.py" | xargs pep8 --ignore=E221',
          capture=False)

def run_tests():
    """Run parser tests"""
    local('python -m unittest test.tests', capture=False)

def release():
    """Create a new version of the podparser"""

    # upload new package to pypi
    upload()

    # upload new package to pypi
    upload_docs()

    # create new tag
    local('git tag -a %s -m "release version %s"' % (podparser.get_version(), podparser.get_version()))
