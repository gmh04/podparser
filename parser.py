from xml.dom.minidom import parse

import argparse
import os
import sys

class Parser:
    """
    Post office directory parser.
    """

    def __init__(self,
                 config,
                 directory,
                 start=0,
                 end=9999,
                 verbose=False,
                 prePostOffice=False,
                 commit=False):
        """
        Initialise the parser.
        """
        self.config        = config
        self.directory     = directory
        self.start         = start
        self.end           = end
        self.verbose       = verbose
        self.prePostOffice = prePostOffice
        self.commit        = commit

 
    def run_parser(self, callback):
        """
        
        """

        # read meta data
        self.metadata = MetaData(self.directory);
        
        # get list of files to parse
        files = self.get_listing();
        
        for page in files:
            entries = []
            lines = self.fix_line_returns(self.parse_page(page))
            
            for line in lines:
                entry = PodEntry(line)

                if entry.valid:
                    # clean up
                    # checker.cleanUp(PodEntry(line))
                entries.append(entry)
                
            callback(entries);
    def get_listing(self):
        """
        Get list of djvu xml files
        """
        files = [];

        def get_page_from_file(file):
            return int(file[len(file) -9: len(file) -5])

        if os.path.isdir(self.directory):
            for d in os.listdir(self.directory):
                if d.endswith('djvu_xml'):
                    for f in os.listdir('%s%c%s' % (self.directory, os.sep, d)):
                        if((f.startswith("postoffice") or f.startswith("williamsonsdirect")) and f.endswith(".djvu")):
                            page_no = get_page_from_file(f);
                        
                        if page_no >= self.start and page_no <= self.end:
                            files.append('%s%c%s' % (d, os.sep, f))
                    break

        else:
            files.append(self.directory)

        return files

    def parse_page(self, page):
        entries = []

        # parse POD page
        dom = parse(page)

        lines = dom.getElementsByTagName('LINE')

        for line in lines:
           entries.append(line.firstChild.nodeValue); 

        return entries

    def fix_line_returns(self, lines):
        entries = []

        def add_to_last(entry):
            entries[len(entries) -1] = '%s %s' % (entries[len(entries) -1], entry)

        def close_char(char):
            #return ord(char) != ord() + 1
            if abs(ord(char) - ord(top_char)) < 2:
                return True
            else:
                return False

        def get_top_char(lst):
            chars = {}
            char_val = 0
            
            for line in lst:
                if line[0] in chars:
                    chars[line[0]] = chars[line[0]] + 1
                else:
                    chars[line[0]] = 1
            print lst
            print chars

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
                    print '**** %c ***** ' % (current_alpha)
                    entries.append(entry)
            else:
                #print '%c : %d' % (entry[0], ord(entry[0]))
                previous = entries[len(entries) -1];

                if previous.endswith(',') or previous.endswith(' and') or previous[len(previous) - 1].isdigit():
                    add_to_last(entry);
                elif entry[0] != current_alpha: 
                    if ord(entry[0]) == (ord(current_alpha) + 1):
                        # next char up
                        # check all remaining entries have the same character
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

def read_page(entries):
    print entries

class PodEntry():
    def __init__(self, entry):
        self.entry = entry

class MetaData():
    """
    POD metadata
    """

    def __init__(self, directory):
        self.directory = directory;
        self.read();
        
    def read(self):
        """
        read metadata from POD meta file
        """
        if os.path.isdir(self.directory):
            ddir = self.directory
        elif os.path.isfile(self.directory):
            # get parent directory of single file
            ddir = self.directory[0: self.directory.rfind(os.sep)]
            ddir = ddir[0: ddir.rfind(os.sep)]
        else:
            print '*** Can read directory: %s ***' % self.directory
            sys.exit(1)
            
        # find meta file in directory
        for f in os.listdir(ddir):
            if f.endswith('_meta.xml'):
                meta_file = '%s%c%s' % (ddir, os.sep, f)
                break
             
        if meta_file:
            # parse meta file
            dom = parse(meta_file)
             
            # use publisher field for town
            publisher = dom.getElementsByTagName('publisher')[0].firstChild.nodeValue
            self.town = publisher.split(':')[0].strip()
             
            # volume becomes year
            volume = dom.getElementsByTagName('volume')[0].firstChild.nodeValue
            self.year = volume.split('-')[0].strip()
             
            print 'Parsing %s for %s' % (self.town, self.year)
            
        else:
            print '*** Cannot find metadata file in : %s ***' % ddir
            sys.exit(1)

if __name__ == "__main__":

    # get the pod parser direcory
    os.chdir('%s%c..' % (os.getcwd(), os.sep))
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
    arg_parser.add_argument('-p', '--page',
                            help='single postcode directory page to be parsed')
    arg_parser.add_argument('-e', '--end',
                            default=9999,
                            type=int,
                            help='End page to be parsed (only applies to -d), If no end page given parse until last.')
    arg_parser.add_argument('-s', '--start',
                            default=0,
                            help='Start page to be parsed (only applies to -d). If no start page given start from 0.')
    arg_parser.add_argument('-v', '--verbose',
                            action='store_false',
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
        #print args
        directory = args.page
    else:
        print '*** No directory given ***'
        print arg_parser.print_help()
        sys.exit(1)

    # kick off parsing
    from podparser import parser
    parser.Parser(config_dir,
                  directory,
                  args.start,
                  args.end,
                  args.verbose,
                  args.williamson).run_parser(read_page)
