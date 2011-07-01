from fabric.api import cd, local, settings

import os
import sys

def upload():
    local('python setup.py sdist upload', capture=False) 

def build_docs():

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
            #print local('pwd')
            local('zip -r ../%s .' % fname)
            pass

def help():
    print 'fab help'
    print 'fab build_docs - build HTML documentation'
    print 'fab upload - upload to pypi'
