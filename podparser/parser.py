from xml.dom.minidom import parse

import argparse
import os
import sys

total    = 0
rejected = 0
no_geo   = 0
bad_geo  = 0

class Parser:
    """
    Post office directory parser.
    """

    def __init__(self,
                 config,
                 directory,
                 start           = 0,
                 end             = 9999,
                 encoder_key     = None,
                 verbose         = False,
                 pre_post_office = False,
                 commit          = False):
        """
        Initialise the parser.
        """
        self.config          = config
        self.directory       = directory
        self.start           = int(start)
        self.end             = int(end)
        self.verbose         = verbose
        self.pre_post_office = pre_post_office
        self.commit          = commit

        if encoder_key:
            import podparser.geo.encoder
            self.geoencoder = podparser.geo.encoder.Google(encoder_key)
        else:
            self.geoencoder = None
 
    def run_parser(self, callback):
        """
        Parse post office directory
        """

        from podparser import checker, directory

        # read meta data
        self.directory = directory.Directory(self.directory);

        # create checker object
        checker = checker.EntryChecker(self.directory, self.config)

        print 'Parsing %s for %s\n' % (self.directory.town, self.directory.year)

        # get list of files to parse
        self._get_listing();

        for page in self.directory.pages:
            lines = self._fix_line_returns(self._parse_page(page))

            if self.verbose:
                print '\n'
                for line in lines:
                    print line
                print '\n'

            for line in lines:
                pod_entry = directory.Entry(line)
                
                if pod_entry.valid():
                    # clean up valid entries
                    checker.clean_up(pod_entry)

                    # geo encode address if encoder set up
                    if self.geoencoder:
                        checker.geo_encode(self.geoencoder, pod_entry)

                self._print_entry(pod_entry)
                page.entries.append(pod_entry)
                
            callback(self.directory, page);

        return directory

    def _get_listing(self):
        #  get list of djvu xml files
        from podparser import directory
        
        def get_page_from_file(file):
            return int(file[len(file) -9: len(file) -5])

        path = self.directory.path
        if os.path.isdir(path):
            for d in os.listdir(path):
                if d.endswith('djvu_xml'):
                    pod_path = '%s%c%s' % (path, os.sep, d)
                    for f in os.listdir(pod_path):
                        if((f.startswith("postoffice") or f.startswith("williamsonsdirect")) and f.endswith(".djvu")):
                            page_no = get_page_from_file(f);
                        if page_no >= self.start and page_no <= self.end:
                            fpath = '%s%c%s' % (pod_path,
                                                os.sep,
                                                f)
                            self.directory.pages.append(directory.Page(fpath, page_no));
                            if self.verbose:
                                print fpath
                    break

        else:
            self.directory.pages.append(directory.Page(path, get_page_from_file(path)))

    def _parse_page(self, page):
        entries = []

        # parse POD page
        dom = parse(page.path)

        lines = dom.getElementsByTagName('LINE')

        for line in lines:
            entries.append(line.firstChild.nodeValue); 

        return entries

    def _fix_line_returns(self, lines):
        entries = []

        def add_to_last(entry):
            # append an entry with previous
            entries[len(entries) - 1] = '%s %s' % (entries[len(entries) - 1], entry)

        def get_top_char(lst):
            # find the most commonly occurring first character
            chars = {}
            char_val = 0
            
            for line in lst:
                if line[0] in chars:
                    chars[line[0]] = chars[line[0]] + 1
                else:
                    chars[line[0]] = 1

            for char in chars:
                if chars[char] > char_val:
                    top_char = char;
                    char_val = chars[char]

            return top_char

        top_char = get_top_char(lines)  
        current_alpha = None
   
        for entry in lines:
            if current_alpha is None:
                # if the first character is a character and uppercase
                # and entry contains a comma, then it looks like the first real entry
                if entry[0].isalpha() and entry[0].istitle() and len(entry.split(',')) > 2 and abs(ord(entry[0]) - ord(top_char)) < 2:
                   
                    current_alpha = entry[0]
                    entries.append(entry)
            else:
                previous = entries[len(entries) -1];

                if previous.endswith(',') or previous.endswith(',') or previous.endswith(' and') or previous[len(previous) - 1].isdigit():
                    add_to_last(entry);
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
                            add_to_last(entry);
                    else:
                        # first character isn't in alphabetical order - append to previous entry
                        add_to_last(entry);
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

        print entry

def read_page(directory, page):

    print 'Page Number: %d\n' % page.number
    global total, rejected, no_geo, bad_geo, bad_geo_derived

    # tally up out some stats
    for entry in page.entries:
        
        if entry.error:
            rejected = rejected + 1
        else:
            if entry.get_geo_status() == 0:
                no_geo = no_geo + 1
            elif entry.get_geo_status() == 1:
                bad_geo = bad_geo + 1

        total = total + 1

    rejected_per = float(rejected) / total * 100
    good_entries = total - rejected
    no_geo_per   = float(no_geo) / good_entries * 100
    bad_geo_per  = float(bad_geo) / good_entries * 100

    print '\n%-20s%d' % ('Total Entries:', total)
    print '%-20s%d%5d%%' % ('Rejected:', rejected, rejected_per)
    print '%-20s%d%5d%%' % ('No Geo Tag:', no_geo, no_geo_per)
    print '%-20s%d%5d%%' % ('Bad Geo Tag:', bad_geo, bad_geo_per)

if __name__ == "__main__":

    # get the pod parser directory
    cur_dir = os.path.dirname(sys.argv[0])
    if len(cur_dir) == 0:
        cur_dir = '.'
    os.chdir('%s%c..' % (cur_dir, os.sep))
    podparser_dir = os.getcwd()

    # add parent directory of the podparser to the sys path
    sys.path.append(os.getcwd())

    # parse commandline arguments
    arg_parser = argparse.ArgumentParser(description='Tool for parsing postcode directories')

    arg_parser.add_argument('-c', '--commit',
                            action='store_true',
                            help='commit to database')
    arg_parser.add_argument('-C', '--config',
                            nargs=1,
                            help='configuration directory')
    arg_parser.add_argument('-d', '--directory',
                            nargs=1, 
                            help='postcode directory to be parsed')
    arg_parser.add_argument('-e', '--end',
                            default=9999,
                            type=int,
                            help='End page to be parsed (only applies to -d), If no end page given parse until last.')
    arg_parser.add_argument('-k', '--key',
                            help='Geo parser key')
    arg_parser.add_argument('-p', '--page',
                            help='single postcode directory page to be parsed')
    arg_parser.add_argument('-s', '--start',
                            default=0,
                            help='Start page to be parsed (only applies to -d). If no start page given start from 0.')
    arg_parser.add_argument('-v', '--verbose',
                            action='store_true',
                            help='print detailed output')
    arg_parser.add_argument('-w', '--williamson',
                            action='store_false',
                            help="parse williamson's directory")    
    args = arg_parser.parse_args()

    if args.config:
        if os.path.isdir(args.config[0]):
            config_dir = args.config
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

    # kick off parsing
    from podparser import parser
    parser.Parser(config          = config_dir,
                  directory       = directory,
                  start           = args.start,
                  end             = args.end,
                  encoder_key     = args.key,
                  verbose         = args.verbose,
                  pre_post_office = args.williamson).run_parser(read_page)
