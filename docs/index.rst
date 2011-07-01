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
The `Scottish Post Office directories`_ are annual directories, from the period 1773 to 1911, that include an alphabetical list of a town's or county's inhabitants. The directories have been digitised by the `National Library of Scotland`_ and made available in XML fomat. The podparser attempts to parse the XML and determine the forename, surname, occupation and address(es) of each entry. Furthermore, each address location is geocoded using the `Google Geocoding API`_.

Currently only the General Directory section of the directories are parsed.


************
Dependencies
************

- `argparse`_
- `psycopg2`_ (only if the parser results are to be stored in a database. Note: Only `Postgis`_ is current supported.)

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
The command-line application parses the Post Offices directories from XML and optionally commits the entries to a database. For example, the following parses a single directory page::

    $ python </path/to/site-packages>/podparser.parser.py -p </path/to/pod.xml>


The next example parses a range of directory pages::

    $ python </path/to/site-packages>/podparser.parser.py -d </path/to/pods> -s 110 -e 115

Below is an example that will commit the parse result to a database::

    $ python </path/to/site-packages>/podparser.parser.py -p </path/to/pod.xml> -D mydb -W mydbpass -c

For a full list of parser command-line options see help options::

    $ python </path/to/site-packages>/podparser.parser.py --help

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

Output
------
The parser prints out the parse results to the terminal. The following is an example of a single entry::

      | Auld                 | John                 | grocer and victualler | G | 25 Duke street ; house, 4 Burrell's lane.
    > | 4 Burrell's Lane, Glasgow, Scotland                          | 55.860516 : -4.238328  | GEOMETRIC_CENTER     | derived    (Burrell's Ln)
    > | 25 Duke Street, Glasgow, Scotland                            | 55.860185 : -4.238551  | RANGE_INTERPOLATED   | derived    (Duke St)

The first row is the entry details:

.. table::

   = ==================== ===
   1 Surname
   2 Forename
   3 Occupation
   4 Occupation Category  see `UK Standard Industrial Classification`_
   5 Address(es)
   = ==================== ===

Any following row (starting with '>') are locations that the parser has found in the address column:

.. table::

   === ======== =
    1  Address
    2  LatLon
    3  Accuracy see location_type in `Google Geocoding API results`_
    4  type     raw or derived (A raw type is an address query request as found in the address column. A derived type is constructed used pattern matching, see `Streets config`_)
   === ======== =

Stats
~~~~~
Statistics of the parse are collected and a summary is displayed after each page. For multiple page parses this summary for all the pages parsed and not the last. The table below contains a description of each field.

Problems
~~~~~~~~
The parser will attempt to alert the user when the is a problem with an entry. The following table lists possible problems.

.. table::

   ====================== ===
   No geo tag             No valid location could be found in the address column.
   Poor Geo tag           There is no address in the entry with a geo tag better than APPROXIMATE, see  location_type in `Google Geocoding API results`_
   No profession category Entry has a profession but no pattern is matched in `Professions config`_.
   Inexact tag            In parenthethis after the type column is the address returned by the google geocoding service. If the address returned does not match the query, it is marked as inexact with three asterixes.
   ====================== ===

******
Config
******

Global
------

Names
-----

Professions
-----------

Addresses
---------

Streets
-------


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

.. _argparse: http://docs.python.org/dev/library/argparse.html
.. _Google Geocoding API: http://code.google.com/apis/maps/documentation/geocoding/
.. _Google Geocoding API results: http://code.google.com/apis/maps/documentation/geocoding/#Results
.. _National Library of Scotland: http://www.nls.uk
.. _psycopg2: http://pypi.python.org/pypi/psycopg2/2.0.4
.. _postgis: http://postgis.refractions.net/
.. _Professions config: #professions
.. _Scottish Post Office directories: http://www.nls.uk/family-history/directories/post-office
.. _Streets config: #streets
.. _UK Standard Industrial Classification: http://www.google.com/url?sa=t&source=web&cd=4&ved=0CDsQFjAD&url=http%3A%2F%2Fwww.statistics.gov.uk%2Fmethods_quality%2Fsic%2Fdownloads%2Fsic2007explanatorynotes.pdf&rct=j&q=sic&ei=eqoNTpTEA8LRhAfJp4nnDQ&usg=AFQjCNG7JIkJyXBNV49I3Z5i1gMkMGiGww&sig2=_e5xBAyCYwqGh_qH8cEkMg&cad=rja
