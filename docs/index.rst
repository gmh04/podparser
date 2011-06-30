.. podparser documentation master file, created by
   sphinx-quickstart on Wed Jun  8 16:48:23 2011.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Post Office Directory Parser (podparser)
========================================

This document refers to version |release|

The podparser is a tool for parsing Scotland's Post Office directories.

************
Introduction
************
The `Scottish Post Office directories`_ are annual directories, from the period 1773 to 1911, that include an alphabetical list of a town's or county's inhabitants. The directories have been digitised by the `National Library of Scotland`_ and made available in XML fomat. The podparser attempts to parse the XML and determine the forename, surname, occupation and address(es) of each entry. Furthermore, each address location is geocoded.

Currently only the General Directory section of the directories are parsed.


************
Dependencies
************

- argparse

If the parser results are to be stored in a database there is a dependecy on `psycopg2`_. Note: Only `Postgis`_ is current supported.

************
Installation
************

::

    $ pip install podparser

*****
Usage
*****

The parser can be used as a command-line application or envoked as a library call within a python script.

Command Line
------------
The command-line application parses the directories from XML and optionally commits the entries to a database.

::

    $ python </path/to/site-packages>/podparser.parser.py

For a full list of parser command-line options see:

Python Library
--------------
The following example demonstrates executing the parser and retreiving the results.

::

    from podparser.parser import Parser

    p = Parser(config='/path/to/conf', directory='/path/to/pod')
    dir = p.run_parser()
    for page in dir.pages:
        for entry in page.entries:
            # do something with the entry
            print entry

Post Office directories can contain many pages, leading to parse times of many hours. In cases where many pages are being parsed it makes more sense to use a callback to process the results after the parsing of each page. This means if the process is killed before finishing, it can be restarted from the point of failure. The next example demonstrates the use of a callback.

::

    from podparser.parser import Parser

    def read_page(directory, page):
        for entry in page.entries:
            # do something with the entry
            print entry

    p = parser.Parser(config='/path/to/conf', directory='/path/to/pod')
    p.run_parser(read_page)

******
Config
******

*****
API
*****

.. automodule:: podparser.parser
   :members:

.. automodule:: podparser.directory
   :members:


.. asutofunction podparser.parser.__main__

.. autoclass: podparser.parser.Parser

   .. automethod: run_parser(self, callback)

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

.. _`National Library of Scotland`: http://www.nls.uk
.. _psycopg2: http://pypi.python.org/pypi/psycopg2/2.0.4
.. _postgis: http://postgis.refractions.net/
.. _Scottish Post Office directories: http://www.nls.uk/family-history/directories/post-office
