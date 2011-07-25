from podparser.parser import Parser
from time import sleep

import os
import unittest

def get_resource_dir():
     test_dir = os.path.dirname(os.path.abspath(__file__))
     return '%s%c%s' % (test_dir, os.sep, 'resources')

class ApiTest(unittest.TestCase):

     def setUp(self):
          self.test_resources_dir = get_resource_dir()

          # don't batter google server
          sleep(0.5)

     def test_no_meta(self):
          # test no metadata file
          path = '%s%c%s' % (self.test_resources_dir, os.sep, 'empty')
          p = Parser(config=path, dir_path=path)
          self.assertIsNone(p.run_parser())

     def test_parse_all(self):
          # test api with retrieving all results
          path = '%s%c%s' % (self.test_resources_dir, os.sep, 'api_test')

          p = Parser(config=path, dir_path=path)
          d = p.run_parser()

          self.assertEquals(1, len(d.pages))
          self.assertEquals(2, len(d.pages[0].entries))

     def test_parse_page(self):
          # test api with callback
          def call_back(directory, page):
               self.assertEquals(1, len(directory.pages))
               self.assertEquals(2, len(page.entries))

          path = '%s%c%s' % (self.test_resources_dir, os.sep, 'api_test')
          p = Parser(config=path, dir_path=path)
          d = p.run_parser(call_back)

class MiscTest(unittest.TestCase):
       def setUp(self):
            self.test_resources_dir = get_resource_dir()
            sleep(0.5)

       def test_dito(self):
            # test that ditos ' do.' addresses are ignored
            path = '%s%c%s' % (self.test_resources_dir, os.sep, 'dito_test')

            p = Parser(config=path, dir_path=path)
            d = p.run_parser()
            entry = d.pages[0].entries[0]
            self.assertEquals(1, len(entry.locations))

class StringReplaceTest(unittest.TestCase):
     def setUp(self):
          #self.test_resources_dir = get_resource_dir()
          self.replace_test_dir = '%s%c%s' % (get_resource_dir(), os.sep, 'replace_test')
          sleep(0.5)

     def test_global(self):
          # test global replace
          pod = '%s%ctest_djvu_xml%cpostofficetest_0200.djvu' % (self.replace_test_dir, os.sep, os.sep)
          p = Parser(config=self.replace_test_dir, dir_path=pod)
          d = p.run_parser()
          entry = d.pages[0].entries[0]

          self.assertEquals(entry.forename, 'Robert')
          self.assertEquals(entry.surname,  'Randolph')
          self.assertEquals(entry.address,  '101 Randolph Road')

     def test_name(self):
          # test name replace and stop words
          pod = '%s%ctest_djvu_xml%cpostofficetest_0201.djvu' % (self.replace_test_dir, os.sep, os.sep)
          p = Parser(config=self.replace_test_dir, dir_path=pod)
          d = p.run_parser()

          page = d.pages[0]

          entry = page.entries[0]
          self.assertEquals(entry.forename, 'John')
          self.assertEquals(entry.surname,  'Smith')

          # there should only be one
          self.assertFalse(page.entries[1].valid())

     def test_profession(self):
          # test name replace and stop words
          pod = '%s%ctest_djvu_xml%cpostofficetest_0202.djvu' % (self.replace_test_dir, os.sep, os.sep)
          p = Parser(config=self.replace_test_dir, dir_path=pod)
          d = p.run_parser()

          page = d.pages[0]

          entry = page.entries[0]
          self.assertEquals(entry.profession, 'bookseller')

          entry = page.entries[1]
          self.assertEquals(entry.category, 'A')

     def test_address(self):
          # test address string replaces
          pod = '%s%ctest_djvu_xml%cpostofficetest_0203.djvu' % (self.replace_test_dir, os.sep, os.sep)
          p = Parser(config=self.replace_test_dir, dir_path=pod)
          d = p.run_parser()

          #print d.pages[0]
          self.assertEquals(d.pages[0].entries[0].address, '10 Castle Street')

class GeoLookupTest(unittest.TestCase):
     def setUp(self):
          #self.test_resources_dir = get_resource_dir()
          self.replace_test_dir = '%s%c%s' % (get_resource_dir(), os.sep, 'replace_test')
          sleep(0.5)

     def test_street(self):
          # test street lookup
          pod = '%s%ctest_djvu_xml%cpostofficetest_0204.djvu' % (self.replace_test_dir, os.sep, os.sep)
          p = Parser(config=self.replace_test_dir, dir_path=pod)
          d = p.run_parser()

          page = d.pages[0]

          self.assertEquals(page.entries[0].locations[0].address, "1 Rosslyn Terrace, Glasgow, Scotland")
          self.assertEquals(page.entries[0].locations[0].type,    "derived")
          self.assertEquals(page.entries[1].locations[0].address, "2 Rosslyn Terrace, Glasgow, Scotland")
          self.assertEquals(page.entries[2].locations[0].address, "Brechin Street, Glasgow, Scotland")
          self.assertEquals(page.entries[3].locations[0].address, "Dowanside Road, Glasgow, Scotland")
          self.assertEquals(page.entries[4].locations[0].address, "Albert Drive, Glasgow, Scotland")

          # ensure area level modern name overrides town level latlon
          self.assertEquals(page.entries[5].locations[0].address, "New Tennant St, Glasgow, Scotland")

          print page.entries[5].locations[0]

     def test_latlon(self):
          # test ability to give latlon coords
          pod = '%s%ctest_djvu_xml%cpostofficetest_0205.djvu' % (self.replace_test_dir, os.sep, os.sep)
          p = Parser(config=self.replace_test_dir, dir_path=pod)
          d = p.run_parser()

          page = d.pages[0]

          self.assertEquals(page.entries[0].locations[0].point['lat'], 55.864210)
          self.assertEquals(page.entries[0].locations[0].address,      "Smith Street")
          self.assertEquals(page.entries[0].locations[0].point['lng'], -4.281235)
          self.assertEquals(page.entries[0].locations[0].type,         "explicit")
          self.assertEquals(page.entries[0].locations[0].accuracy,     "GEOMETRIC_CENTER")

          self.assertEquals(page.entries[1].locations[0].point['lat'], 55.111111)
          self.assertEquals(page.entries[1].locations[0].address,      "Smith Street")
          self.assertEquals(page.entries[1].locations[0].point['lng'], -4.111111)
          self.assertEquals(page.entries[1].locations[0].type,         "explicit")
          self.assertEquals(page.entries[1].locations[0].accuracy,     "GEOMETRIC_CENTER")

          self.assertNotEquals(page.entries[2].locations[0].type, "explicit")

class LineWrapping(unittest.TestCase):

     def test_wrap(self):
          line1 = 'Aname, fname, pro'
          line2 = 'Aname, fname, pro'
          line3 = 'Bname, fname, pro'
          line4 = 'Bname, fname, pro'
          lines = [line1, line2, line3, line4]

          p = Parser(config=None, dir_path=None)
          res = p._fix_line_returns(lines)
          self.assertEquals(4, len(res))

          lines[2] = 'Bname, fname, pro-'
          res = p._fix_line_returns(lines)
          self.assertEquals(3, len(res))

          lines[2] = 'bname, fname, pro'
          res = p._fix_line_returns(lines)
          self.assertEquals(3, len(res))


if __name__ == '__main__':
    unittest.main()
