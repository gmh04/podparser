from geo.encoder import Location
from xml.dom.minidom import parse

import os
import re

COMMA_REPLACEMEMT = '#&44'


class EntryChecker():
    """
    Checks and repairs OCR errors based on configuration
    """

    def __init__(self, directory, config_dir):
        """
        Contructor.

        directory  - POD directory object
        config_dir - full path to the config direcory
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
        fname = '%s%c%s' % (self.config_dir, os.sep, file_name)

        if os.path.isfile(fname):
            dom = parse(fname)
            replaces = dom.getElementsByTagName('replace')

            for replace in replaces:
                elem = replace.getElementsByTagName('pattern')[0]
                pattern = elem.firstChild.nodeValue
                value = ''
                valueNode = replace.getElementsByTagName('value')[0].firstChild

                if valueNode:
                    value = valueNode.nodeValue

                map[pattern] = value

    def _populate_stop_words(self, file_name, lst):
        fname = '%s%c%s' % (self.config_dir, os.sep, file_name)

        if os.path.isfile(fname):
            dom = parse(fname)

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
                elem = addr_node.getElementsByTagName('street')[0]
                street = elem.firstChild.nodeValue
                patterns = addr_node.getElementsByTagName('pattern')

                # get town specific configuration for this address
                town = None
                town_nodes = addr_node.getElementsByTagName('town')

                for town_node in town_nodes:
                    name        = None
                    modern_name = None
                    latlon      = None

                    for c in town_node.childNodes:
                        if c.nodeName == 'name':
                            name = c.firstChild.nodeValue
                        elif c.nodeName == 'modern_name':
                            modern_name = c.firstChild.nodeValue
                        elif c.nodeName == 'latlon':
                            latlon = c.firstChild.nodeValue

                    if name and name.lower() == self.directory.town.lower():
                        town = {'modern_name': modern_name,
                                'latlon': latlon,
                                'areas': {}}

                        area_nodes = town_node.getElementsByTagName('area')
                        for area_node in area_nodes:
                            area_name_node = \
                                area_node.getElementsByTagName('name')
                            if area_name_node:
                                area_name = \
                                    area_name_node[0].firstChild.nodeValue
                                town['areas'][area_name] = \
                                    {'modern_name': None,
                                     'latlon': None}

                                modern_node = area_node.getElementsByTagName(
                                    'modern_name')
                                if modern_node:
                                    town['areas'][area_name]['modern_name'] = \
                                        modern_node[0].firstChild.nodeValue
                                else:
                                    ll_node = area_node.getElementsByTagName(
                                        'latlon')
                                    if ll_node:
                                        town['areas'][area_name]['latlon'] = \
                                            ll_node[0].firstChild.nodeValue
                        break

                for patternNode in patterns:
                    pattern = patternNode.firstChild.nodeValue

                    self.addresses[pattern] = {'street': street,
                                               'latlon': None,
                                               'modern_name': None,
                                               'areas': {}}

                    if town:
                        self.addresses[pattern]['modern_name'] = \
                            town['modern_name']
                        self.addresses[pattern]['latlon']      = town['latlon']
                        self.addresses[pattern]['areas']       = town['areas']

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
            # only so forename here as surname
            # should be done as part of line fixing
            if entry.forename.find(name) != -1:
                entry.forename = self.names[name]

        # name stop words
        for word in self.name_stop_words:
            if entry.surname.find(word) != -1:
                entry.error = "Surname contains stop word: '%s'" % word
            elif entry.forename.find(word) != -1:
                entry.error = "Forename contains stop word: '%s'" % word

        # do profession global replaces
        for profession in self.professions:
            if entry.profession.find(profession) != -1:
                entry.profession = entry.profession.replace(
                    profession,
                    self.professions[profession])

        # determine profession category
        for category in self.categories:
            if entry.profession.lower().find(category) != -1:
                entry.category = self.categories[category]
                break

        # address global replaces
        for address in self.address_replaces:
            if entry.address.find(address) != -1:
                entry.address = entry.address.replace(
                    address,
                    self.address_replaces[address])

        # put commas back
        entry.forename   = entry.forename.replace(COMMA_REPLACEMEMT, ',')
        entry.surname    = entry.surname.replace(COMMA_REPLACEMEMT, ',')
        entry.profession = entry.profession.replace(COMMA_REPLACEMEMT, ',')
        entry.address    = entry.address.replace(COMMA_REPLACEMEMT, ',')

    def clean_up_global(self, line):
        """
        Fix global OCR problems
        """

        for replace in self.globals:
            if line.find(replace) != -1:
                line = line.replace(replace, self.globals[replace])

        # replace any comma within brackets with '&#44;'
        while re.search("(\(.+?)(,)(.+?\))", line):
            line = re.sub("(\(.+?)(,)(.+?\))",
                          r"\1%s\3" % COMMA_REPLACEMEMT, line)

        return line

    def clean_up_surname(self, line):
        """
        Clean first column of raw pod entry
        """

        idx = line.find(',')
        first_col = line[0: idx]

        for name in self.names:
            if name in first_col:
                line = ''.join((first_col.replace(name, self.names[name]),
                                line[idx:]))

        return line

    def geo_encode(self, encoder, entry):
        """
        Create geo loactions for an entry
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
            if ' and ' in addr:
                more = addr.split(' and ')
                addrs.remove(addr)
                for a in more:
                    addrs.append(a)

        for addr in addrs:
            addr = addr.strip()

            # don't process address if:
            # its a number
            # it contains the string ' do.' (or dito)
            if addr.isdigit() or addr.find(' do.') != -1:
                continue

            # encode address using derived address
            location = self._get_derived_location(addr, encoder)

            if not location:
                # derived failed, encode it raw
                location = encoder.get_location(addr, self.directory.town)
                if location:
                    location.type = 'raw'
                    entry.locations.append(location)
            else:
                entry.locations.append(location)

    def _get_derived_location(self, addr, encoder):
        # a derived location is an address defined in streets.xml
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
            derived_address = None
            latlon          = None

            address         = self.addresses[best_match]
            derived_address = address['street']

            if address['latlon']:
                latlon = address['latlon']
            elif address['modern_name']:
                derived_address = address['modern_name']
            else:
                # only try and get house number from original if
                # entry has no modern name or latlon defined
                match = re.search('(\d+)', addr)
                if match:
                    derived_address = '%s %s' % (match.group(1),
                                                 derived_address)

            # check if area is associated with entry
            areas = address['areas']
            for area in areas:
                if area.lower() in addr.lower():
                    if areas[area]['latlon']:
                        latlon = areas[area]['latlon']
                    elif areas[area]['modern_name']:
                        # replace address with modern name
                        # (note: drop area and door number)
                        derived_address = areas[area]['modern_name']

                        # ensure town level latlon is over-ridden
                        latlon = None
                    else:
                        # no modern address defined append
                        # area to derived address
                        derived_address = '%s, %s' % (derived_address, area)
                    break

            if latlon:
                # latlon has beed explicity set
                points = latlon.split(' ')

                try:
                    lat = float(points[0])
                    lon = float(points[1])

                    location = Location(address=address['street'],
                                        town=self.directory.town,
                                        point={'lat': lat,
                                               'lng': lon},
                                        accuracy='GEOMETRIC_CENTER')
                    location.type = 'explicit'
                    location.exact = True
                except Exception as e:
                    print '*** Error invalid latlon: %s: %s' % (points, e)
            else:
                # get location from google
                location = encoder.get_location(address=derived_address,
                                                town=self.directory.town)
                if location:
                    location.type = 'derived'

        return location
