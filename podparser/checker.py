from xml.dom.minidom import parse

import os
import re

class EntryChecker():
    """
    checks and repairs OCR errors based on configuration
    """

    def __init__(self, directory, config_dir):
        self.directory  = directory
        self.config_dir = config_dir

        self.forenames = {}
        self._populate_global_replace('forenames.xml', self.forenames)

        self.surname_stop_words = []
        self._populate_stop_words('surnames.xml', self.surname_stop_words)

        self.professions = {}
        self._populate_global_replace('professions.xml', self.professions)
        # categories ?

        self.address_replaces = {}
        self._populate_global_replace("addresses.xml", self.address_replaces)
        self._populate_address_lookup(directory)
        
    def _populate_global_replace(self, file_name, map):
        dom = parse('%s%c%s' % (self.config_dir, os.sep, file_name))

        replaces = dom.getElementsByTagName('replace')

        for replace in replaces:
            pattern = replace.getElementsByTagName('pattern')[0].firstChild.nodeValue
            value = ''
            valueNode = replace.getElementsByTagName('value')[0].firstChild

            if valueNode:
                value = valueNode.nodeValue
            
            map[pattern] = value
        #print '%s : %d' % (file_name, len(map))

    def _populate_stop_words(self, file_name, lst):
        dom = parse('%s%c%s' % (self.config_dir, os.sep, file_name))

        words = dom.getElementsByTagName('word')
        for word in words:
            lst.append(word.firstChild.nodeValue)

    def _populate_address_lookup(self, directory):
        self.addresses = {}

        # directory specific addresses
        fname = '%s%c%s-%s.xml' % (self.config_dir, os.sep, directory.town.lower(), directory.year)

        if os.path.isfile(fname):
            dom = parse(fname)
            addrs = dom.getElementsByTagName('address')

            for addr_node in addrs:
                #pattern = addr_node.getElementsByTagName('pattern')[0].firstChild.nodeValue

                patterns = addr_node.getElementsByTagName('pattern')
                for patternNode in patterns:
                    pattern = patternNode.firstChild.nodeValue
                    street = addr_node.getElementsByTagName('street')[0].firstChild.nodeValue
                    self.addresses[pattern] = {'areas': [],
                                               'street': street,
                                               'modern_name': ''}
                    areas_node = addr_node.getElementsByTagName('areas')

                    if len(areas_node) > 0:
                        area_nodes = areas_node[0].getElementsByTagName('area')
                        for area_node in area_nodes:
                            self.addresses[pattern]['areas'].append(area_node.firstChild.nodeValue)

                """
                street = addr_node.getElementsByTagName('street')[0].firstChild.nodeValue
                self.addresses[pattern] = {'areas': [],
                                           'street': street,
                                           'modern_name': ''}
                areas_node = addr_node.getElementsByTagName('areas')

                if len(areas_node) > 0:
                    area_nodes = areas_node[0].getElementsByTagName('area')
                    for area_node in area_nodes:
                        self.addresses[pattern]['areas'].append(area_node.firstChild.nodeValue)
                        """
    def clean_up(self, entry):

        if entry.forename in self.forenames:
            entry.forename = self.forenames[entry.forename]

        for word in self.surname_stop_words:
            if entry.surname.find(word) != -1:
                entry.error = 'Surname contains stop word: %s' % word

        for profession in self.professions:
            if entry.profession.find(profession) != -1:
                entry.profession = entry.profession.replace(profession, self.professions[profession])
              
        for address in self.address_replaces:
            if entry.address.find(address) != -1:
                entry.address = entry.address.replace(address, self.address_replaces[address])

    def geo_encode(self, encoder, entry):

        entry.locations = []
        addrs = []

        if entry.address.find(';'):
            addrs = entry.address.split(';')
        else:
            addrs.append(entry.address)
        
        for addr in addrs:
            addr = addr.strip()

            # encode address as is
            location = encoder.get_location('%s, %s, %s' % (addr,
                                                            self.directory.town,
                                                            self.directory.country))
        
            if location:

                # TODO: this is here for debugging - only append if good geo tag
                location.type = 'raw'
                entry.locations.append(location)

                if location.get_geo_status() < 2:
                    # poor location try getting a derived location
                    self._get_derived_location(addr, encoder, entry)
            else:
                # no location returned try derived
                self._get_derived_location(addr, encoder, entry)    

    def _get_derived_location(self, addr, encoder, entry):

        matches = []
        best_match = ''

        # do lookup
        for address in self.addresses:
            if address in addr.lower():
                matches.append(address)

        if len(matches) == 1:
            best_match = matches[0]
        elif len(matches) > 1:
            # more than one match - the best match will be the longest text
            for match in matches:
                if len(match) > len(best_match):
                    best_match = match
                    
        if len(best_match) > 0:
            derived_address = self.addresses[best_match]['street']
            areas           = self.addresses[best_match]['areas']

            # try and get house number from original
            match = re.search('(\d+)', addr)
            if match:
                derived_address = '%s %s' % (match.group(1), derived_address)

            # check if area is associated with entry
            for area in areas:
                if area.lower() in addr.lower():
                    derived_address = '%s, %s' % (derived_address, area)
                    #print 'AREA found %s ' % area
            location = encoder.get_location('%s, %s, %s' % (derived_address,
                                                            self.directory.town,
                                                            self.directory.country))
            if location:
                location.type = 'derived'
                entry.locations.append(location)
