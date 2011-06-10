import argparse
import base64
import hashlib
import hmac
import json
import re
import sys
import time
import urllib
import urlparse

class Google(object):

    def __init__(self, verbose):
        """
        TODO
        """
        self.params = {'bounds': '55.8,-3.6|56.1,-2.6',
                       'sensor': 'false'}
        self.url     = 'http://maps.googleapis.com/maps/api/geocode/json'
        self.verbose = verbose

    def get_location(self, address, town):
        location = None

        # send to google in ascii
        address = '%s, %s, Scotland' % (address, town)
        self.params['address'] = address.encode('utf-8')

        url = self._get_url()

        f = urllib.urlopen(url)
        output = f.read()

        if self.verbose:
            print output

        try:
            result = json.loads(output)

            if result['status'] == 'OK':
                found_address  = None
                found_locality = None

                entry = result['results'][0]
                geom = entry['geometry']
                accuracy = geom['location_type']
                if accuracy != 'APPROXIMATE':
                    for comp in entry['address_components']:
                        if comp['types'][0] == 'route':
                            found_address = comp['long_name']

                            # locality is return in the next element
                            found_locality = entry['address_components'][entry['address_components'].index(comp) + 1]['long_name']

                            break

                location = Location(address        = address,
                                    town           = town,
                                    point          = geom['location'],
                                    type           = type,
                                    accuracy       = accuracy,
                                    found_address  = found_address,
                                    found_locality = found_locality)
            else:
                if result['status'] == 'ZERO_RESULTS':
                    pass
                elif result['status'] == 'OVER_QUERY_LIMIT':
                    print 'Google limit quota reached'
                elif result['status'] == "REQUEST_DENIED" or  result['status'] == "INVALID_REQUEST":
                    print 'Fetch rejected: %s' % result['status']
                    print url
        except ValueError as e:
            # can happen if URL is too large
            print e

        # enforce 1/2 second sleep after each fetch otherwise will be
        # blacklisted by google
        time.sleep(0.5)

        return location

    def _get_url(self):
        return '%s?%s' % (self.url, urllib.urlencode(self.params))

class GooglePremium(Google):
    """
    Use premium google geocode with premium key and client id
    """

    def __init__(self, key, client_id, db=None, verbose=False):
        super(GooglePremium, self).__init__(verbose)

        self.key              = key
        self.params['client'] = client_id
        self.db               = db

    def get_location(self, address, town, verbose=False):
        location = super(GooglePremium, self).get_location(address, town)

        if self.db:
            self.db.record_google_lookup();

        return location

    def _get_url(self):

        # for google's URL signing process see
        # http://code.google.com/apis/maps/documentation/webservices/#SignatureProcess

        # encode url
        url              = '%s?%s' % (self.url, urllib.urlencode(self.params))

        # convert the URL string to a URL,
        url              = urlparse.urlparse(url)

        # only sign the path+query part of the string
        urlToSign        = url.path + "?" + url.query

        # decode the private key into its binary format
        decodedKey       = base64.urlsafe_b64decode(self.key)

        # create a signature using the private key and the URL-encoded
        # string using HMAC SHA1. This signature will be binary.
        signature        = hmac.new(decodedKey, urlToSign, hashlib.sha1)
        encodedSignature = base64.urlsafe_b64encode(signature.digest())

        originalUrl      = url.scheme + "://" + url.netloc + url.path + "?" + url.query
        return '%s&signature=%s' % (originalUrl, encodedSignature)

class Location():
    """
    Stores location information related to an address

    address       - address used in search
    TODO
    found_address - address returned by google
    point         - the latlon returned by google for address
    accuracy      - accuracy returned by google:
                    ROOFTOP, RANGE_INTERPOLATED, GEOMETRIC_CENTER, APPROXIMATE
                    see http://code.google.com/apis/maps/documentation/geocoding/#Results
    type          - raw:     address is sent as found in the POD
                    derived: address is built using pattern matching
    """
    def __init__(self,
                 address,
                 town,
                 point,
                 accuracy,
                 type,
                 found_address=None,
                 found_locality=None):
        self.address       = address
        self.town          = town
        self.found_address = found_address
        self.found_locality = found_locality
        self.point         = point
        self.accuracy      = accuracy
        self.type          = ''
        self.exact         = False

        self._exact()

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

        if not self.accuracy:
            status = 0
        elif self.accuracy == 'APPROXIMATE':
            status = 1
        else:
            status = 2

        return status

    def _exact(self):
        # does the street returned by google match the search term?
        if self.found_address:
            s_addr = self.address.lower()
            g_addr = self.found_address.lower()

            s_addr = s_addr.replace(' lane',   ' ln')
            s_addr = s_addr.replace(' road',   ' rd')
            s_addr = s_addr.replace(' street', ' st')
            s_addr = s_addr.replace(' st.',    ' st')

            # if street returned buy google starts or ends with a single
            # character (e.g N, E, S or W) remove it
            if re.match('\w ', g_addr):
                g_addr = g_addr[2: len(g_addr)]
            if re.search(' \w$', g_addr):
                g_addr = g_addr[0: len(g_addr) - 2]

            if s_addr.find(g_addr) != -1:
                if self.town.lower() == self.found_locality.lower():
                    self.exact = True

    def __str__(self):
        latlon = '%(lat)f : %(lng)f ' % (self.point)
        str = '| %-60s | %s | %-20s | %-10s' % (self.address,
                                                latlon,
                                                self.accuracy,
                                                self.type)

        if self.found_address:
            if not self.exact:
                str = '%s (*** %s, %s ***)' % (str, self.found_address, self.found_locality)
            else:
                str = '%s (%s)' % (str, self.found_address)

        return str

if __name__ == "__main__":

    arg_parser = argparse.ArgumentParser(description='Wrapper for Google geo-encoder')

    arg_parser.add_argument('-a', '--address',
                            help     = 'Address to encode',
                            required = True)
    arg_parser.add_argument('-t', '--town',
                            help     = 'Address city or town',
                            required = True)
    arg_parser.add_argument('-k', '--key',
                            help='Google premium private key')
    arg_parser.add_argument('-i', '--client_id',
                            help = 'Google premium client identifier')
    arg_parser.add_argument('-v', '--verbose',
                            action = 'store_true',
                            help = 'Print detailed output')

    args = arg_parser.parse_args()

    if args.client_id and args.key:
        google = GooglePremium(args.key, args.client_id, verbose=args.verbose)
        print 'Encode using Google Premium'
    else:
        google = Google(verbose=args.verbose)
        print 'Encode using Google'

    print google.get_location(args.address, args.town)
