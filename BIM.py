class BIM:

    # Here we might have to write some sort of function that parses the .JSON file from the SimCenter BIM Model

    def __init__(self, PID, num_stories, occupancy, year_built, lat, lon):
        self.PID = PID
        self.num_stories = num_stories
        self.occupancy = occupancy
        self.year_built = year_built
        self.lat = lat
        self.lon = lon
    # lat lon can also be used to figure out what the associated wind speed for the parcel is:
        #One of the first things that we will need to do for every parcel is figure out where they are located:
        #[INSERT SCRIPT]
        #some sort of if lat lon is within this lat lon range, then you are in this location
        self.location = "FL Panhandle"