from xml.dom.minidom import parse

import os

class EntryChecker():

    def __init__(self, directory, config_dir):
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

    def _populate_stop_words(self, file_name, lst):
        dom = parse('%s%c%s' % (self.config_dir, os.sep, file_name))

        words = dom.getElementsByTagName('word')
        for word in words:
            lst.append(word.firstChild.nodeValue)

    def _populate_address_lookup(self, directory):
        # directory specific addresses
        fname = '%s%c%s-%s.xml' % (self.config_dir, os.sep, directory.town.lower(), directory.year)

        if os.path.isfile(fname):
            self.addresses = {}
            dom = parse(fname)
            addresses = dom.getElementsByTagName('address')

            for addr_node in addresses:
                street = addr_node.getElementsByTagName('street')[0].firstChild.nodeValue
                self.addresses[street] = {'areas': [], 'modern_name': ''}
                areas_node = addr_node.getElementsByTagName('areas')

                if len(areas_node) > 0:
                    area_nodes = areas_node[0].getElementsByTagName('area')
                    for area_node in area_nodes:
                        self.addresses[street]['areas'].append(area_node.firstChild.nodeValue)               
                    
       

    def clean_up(self, entry):

        if entry.forename in self.forenames:
            entry.forename = self.forenames[entry.forename]

        for word in self.surname_stop_words:
            if entry.surname.find(word) != -1:
                entry.error = 'Surname contains stop word: %s' % word

        for profession in self.professions:
            if entry.profession.find(profession) != -1:
                entry.profession.replace(profession, self.professions[profession])

        for address in self.address_replaces:
            if entry.address.find(address) != -1:
                entry.address.replace(address, self.address_replaces[address])

    def geo_encode(self, encoder, directory, entry):

        entry.locations = []
        addresses = []

        if entry.address.find(';'):
            addresses = entry.address.split(';')
        else:
            addresses.append(entry.address)
        
        for addr in addresses:
            # do lookup
            
            # do encode
            location = encoder.get_location('%s, %s, %s' % (addr, directory.town, directory.country))

            if location:
                entry.locations.append(location)

        #import sys
        #sys.exit(1)
        
