from setuptools import setup, find_packages
import sys, os

version = '0.1'

setup(name='podparser',
      version=version,
      description="Post Office Directory Parser",
      long_description="""\
The podparser is a tool for parsing Scotlands post office directories""",
      classifiers=[], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
      keywords='post-office pod directory geneology history scotland',
      author='George Hamilton',
      author_email='george.hamilton@ed.ac.uk',
      url='https://github.com/gmh04/podparser',
      license='GPL',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      include_package_data=True,
      zip_safe=True,
      classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'License :: OSI Approved :: GNU General Public License (GPL)',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: System :: Archiving',
        'Topic :: Text Processing :: Indexing',
        ],
      install_requires=[
          # -*- Extra requirements: -*-
      ],
      entry_points="""
      # -*- Entry points: -*-
      """,
      )
