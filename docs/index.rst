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
- `psycopg2`_ (only if the parser results are to be stored in a database. Note: Only `Postgis`_ is currently supported.)

************
Installation
************

::

    $ pip install podparser

or

::

    $ easy_install podparser

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
The following example demonstrates envoking the parser and retrieving the results from within a python script.

::

    from podparser.parser import Parser

    p = Parser(config='/path/to/conf', dir_path='/path/to/pod')
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

    p = parser.Parser(config='/path/to/conf', dir_path='/path/to/pod')
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
Statistics of the parse are collected and a summary is displayed after each page. For multiple page parses, this summary is for all pages parsed and not the last:

.. table::

    ============= ==
    Total Entries Number of processed entries after fixing line wrapping.
    Rejected      If an entry has less than 3 columns or the name contains a `stop word`_, the entry is not processed.
    No geo tag    Google has returned no geotag for the entry.
    Bad geo tag   Google has returned an accuracy of APPROXIMATE, see `Google Geocoding API results`_.
    Exact Tags    The percentage of good tags where the search address matches the result address.
    Professions   Number of entries with a profession entry
    No Category   Number of entries with a profession but no category.
    ============= ==

Problems
~~~~~~~~
The parser will alert the user when there is a problem with an entry:

.. table::

   ====================== ===
   No geo tag             No valid location could be found in the address column.
   Poor Geo tag           There is no address in the entry with a geo tag better than APPROXIMATE, see  location_type in `Google Geocoding API results`_
   No profession category Entry has a profession but no pattern is matched in `Professions config`_.
   Inexact tag            In parentheses after the type column is the address returned by the google geocoding service. If the address returned does not match the query, it is marked as inexact with three asterixes.
   Rejected               If an entry has less than 3 columns or contains a `stop word`_, the entry is not processed.
   ====================== ===

********
Database
********
Currently only Postgis is supported. The schema can be found in </path/to/site-packages>/podparser/etc.

******
Config
******
A number of XML files exist to help the parser improve the quality of the results.

Global
------

global.xml contains replace elements to fix Optical Character Recogintion(OCR) errors and misspellings for all entry fields. E.g.::

  <?xml version="1.0" encoding="UTF-8"?>
  <global>

    <replaces>
      <replace>
        <pattern>Eando'ph</pattern>
        <value>Randolph</value>
      </replace>
      <replace>
        <pattern>Eobert</pattern>
        <value>Robert</value>
      </replace>
      ...
    </replaces>
  </global>

Names
-----

In addition to containing replace elements to fix OCR errors and misspellings for name fields, names.xml contains stop words. A stop word is a character string where if found in the forename or surname, the entry will be rejected. Stop words in names can be used for identifying commercial entries::

  <?xml version="1.0" encoding="UTF-8"?>
  <names>
    <stopWords>
      <word>Association</word>
      <word>Insurance</word>
      ...
    </stopWords>

    ...
    <replace>
      <pattern>Jobn</pattern>
      <value>John</value>
    </replace>
    ...
  </names>


Professions
-----------
In addition to containing replace elements to fix OCR errors and misspellings for the profession field, professions.xml contains elements for indentifying professional category::

  <?xml version="1.0" encoding="UTF-8"?>

  <professions>
    <replaces>
      <replace>
        <pattern>bookfeller</pattern>
        <value>bookseller</value>
      </replace>
      ...
    </replaces>
    <categories>
      <category>
        <name>Agriculture, forestry and fishing</name>
        <code>A</code>
        <list>
          <pattern>cowfeeder</pattern>
          <pattern>dairy</pattern>
          <pattern>farmer</pattern>
          <pattern>game dealer</pattern>
        </list>
      </category>
    </categories>
  </professions>

Addresses
---------
addresses.xml contains replace elements to fix OCR errors and misspellings for the address field. E.g.::

  <?xml version="1.0" encoding="UTF-8"?>
  <addresses>
    <replaces>
      <replace>
        <pattern>Caftle</pattern>
        <value>Castle</value>
      </replace>
      <replace>
        <pattern>Calton-hiil</pattern>
        <value>Calton hill</value>
      </replace>
      ...
    </replaces>
  </addresses>

Streets
-------
streets.xml helps the parser improve google geoencoding by cleaning the address character string sent to google (derived address) and providing a mechanism for specifying the modern street name. For example for following provides a means of finding alternative spelling for the same street::

  <addresses>
    <address>
      <pattern>st james' terrace</pattern>
      <pattern>st. james terrace</pattern>
      <street>St James' Terrace</street>
    </address>
  <addresses>

The next example shows how by providing a town element, a modern street name can be defined::

  <address>
    <pattern>alexander street</pattern>
    <street>Alexander Street</street>
    <town>
      <name>Glasgow</name>
      <modern_name>Brechin Street</modern_name>
    </town>
  </address>

Furthermore, areas withing particular towns can have the same street name but different modern names::

  <address>
    <pattern>albert road</pattern>
    <street>Albert Road</street>
    <town>
      <name>Glasgow</name>
      <area>
        <name>Crosshill</name>
      </area>
      <area>
        <name>Langside</name>
        <modern_name>Dowanside Road</modern_name>
      </area>
      <area>
        <name>Pollockshields</name>
        <modern_name>Albert Drive</modern_name>
      </area>
    </town>
  </address>

A full example of streets can be found at `github`_.

*****
API
*****

Parser
------

.. autoclass:: podparser.parser.Parser
   :members:

   .. .. function:: Parser.run_parser(callback=None)
   .. method:: Parser.run_parser(callback=None)

      Kick off parser.

      Returns `Directory`_ instance

Directory
---------

.. autoclass:: podparser.directory.Directory
    :members: country, pages

Page
----

.. autoclass:: podparser.directory.Page
    :members:

Entry
-----

.. autoclass:: podparser.directory.Entry
    :members: forename, surname, profession, locations

Location
--------

.. autoclass:: podparser.geo.encoder.Location
    :members: address, point

PodConnection
-------------

.. autoclass:: podparser.db.connection.PodConnection

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

.. _argparse: http://docs.python.org/dev/library/argparse.html
.. _Directory: #podparser.directory.Directory
.. _Entries: #podparser.directory.Entry
.. _github: https://github.com/gmh04/podparser/blob/master/etc/streets.xml
.. _Google Geocoding API: http://code.google.com/apis/maps/documentation/geocoding/
.. _Google Geocoding API results: http://code.google.com/apis/maps/documentation/geocoding/#Results
.. _Locations: podparser.geo.encoder.Google
.. _National Library of Scotland: http://www.nls.uk
.. _Pages: #podparser.directory.Page
.. _psycopg2: http://pypi.python.org/pypi/psycopg2/2.0.4
.. _PodConnection: #podparser.db.connection.PodConnection
.. _postgis: http://postgis.refractions.net/
.. _Professions config: #professions
.. _Scottish Post Office directories: http://www.nls.uk/family-history/directories/post-office
.. _stop word: #names
.. _Streets config: #streets
.. _UK Standard Industrial Classification: http://www.google.com/url?sa=t&source=web&cd=4&ved=0CDsQFjAD&url=http%3A%2F%2Fwww.statistics.gov.uk%2Fmethods_quality%2Fsic%2Fdownloads%2Fsic2007explanatorynotes.pdf&rct=j&q=sic&ei=eqoNTpTEA8LRhAfJp4nnDQ&usg=AFQjCNG7JIkJyXBNV49I3Z5i1gMkMGiGww&sig2=_e5xBAyCYwqGh_qH8cEkMg&cad=rja
