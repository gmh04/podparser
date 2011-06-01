from xml.dom.minidom import parse

import os

class EntryChecker():

    def __init__(self, config_dir):
        self.config_dir = config_dir

        self.forenames = {}
        self._populate_global_replace('forenames.xml', self.forenames)

        self.surname_stop_words = []
        self._populate_stop_words('surnames.xml', self.surname_stop_words)

        self.professions = {}
        self._populate_global_replace('professions.xml', self.professions)
        # categories ?

        self.addresses = {}
        self._populate_global_replace("addresses.xml", self.addresses)
        
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

    def clean_up(self, entry):

        if entry.forename in self.forenames:
            entry.forename = self.forenames[entry.forename]

        for word in self.surname_stop_words:
            if entry.surname.find(word) != -1:
                entry.error = 'Surname contains stop word: %s' % word

        for profession in self.professions:
            if entry.profession.find(profession) != -1:
                entry.profession.replace(profession, self.professions[profession])

        for address in self.addresses:
            if entry.address.find(address) != -1:
                entry.address.replace(address, self.addresses[address])

    def geo_encode(self, encoder):

        self.locations = []
        addresses = []

        if self.address.find(';'):
            addresses = self.address.split(';')
        else:
            addresses.append(self.address)
        
        for addr in addresses:
            # do lookup
            
            # do encode
            location = encoder.get_location(addr)
            
