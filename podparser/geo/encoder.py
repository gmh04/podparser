import argparse
import base64
import hashlib
import hmac
import json
import sys
import time
import urllib
import urlparse

class Google(object):
    def __init__(self):
        self.params = {'bounds': '55.8,-3.6|56.1,-2.6',
                       'sensor': 'false'}
        self.url = 'http://maps.googleapis.com/maps/api/geocode/json'

    def get_location(self, address):
        location = None

        # send to google in ascii
        self.params['address'] = address.encode('utf-8')

        url = self._get_url()

        f = urllib.urlopen(url)
        output = f.read()

        #print output

        try:
            result = json.loads(output)

            if result['status'] == 'OK':
                geom = result['results'][0]['geometry']            
                location = Location(address, geom['location'],  geom['location_type'])
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

    def __init__(self, key, client_id):
        super(GooglePremium, self).__init__()

        self.key              = key
        self.params['client'] = client_id

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
    """
    def __init__(self, address, point, accuracy):
        self.address  = address
        self.point    = point
        self.accuracy = accuracy
        self.type     = ''

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

    def __str__(self):
        latlon = '%(lat)f : %(lng)f ' % (self.point)
        return '%s : %s : %s' % (self.address, latlon, self.accuracy)

if __name__ == "__main__":

    arg_parser = argparse.ArgumentParser(description='Wrapper for Google geo-encoder')

    arg_parser.add_argument('-a', '--address',
                            help='Address to encode',
                            required=True)
    arg_parser.add_argument('-c', '--client_id',
                            help='Google client id')
    arg_parser.add_argument('-k', '--key',
                            help='Google private key')
 
    args = arg_parser.parse_args()
    
    if args.client_id and args.key:
        google = GooglePremium(args.key, args.client_id)
        print 'Encode using Google Premium'
    else:
        google = Google()
        print 'Encode using Google'
