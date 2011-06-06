from xml.dom.minidom import parse

import os
import re
import sys

class Directory():
    """
    POD metadata
    """

    def __init__(self, path):
        self.country = 'Scotland'
        self.pages   = []
        self.path    = path;
        self.read_from_meta();
        
    def read_from_meta(self):
        """
        read metadata from POD meta file
        """
        if os.path.isdir(self.path):
            ddir = self.path
        elif os.path.isfile(self.path):
            # get parent directory of single file
            ddir = self.path[0: self.path.rfind(os.sep)]
            ddir = ddir[0: ddir.rfind(os.sep)]
        else:
            print '*** Cannot read directory: %s ***' % self.path
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
        else:
            print '*** Cannot find metadata file in : %s ***' % ddir
            sys.exit(1)

class Page():
    """
    Represents a single page in the POD
    """

    def __init__(self, path, number):
        self.path    = path
        self.number  = number
        self.entries = []

class Entry():
    """
    Represents a single POD entry.
    """

    def __init__(self, line):
        self.line       = line
        self.profession = ''
        self.category   = ''
        self.error      = None
        self.locations  = []

        # parse individual entry values from pod
        self._parse()

    def _parse(self):
        # parse pod entry based on a single line string

        # apply global replace to all columns
        self.line = self.line.replace("M'", "Mc")

        columns = self.line.split(',')

        if len(columns) > 2:
            self.surname = columns[0].strip()
            self.forename = columns[1].strip()

            if len(columns) == 3:
                self.address = columns[2]
            elif len(columns) == 4:
                # if the third column has an address match concatenate with address
                if self._get_address_match(columns[2]):
                    self.address = '%s,%s' % (columns[2], columns[3])
                else:
                    self.profession = columns[2]
                    self.address = columns[3]
            else:
                # there are more than four columns, use the number in the address to divide them
                remaining = None
                for column in columns[2: len(columns)]:
                    if remaining:
                        remaining = '%s,%s' % (remaining, column)
                    else:
                        remaining = column

                match = self. _get_address_match(remaining)
          
                if match:
                    # there is an address match get the index
                    num_index = remaining.find(match.group(1))

                    # comma to left of number
                    comma_index = remaining[0: num_index].rfind(',')
                else:
                    # no address match just assign the third column to profession and the rest to the address
                    comma_index = remaining.find(',')
                    
                self.profession = remaining[0: comma_index]
                self.address    = remaining[comma_index + 1: len(remaining)]

            self.profession = self.profession.strip()
            self.address    = self.address.strip()
        else:
            # anything with less than 3 columns is invalid
            self.error = 'Not enough columns' 

    def _get_address_match(self, text):
        # match number
        match = re.search('(\d)', text)

        if not match:
            # if no number in address try some common street strings
            match = re.search('(street)', text, flags=re.IGNORECASE)

        return match

    def valid(self):
        """
        Is the entry valid? The entry is deemed invalid if the error property is
        set.
        """
        return self.error == None

    def get_geo_status(self):
        """
        Get geo status of an entry. This will return 

        0 - there is no geo tag
        1 - there is a poor geo tag
        2 - there is a good geo tag

        A poor geo tag is accuracy 'APPROXIMATE', while a good tag is any value
        above that (ROOFTOP, RANGE_INTERPOLATED, GEOMETRIC_CENTER, see
        http://code.google.com/apis/maps/documentation/geocoding/#Results).
        """
        status = 0

        if len(self.locations) == 0:
            status = 0
        else:
            status = 1
            for location in self.locations:
                if location.accuracy != 'APPROXIMATE':
                    status = 2
                    break

        return status

    def __str__(self):
       
        if self.error:
            str = 'Rejected: %s. Reason: %s\n' % (self.line, self.error)
        else:
            str = '| %-20s | %-20s | %-20s | %-1s | %-40s\n' % (self.surname,
                                                                self.forename,
                                                                self.profession,
                                                                self.category,
                                                                self.address)

            for location in self.locations:
                loc_str = '| %-60s | %f | %f | %-20s | %-5s' % (location.address,
                                                                location.point['lat'],
                                                                location.point['lng'],
                                                                location.accuracy,
                                                                location.type)
                str = '%s%s\n' % (str, loc_str)

        return str.encode( "utf-8" )
