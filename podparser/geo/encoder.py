import json
import sys
import time
import urllib

class Google():
    def __init__(self, key):
        self.params = {'key': key,
                       'bounds': '55.8,-3.6|56.1,-2.6',
                       'sensor': 'false'}
        
        self.url = 'http://maps.googleapis.com/maps/api/geocode/json'

    def get_location(self, address):
        location = None
        self.params['address'] = address

        url = '%s?%s' % (self.url, urllib.urlencode(self.params))
        f = urllib.urlopen(url)
        output = f.read()

        #print output

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

        # enforce 1/2 second sleep after each fetch otherwise will be
        # blacklisted by google
        time.sleep(0.5)

        return location

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
  
    if len(sys.argv) > 2:
        g = Google(sys.argv[1])
        print g.get_location(sys.argv[2])
        
    else:
        print 'Args are missing'
