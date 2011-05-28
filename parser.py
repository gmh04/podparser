#import sys
import os

class Parser:
    """
    
    """
    def __init__(self,
                 config,
                 directory,
                 start=0,
                 end=9999,
                 verbose=False,
                 prePostOffice=False,
                 commit=False):

        self.config = config
        self.directory = directory
        self.start  = start
        self.end    = end
        self.verbose = verbose
        self.prePostOffice = prePostOffice
        self.commit = commit

 
    def run_parser(self):
        
        # read meta data
        self.metadata = MetaData(self.directory);
        
        files = self.get_listing();
        print files
      

    def get_listing(self):
        files = [];

        def get_page_from_file(file):
            return int(file[len(file) -9: len(file) -5])

        if os.path.isdir(self.directory):
            for d in os.listdir(self.directory):
                if d.endswith('djvu_xml'):
                    for f in os.listdir('%s%c%s' % (self.directory, os.sep, d)):
                        if((f.startswith("postoffice") or f.startswith("williamsonsdirect")) and f.endswith(".djvu")):
                            page_no = get_page_from_file(f);
                        print '%d %d' % (page_no, self.start)
                        
                        if page_no >= self.start and page_no <= self.end:
                            files.append(f)
                    break

        else:
            files.append(self.directory)

        return files

class MetaData():
     def __init__(self, directory):
         self.directory = directory;
         self.read();

     def read(self):
         if os.path.isdir(self.directory):
             ddir = self.directory
         elif os.path.isfile(self.directory):
             ddir = '%s%c..' % (self.directory, os.sep)
         else:
             print '*** Can read directory: %s ***' % self.directory
             sys.exit(1)
             
         for f in os.listdir(ddir):
             if f.endswith('_meta.xml'):
                 meta_file = '%s%c%s' % (ddir, os.sep, f)
                 break
             
         if meta_file:
             from xml.dom.minidom import parse, parseString
             dom = parse(meta_file)
             
             publisher = dom.getElementsByTagName('publisher')[0].firstChild.nodeValue
             self.town = publisher.split(':')[0].strip()
             
             volume = dom.getElementsByTagName('volume')[0].firstChild.nodeValue
             self.year = volume.split('-')[0].strip()
             
             print '%s => %s ' % (self.town, self.year)
            
         else:
             print '*** Cannot find metadata file in : %s ***' % ddir
             sys.exit(1)
