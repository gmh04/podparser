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

        if result['status'] == 'OK':
            print output
            geom = result['results'][0]['geometry']
            #accuracy = geom['location_type']
            #location = geom['location']

            location = Location(geom['location'],  geom['location_type']):
        else:
            print 'Fetch returned a status of %s' % result['status']
            print url

        return location

class Location():
    def __init__(self, point, accuracy):
        #self.lat = lat
        self.point
        self.accuracy = accuracy

if __name__ == "__main__":
    g = Google('ABQIAAAAteMzW-ziP3HW3ZZjPgk9ixT8_INs4XMsnY5-NjTNJBeA3ldNBhS1z74Tapal2-XqbvvkBJL1McMXQA&client=gme-unied')

    if len(sys.argv) > 1:
        g.get_location(sys.argv[1])
    else:
        print 'Address is missing'
