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

        self.globals = {}
        self._populate_global_replace('global.xml', self.globals)

        self.names = {}
        self.name_stop_words = []
        self._populate_global_replace('names.xml', self.names)
        self._populate_stop_words('names.xml', self.name_stop_words)

        self.professions = {}
        self._populate_global_replace('professions.xml', self.professions)
        self._populate_categories()

        self.address_replaces = {}
        self._populate_global_replace("addresses.xml", self.address_replaces)
        self._populate_address_lookup('streets.xml')

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

    def _populate_address_lookup(self, file_name):
        # parse and populate address/street lookup
        self.addresses = {}
        fname = '%s%c%s' % (self.config_dir, os.sep, file_name)

        if os.path.isfile(fname):
            dom = parse(fname)
            addrs = dom.getElementsByTagName('address')

            for addr_node in addrs:
                street = addr_node.getElementsByTagName('street')[0].firstChild.nodeValue
                patterns = addr_node.getElementsByTagName('pattern')

                # get town specific configuration for this address
                town = None
                town_nodes = addr_node.getElementsByTagName('town')

                for town_node in town_nodes:
                    name = None
                    modern_name = ''

                    for c in town_nodes[0].childNodes:
                        if c.nodeName == 'name':
                            name = c.firstChild.nodeValue
                        elif c.nodeName == 'modern_name':
                            modern_name = c.firstChild.nodeValue
                    if name and name.lower() == self.directory.town.lower():
                        town = {'modern_name': modern_name, 'areas': {}}

                        area_nodes = town_node.getElementsByTagName('area')
                        for area_node in area_nodes:
                            area_name_node = area_node.getElementsByTagName('name')
                            if area_name_node:
                                area_name   = area_name_node[0].firstChild.nodeValue
                                modern_name = ''

                                modern_node = area_node.getElementsByTagName('modern_name')
                                if modern_node:
                                    modern_name = modern_node[0].firstChild.nodeValue

                                town['areas'][area_name] = modern_name
                    break

                for patternNode in patterns:
                    pattern = patternNode.firstChild.nodeValue

                    self.addresses[pattern] = {'street': street,
                                               'modern_name': '',
                                               'areas': {}}

                    if town:
                        self.addresses[pattern]['modern_name'] = town['modern_name']

                        for area in town['areas']:
                            self.addresses[pattern]['areas'][area] = town['areas'][area]

    def _populate_categories(self):
        # parse and populate profession categories
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
        """
        Fix OCR problems with an individual entry.
        """

        # forename / surname name replaces
        for name in self.names:
            if entry.surname.find(name) != -1:
                entry.surname = entry.surnam.replace(name, self.names[name])
            if entry.forename.find(name) != -1:
                entry.forename = self.names[name]

        # name stop words
        for word in self.name_stop_words:
            if entry.surname.find(word) != -1:
                entry.error = 'Surname contains stop word: %s' % word
            elif entry.forename.find(word) != -1:
                entry.error = 'Forename contains stop word: %s' % word

        # do profession global replaces
        for profession in self.professions:
            if entry.profession.find(profession) != -1:
                entry.profession = entry.profession.replace(profession, self.professions[profession])

        # determine profession category
        for category in self.categories:
            if entry.profession.find(category) != -1:
                entry.category = self.categories[category]
                break

        # address global replaces
        for address in self.address_replaces:
            if entry.address.find(address) != -1:
                entry.address = entry.address.replace(address, self.address_replaces[address])

    def clean_up_global(self, line):
        """
        TODO
        """

        for replace in self.globals:
            if line.find(replace) != -1:
                line = line.replace(replace, self.globals[replace])

        return line

    def geo_encode(self, encoder, entry):
        """
        TODO
        """

        entry.locations = []
        addrs = []

        # process multiple addresses divided by a semi-colon
        if entry.address.find(';'):
            addrs = entry.address.split(';')
        else:
            addrs.append(entry.address)

        # process multiple addresses divided by ' and '
        for addr in addrs:
            if addr.find(' and '):
                more = addr.split(' and ')
                addrs.remove(addr)
                for a in more:
                    addrs.append(a)

        for addr in addrs:
            addr = addr.strip()

            # encode address as is
            location = self._get_derived_location(addr, encoder, entry)

            #if not location or not location.exact:
            #

            """
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
            """
    def _get_derived_location(self, addr, encoder, entry):
        location = None
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
                    # address stored as key
                    # modern name stored as a value
                    if areas[area]:
                        # replace address with modern name (note: drop area and door number)
                        derived_address = areas[area]
                    else:
                        # append area to derived address
                        derived_address = '%s, %s' % (derived_address, area)
                    break
            """
            location = encoder.get_location('%s, %s, %s' % (derived_address,
                                                            self.directory.town,
                                                         self.directory.country))
            """
            location = encoder.get_location(derived_address,
                                            self.directory.town,
                                            self.directory.country)

            if location:
                location.type = 'derived'
                entry.locations.append(location)

        return location
