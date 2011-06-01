class EntryChecker():

    def __init__(self, config_dir):
        self.config_dir = config_dir

    def clean_up(self, entry):
        #self.entry = entry
        pass

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
            
