"""
The podparser is free software: you can redistribute it and/or modify it under
the terms of the GNU General Public License as published by the Free Software
Foundation, either version 3 of the License, or (at your option) any later
version.

The podparser is distributed in the hope that it will be useful, but WITHOUT ANY
WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
PARTICULAR PURPOSE.  See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with the
podparser.  If not, see <http://www.gnu.org/licenses/>.
"""

from datetime        import datetime
from xml.dom.minidom import parse

import argparse
import codecs
import contextlib
import os
import sys

# parser imports
import db
import checker
import directory
import geo
import parser
import podparser

from geo import encoder


def timer(f):
    # timer decorator
    def deco(self, *args):
        then = datetime.now()
        d = f(self, *args)

        td = datetime.now() - then

        if  td.seconds < 60:
            print '\nParse took: %d secs' % td.seconds
        else:
            print '\nParse took: %d hour(s): %d mins: %d secs' % (
                td.seconds / 3600,
                (td.seconds / 60) % 60,
                td.seconds % 60)
        return d
    return deco


@contextlib.contextmanager
def chdir(dirname=None):
    """
    Change directory but return to origin after context.

    dirname - the directory to change to
    """

    curdir = os.getcwd()
    try:
        if dirname is not None:
            os.chdir(dirname)
        yield
    finally:
        os.chdir(curdir)

class Parser:
    """
    Post office directory parser.

    | config      - The full path to the parser configuration files.
    | directory   - The full path to either an individual POD file or the POD
                    directory.
    | start       - Start directory page to be parsed, only applies to for
                    directory parse. If no start page given start from 0.
    | end         - End directory page to be parsed, only applies to for
                    directory parse. If no end page given parse until last.
    | encoder_key - Google premium private key
    | client_id   - Google premium client identifier
    | verbose     - Print detailed output
    | pre_post_office - parse williamson's directory?
    | db          - `PODconnection`_ instance
    | commit      - commit results to database?
    """

    def __init__(self,
                 config,
                 dir_path,
                 start=0,
                 end=9999,
                 encoder_key=None,
                 client_id=None,
                 verbose=False,
                 pre_post_office=False,
                 db=None,
                 commit=False):
        self.config          = config
        self.dir_path        = dir_path
        self.start           = int(start)
        self.end             = int(end)
        self.verbose         = verbose
        self.pre_post_office = pre_post_office
        self.db              = db
        self.commit          = commit

        if encoder_key and client_id:
            self.geoencoder = geo.encoder.GooglePremium(
                key=encoder_key,
                client_id=client_id,
                db=self.db)
        else:
            self.geoencoder = geo.encoder.Google()

    @timer
    def run_parser(self, callback=None):
        """
        Parse post office directory

        callback - function to be executed after each page parse
        """

        # read meta data
        self.directory = directory.Directory(self.dir_path)

        if self.directory.town == None:
            return None

        if self.db:
            self.db.set_directory(self.directory, self.commit)

        # create checker object
        entry_checker = checker.EntryChecker(self.directory, self.config)
        print 'Parsing %s for %s\n' % (self.directory.town,
                                       self.directory.year)

        # get list of files to parse
        self._get_listing()

        for page in self.directory.pages:

            print '\nParsing %s ' % page.path

            lines = self._fix_line_returns(self._parse_page(page,
                                                            entry_checker))

            if self.verbose:
                self._print_page(lines)

            for line in lines:
                # fix OCR problems with global replaces
                line = entry_checker.clean_up_global(line)

                # create entry with cleanup line
                pod_entry = directory.Entry(line)

                if pod_entry.valid():
                    # again, clean up valid entries
                    entry_checker.clean_up(pod_entry)

                    # geo encode address if encoder set up
                    if self.geoencoder:
                        entry_checker.geo_encode(self.geoencoder, pod_entry)

                self._print_entry(pod_entry)
                page.entries.append(pod_entry)

            # envoke callback function for a page
            if callback:
                callback(self.directory, page)

            # commit page to database
            if self.db and self.commit:
                self.db.commit(page)

        return self.directory

    def _get_listing(self):

        def get_page_from_file(file):
            #  get list of djvu xml files
            return int(file[len(file) - 9: len(file) - 5])

        path = self.directory.path
        if os.path.isdir(path):
            for d in os.listdir(path):
                if d.endswith('djvu_xml'):
                    pod_path = '%s%c%s' % (path, os.sep, d)
                    for f in os.listdir(pod_path):
                        if f.endswith(".djvu"):
                            if(f.startswith("postoffice") or
                               f.startswith("williamsonsdirect")):
                                page_no = get_page_from_file(f)
                            else:
                                print '*** No page number found for %s ***' % f
                                continue

                            if page_no >= self.start and page_no <= self.end:
                                fpath = '%s%c%s' % (pod_path,
                                                    os.sep,
                                                    f)
                                self.directory.pages.append(
                                    directory.Page(fpath, page_no))
                                if self.verbose:
                                    print fpath
                    break

            # sort files alphabetically by path
            self.directory.pages.sort(key=lambda x: x.path)

        else:
            self.directory.pages.append(
                directory.Page(path, get_page_from_file(path)))

    def _parse_page(self, page, checker):
        entries = []

        # parse POD page
        dom = parse(page.path)

        lines = dom.getElementsByTagName('LINE')

        for line in lines:
            if line.firstChild:
                # need to do surname replace on the raw line
                line = checker.clean_up_surname(line.firstChild.nodeValue)

                entries.append(line)

        return entries

    def _fix_line_returns(self, lines):
        # fix line wrapping int the PODs

        entries = []

        def add_to_last(entry):
            # append an entry with previous
            entries[len(entries) - 1] = '%s %s' % (
                entries[len(entries) - 1], entry)

        def get_top_char(lst):
            # find the most commonly occurring first character
            chars    = {}
            char_val = 0
            top_char = None

            for line in lst:
                if line[0] in chars:
                    chars[line[0]] = chars[line[0]] + 1
                else:
                    chars[line[0]] = 1

            for char in chars:
                if chars[char] > char_val:
                    top_char = char
                    char_val = chars[char]

            return top_char

        top_char = get_top_char(lines)
        current_alpha = None

        for entry in lines:

            if current_alpha is None:
                # if the first character is a character and uppercase and entry
                # contains a comma, then it looks like the first real entry
                if entry[0].isalpha() and \
                        entry[0].istitle() and \
                        len(entry.split(',')) > 2 and \
                        abs(ord(entry[0]) - ord(top_char)) < 2:
                    current_alpha = entry[0]
                    entries.append(entry)
            else:
                previous = entries[len(entries) - 1]

                if previous.endswith(',') or \
                        previous.endswith(' and') or \
                        previous[len(previous) - 1].isdigit():
                    add_to_last(entry)
                elif previous.endswith('-'):
                    # take off last character first
                    previous = previous[0: len(previous) - 1]

                    # append with no space
                    entries[len(entries) - 1] = '%s%s' % (previous, entry)
                elif entry[0] != current_alpha:
                    if ord(entry[0]) == (ord(current_alpha) + 1):
                        # found next char up
                        # check remaining entries have the same character
                        remaining = lines[lines.index(entry): len(lines)]
                        top_remaining = get_top_char(remaining)

                        if entry[0] == top_remaining:
                            current_alpha = top_remaining
                            entries.append(entry)
                        else:
                            add_to_last(entry)
                    else:
                        # first character isn't in alphabetical order
                        # - append to previous entry
                        add_to_last(entry)
                else:
                    # new entry
                    entries.append(entry)

        return entries

    def _print_entry(self, entry):
        # print entry details to stdout
        if entry.valid():
            geo_status = entry.get_geo_status()

            if geo_status == 0:
                print '*** No geo tag'
            elif geo_status == 1:
                print '*** Poor geo tag'

            if len(entry.profession) > 0 and entry.category == None:
                print '*** No profession category'

        print unicode(entry)

    def _print_page(self, lines):
        # print raw entries to std out
        print '\n'
        for line in lines:
            print line
        print '\n'

total         = 0
rejected      = 0
no_geo        = 0
bad_geo       = 0
unmatched_geo = 0

total_locations = 0
exact_locations = 0

profession  = 0
no_category = 0


def read_page(directory, page):

    if len(page.entries) == 0:
        return

    print 'Page Number: %d\n' % page.number
    global total, rejected, no_geo, bad_geo, unmatched_geo, profession, \
        no_category, total_locations, exact_locations

    # tally up out some stats
    for entry in page.entries:

        if entry.error:
            rejected = rejected + 1
        else:
            if entry.get_geo_status() == 0:
                no_geo = no_geo + 1
            elif entry.get_geo_status() == 1:
                bad_geo = bad_geo + 1
            else:
                # good geo tag, but is it exact?
                loc_stats = entry.get_location_stats()
                total_locations = total_locations + loc_stats[0]
                exact_locations = exact_locations + loc_stats[1]

            if len(entry.profession) > 0:
                profession = profession + 1

                if entry.category == None:
                    no_category = no_category + 1

        total = total + 1

    rejected_per      = float(rejected) / total * 100
    good_entries      = total - rejected
    no_geo_per        = float(no_geo)          / good_entries * 100
    bad_geo_per       = float(bad_geo)         / good_entries * 100
    profession_per    = float(profession)      / good_entries * 100
    no_category_per   = float(no_category)     / good_entries * 100

    if exact_locations == 0:
        exact_geo_per = 0
    else:
        exact_geo_per = float(exact_locations) / total_locations * 100

    print '\n%-20s%5d' % ('Total Entries:', total)
    print '%-20s%5d%5d%%' % ('Rejected:', rejected, rejected_per)
    print '%-20s%5d%5d%%' % ('No Geo Tag:', no_geo, no_geo_per)
    print '%-20s%5d%5d%%' % ('Bad Geo Tag:', bad_geo, bad_geo_per)
    print '%-20s%10d%%'   % ('Exact Tags:', exact_geo_per)
    print '%-20s%5d%5d%%' % ('Professions:', profession, profession_per)
    print '%-20s%5d%5d%%' % ('No Category:', no_category, no_category_per)


def run_parser():
    # kick off parser process

    # print unicode to std out
    sys.stdout = codecs.getwriter('utf8')(sys.stdout)

    # get the pod parser directory
    cur_dir = os.path.dirname(sys.argv[0])
    if len(cur_dir) == 0:
        cur_dir = '.'
    os.chdir('%s%c..' % (cur_dir, os.sep))
    podparser_dir = os.getcwd()

    # parse commandline arguments
    arg_parser = argparse.ArgumentParser(
        description='Tool for parsing postoffice directories')

    parse_group = arg_parser.add_argument_group('Parse Options')
    parse_group.add_argument(
        '-p', '--page',
        help='single postoffice directory page to be parsed')

    parse_group.add_argument(
        '-d', '--directory',
        nargs=1,
        help='postoffice directory to be parsed')
    parse_group.add_argument(
        '-s', '--start',
        default=0,
        help="""Start page to be parsed (only applies to -d). If no start page
                given start from 0.""")
    parse_group.add_argument(
        '-e', '--end',
        default=9999,
        type=int,
        help="""End page to be parsed (only applies to -d), If no end page
                given parse until last.""")
    parse_group.add_argument('-C', '--config',
                             nargs=1,
                             help='configuration directory')
    parse_group.add_argument('-w', '--williamson',
                             action='store_false',
                             help="parse williamson's directory")

    arg_parser.add_argument('-v', '--verbose',
                            action='store_true',
                            help='print detailed output')
    arg_parser.add_argument('-V', '--version',
                            action='store_true',
                            help='print podparser version')

    google_group = arg_parser.add_argument_group('Google Options')
    google_group.add_argument('-k', '--key',
                              help='Google premium private key')
    google_group.add_argument('-i', '--client_id',
                              help='Google premium client identifier')

    db_group = arg_parser.add_argument_group('Database Options')
    db_group.add_argument('-H', '--dbhost',
                          default='localhost',
                          help='database host')
    db_group.add_argument('-D', '--dbname',
                          default='ahistory',
                          help='database name')
    db_group.add_argument('-P', '--dbport',
                          type=int,
                          default=5432,
                          help='database port')
    db_group.add_argument('-U', '--dbuser',
                          default='ahistory',
                          help='database user name')
    db_group.add_argument('-W', '--dbpassword',
                          help='database password')
    db_group.add_argument('-c', '--commit',
                          action='store_true',
                          help='commit parsed results to database')

    args = arg_parser.parse_args()

    if args.version:
        print podparser.get_version()
        sys.exit(0)

    if args.config:
        if os.path.isdir(args.config[0]):
            config_dir = args.config[0]
        else:
            print '*** Invalid config directory ***'
            print arg_parser.print_help()
            sys.exit(1)
    else:
        config_dir = '%s/etc' % podparser_dir

    if args.directory:
        directory = args.directory[0]
    elif args.page:
        directory = args.page
    else:
        print '*** No directory given ***'
        print arg_parser.print_help()
        sys.exit(1)
    directory = os.path.abspath(directory)

    db_conn = None
    if args.dbpassword:
        # putting import here ensures that there is no
        # database library dependency unless needed
        from db import connection
        db_conn = connection.PodConnection(db_password=args.dbpassword,
                                           db_name=args.dbname,
                                           db_user=args.dbuser,
                                           db_host=args.dbhost,
                                           db_port=args.dbport)
    else:
        print 'No database defined'

    if not db and args.key:
        print 'To use google premium a database must be defined'
        args.key = None

    # kick off parsing
    parser.Parser(config=config_dir,
                  dir_path=directory,
                  start=args.start,
                  end=args.end,
                  encoder_key=args.key,
                  client_id=args.client_id,
                  verbose=args.verbose,
                  pre_post_office=args.williamson,
                  db=db_conn,
                  commit=args.commit).run_parser(read_page)

    sys.exit(0)

if __name__ == "__main__":
    """
    Execute parser as command line process
    """
    run_parser()
