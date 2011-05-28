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
      url='',
      license='GPL',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      include_package_data=True,
      zip_safe=True,
      install_requires=[
          # -*- Extra requirements: -*-
      ],
      entry_points="""
      # -*- Entry points: -*-
      """,
      )
