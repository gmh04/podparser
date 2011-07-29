from setuptools import setup, find_packages

import os
import podparser
import sys

setup(name='podparser',
      version=podparser.get_version(),
      description="Post Office Directory Parser",
      long_description="The podparser is a tool for parsing Scotland's post office directories",
      keywords='post-office pod directory geneology history scotland',
      author='George Hamilton',
      author_email='george.hamilton@ed.ac.uk',
      url='https://github.com/gmh04/podparser',
      license='GPL',
      packages=find_packages(exclude=['ez_setup']),
      classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'License :: OSI Approved :: GNU General Public License (GPL)',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: System :: Archiving',
        'Topic :: Text Processing :: Indexing'
        ],
      install_requires=[
        'argparse'
        ],
      entry_points="""
            [console_scripts]
            podparser = podparser.parser:run_parser
          """,
      )
