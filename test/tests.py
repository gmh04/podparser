from datetime import datetime
from podparser.db import connection
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
        self.replace_test_dir = '%s%c%s' % (get_resource_dir(),
                                            os.sep,
                                            'replace_test')
        sleep(0.5)

    def test_global(self):
        # test global replace
        pod = '%s%ctest_djvu_xml%cpostofficetest_0200.djvu' % (
            self.replace_test_dir, os.sep, os.sep)
        p = Parser(config=self.replace_test_dir, dir_path=pod)
        d = p.run_parser()
        entry = d.pages[0].entries[0]

        self.assertEquals(entry.forename, 'Robert')
        self.assertEquals(entry.surname,  'Randolph')
        self.assertEquals(entry.address,  '101 Randolph Road')

    def test_name(self):
        # test name replace and stop words
        pod = '%s%ctest_djvu_xml%cpostofficetest_0201.djvu' % (
            self.replace_test_dir, os.sep, os.sep)
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
        pod = '%s%ctest_djvu_xml%cpostofficetest_0202.djvu' % (
            self.replace_test_dir, os.sep, os.sep)
        p = Parser(config=self.replace_test_dir, dir_path=pod)
        d = p.run_parser()

        page = d.pages[0]

        entry = page.entries[0]
        self.assertEquals(entry.profession, 'bookseller')

        entry = page.entries[1]
        self.assertEquals(entry.category, 'A')

    def test_address(self):
        # test address string replaces
        pod = '%s%ctest_djvu_xml%cpostofficetest_0203.djvu' % (
            self.replace_test_dir, os.sep, os.sep)
        p = Parser(config=self.replace_test_dir, dir_path=pod)
        d = p.run_parser()

        self.assertEquals(d.pages[0].entries[0].address, '10 Castle Street')

class GeoLookupTest(unittest.TestCase):
    def setUp(self):
        self.replace_test_dir = '%s%c%s' % (
            get_resource_dir(), os.sep, 'replace_test')
        sleep(0.5)

    def test_street(self):
        # test street lookup
        pod = '%s%ctest_djvu_xml%cpostofficetest_0204.djvu' % (
            self.replace_test_dir, os.sep, os.sep)
        p = Parser(config=self.replace_test_dir, dir_path=pod)
        d = p.run_parser()

        page = d.pages[0]

        self.assertEquals(page.entries[0].locations[0].address,
                          "1 Rosslyn Terrace, Glasgow, Scotland")
        self.assertEquals(page.entries[0].locations[0].type,    "derived")
        self.assertEquals(page.entries[1].locations[0].address,
                          "2 Rosslyn Terrace, Glasgow, Scotland")
        self.assertEquals(page.entries[2].locations[0].address,
                          "Brechin Street, Glasgow, Scotland")
        self.assertEquals(page.entries[3].locations[0].address,
                          "Dowanside Road, Glasgow, Scotland")
        self.assertEquals(page.entries[4].locations[0].address,
                          "Albert Drive, Glasgow, Scotland")

        # ensure area level modern name overrides town level latlon
        self.assertEquals(page.entries[5].locations[0].address,
                          "New Tennant St, Glasgow, Scotland")

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

        lines[0] = 'Aname, fname, pro, 21 Argyll-'
        lines[1] = ' street'
        lines[2] = 'Aname, fname, pro,'
        lines[3] = '12 Argyll St.'
        lines.append('Aname, fname, pro, 1 Argyll St and')
        lines.append('2 Argyll St.')
        lines.append('Aname, fname, pro, 21')
        lines.append('Argyll St')
        res = p._fix_line_returns(lines)

        self.assertEquals(res[0], 'Aname, fname, pro, 21 Argyll street')
        self.assertEquals(res[1], 'Aname, fname, pro, 12 Argyll St.')
        self.assertEquals(res[2], 'Aname, fname, pro, 1 Argyll St and 2 Argyll St.')
        self.assertEquals(res[3], 'Aname, fname, pro, 21 Argyll St')

class DbTest(unittest.TestCase):

    def setUp(self):
        self.db_test_dir = '%s%c%s' % (get_resource_dir(), os.sep, 'db_test')
        self.db = connection.PodConnection(db_password='password')
        sleep(0.5)

    def test_insert(self):
        # test simple database insert
        then = datetime.now()
        pod = '%s%ctest_djvu_xml%cpostofficetest_0200.djvu' % (self.db_test_dir, os.sep, os.sep)
        p = Parser(config=self.db_test_dir, dir_path=pod, db=self.db, commit=True)
        d = p.run_parser()
        self.directory = p.directory

        class Directory(object):
            def __init__(self):
                self.country = 'Scotland'
                self.town = 'Glasgow'
                self.year = 1681

        self.assertEquals(self.db.pod_id, self.db._fetch_pod_id(Directory()))

        cur = self.db.conn.cursor()
        sql = "SELECT id, section, number FROM page WHERE directory = %s";
        data = (self.db.pod_id,)
        cur.execute(sql, data)

        row = cur.fetchone()
        page_id = row[0]
        self.assertEquals('General Directory', row[1])
        self.assertEquals(200, row[2])

        cur = self.db.conn.cursor()
        sql = "SELECT id, line FROM entry WHERE page = %s";
        data = (page_id,)
        cur.execute(sql, data)

        row = cur.fetchone()
        entry_id = row[0]
        self.assertEquals('Smith, Bill, farmer, 100 Rosslyn Terrace ; 10 Albert Road', row[1])

        cur = self.db.conn.cursor()
        sql = """
                SELECT surname, forename, profession, profession_category, address, userid_mod, date_mod, current
                FROM entry_detail WHERE entry_id = %s
                """
        data = (entry_id,)
        cur.execute(sql, data)
        row = cur.fetchone()

        self.assertEquals('Smith',  row[0])
        self.assertEquals('Bill',   row[1])
        self.assertEquals('farmer', row[2])
        self.assertEquals('A',      row[3])
        self.assertEquals('100 Rosslyn Terrace ; 10 Albert Road',  row[4])
        self.assertEquals('parser', row[5])
        self.assertTrue(row[6] > then.replace(tzinfo=row[6].tzinfo) and row[6] < datetime.now(tz=row[6].tzinfo))
        self.assertEquals(True,     row[7])

        cur = self.db.conn.cursor()
        sql = """
                SELECT address, accuracy, type, userid_mod, date_mod, current, exact, ST_AsText(geom)
                FROM location WHERE entry_id = %s
                """
        data = (entry_id,)
        cur.execute(sql, data)
        rows = cur.fetchall()

        self.assertEquals('10 Albert Road, Glasgow, Scotland',  rows[0][0])
        self.assertEquals(4,                                    rows[0][1])
        self.assertEquals('derived',                            rows[0][2])
        self.assertEquals('parser',                             rows[0][3])
        dt = rows[0][4]
        self.assertTrue(dt > then.replace(tzinfo=dt.tzinfo) and dt < datetime.now(tz=dt.tzinfo))
        self.assertEquals(True,                             rows[0][5])
        self.assertEquals(True,                             rows[0][6])
        self.assertEquals('POINT(-4.2650211 55.8345335)',   rows[0][7])

        self.assertEquals('100 Rosslyn Terrace, Glasgow, Scotland',  rows[1][0])
        self.assertEquals(4,                                    rows[1][1])
        self.assertEquals('derived',                            rows[1][2])
        self.assertEquals('parser',                             rows[1][3])
        dt = rows[1][4]
        self.assertTrue(dt > then.replace(tzinfo=dt.tzinfo) and dt < datetime.now(tz=dt.tzinfo))
        self.assertEquals(True,                             rows[1][5])
        self.assertEquals(True,                             rows[1][6])
        self.assertEquals('POINT(-4.2979506 55.8794522)',   rows[1][7])

    def tearDown(self):
        self.db._delete_directory(self.directory)

if __name__ == '__main__':
    unittest.main()
