from xml.dom.minidom import parse

import os
import re

class EntryChecker():
    """
    Checks and repairs OCR errors based on configuration
    """

    def __init__(self, directory, config_dir):
        """
        Contructor.

        directory  -- POD directory object
        config_dir -- full path to the config direcory
        """

        self.directory  = directory
        self.config_dir = config_dir

        self.forenames = {}
        self._populate_global_replace('forenames.xml', self.forenames)

        self.surname_stop_words = []
        self._populate_stop_words('surnames.xml', self.surname_stop_words)

        self.professions = {}
        self._populate_global_replace('professions.xml', self.professions)
        self._populate_categories()

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
                patterns = addr_node.getElementsByTagName('pattern')
                for patternNode in patterns:
                    pattern = patternNode.firstChild.nodeValue
                    street = addr_node.getElementsByTagName('street')[0].firstChild.nodeValue

                    modern_name = ''
                    modern_name_node = addr_node.getElementsByTagName('modern_name')
                    if len(modern_name_node) > 0:
                        modern_name =  modern_name_node[0].firstChild.nodeValue

                    self.addresses[pattern] = {'areas': {},
                                               'street': street,
                                               'modern_name': modern_name}

                    areas_node = addr_node.getElementsByTagName('areas')

                    if len(areas_node) > 0:
                        area_nodes = areas_node[0].getElementsByTagName('area')
                        for area_node in area_nodes:
                            nameNode = area_node.getElementsByTagName('name')
                            name = nameNode[0].firstChild.nodeValue

                            area_modern_name = ''
                            modNode = area_node.getElementsByTagName('modern_name')
                            if len(modNode) > 0:
                                area_modern_name = modNode[0].firstChild.nodeValue

                            self.addresses[pattern]['areas'][name] = area_modern_name

    def _populate_categories(self):
        self.categories = {}

        # directory specific addresses
        fname = '%s%cprofessions.xml' % (self.config_dir, os.sep)

        if os.path.isfile(fname):
            dom = parse(fname)
            categories_node = dom.getElementsByTagName('category')

            for category_node in categories_node:
                code_node = category_node.getElementsByTagName('code')

                if len(code_node) > 0:
                    code = code_node[0].firstChild.nodeValue
                    list_node = category_node.getElementsByTagName('pattern')

                    if len(list_node) > 0:
                        for lnode in list_node:
                            pattern = lnode.firstChild.nodeValue
                            self.categories[pattern] = code

    def clean_up(self, entry):

        if entry.forename in self.forenames:
            entry.forename = self.forenames[entry.forename]

        for word in self.surname_stop_words:
            if entry.surname.find(word) != -1:
                entry.error = 'Surname contains stop word: %s' % word

        # do profession global replaces
        for profession in self.professions:
            if entry.profession.find(profession) != -1:
                entry.profession = entry.profession.replace(profession, self.professions[profession])

        # determine profession category
        for category in self.categories:
            if entry.profession.find(category) != -1:
                entry.category = self.categories[category]
                break

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
            modern_name     = self.addresses[best_match]['modern_name']

            if modern_name:
                derived_address = modern_name

            # try and get house number from original
            match = re.search('(\d+)', addr)
            if match:
                derived_address = '%s %s' % (match.group(1), derived_address)

            # check if area is associated with entry
            for area in areas:
                if area.lower() in addr.lower():
                    # modern name is stored as a value
                    if areas[area]:
                        # replace address with modern name (note: drop area and door number)
                        derived_address = areas[area]
                    else:
                        # append area to derived address
                        derived_address = '%s, %s' % (derived_address, area)
                    break
            location = encoder.get_location('%s, %s, %s' % (derived_address,
                                                            self.directory.town,
                                                            self.directory.country))
            if location:
                location.type = 'derived'
                entry.locations.append(location)
