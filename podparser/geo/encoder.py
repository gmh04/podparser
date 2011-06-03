import json
import sys
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
        result = json.loads(output)

        #print address

        if result['status'] == 'OK':
            #print output
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

        return location

class Location():
    def __init__(self, address, point, accuracy):
        self.address  = address
        self.point    = point
        self.accuracy = accuracy
        self.type     = ''

    def __str__(self):
        latlon = '%(lat)f : %(lng)f ' % (self.point)
        return '%s : %s : %s' % (self.address, latlon, self.accuracy)

if __name__ == "__main__":
  
    if len(sys.argv) > 2:
        g = Google(sys.argv[1])
        print g.get_location(sys.argv[2])
        
    else:
        print 'Args are missing'

