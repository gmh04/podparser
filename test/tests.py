from podparser.parser import Parser
from time import sleep

import os
import unittest

class ApiTest(unittest.TestCase):

     def setUp(self):
          self.test_dir           = os.path.dirname(os.path.abspath(__file__))
          self.test_resources_dir = '%s%c%s' % (self.test_dir, os.sep, 'resources')

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

if __name__ == '__main__':
    unittest.main()
