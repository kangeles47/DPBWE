from bldg_code import BldgCode


class Parcel:

    def __init__(self,PID, num_stories, occupancy, year_built, lat, lon, location):
        # First define all building attributes available from building tax data
        self.PID = PID
        self.num_stories = num_stories
        self.occupancy = occupancy
        self.year_built = year_built
        self.lat = lat
        self.lon = lon
        self.location = location
        # Derived quantities from national survey data: Commercial Buildings Energy Consumption Survey
        print(self.location)
        print(self.year_built)

        # Pull this parcel's code-informed attributes:
        self.bldg_code = BldgCode(self)
        #self.bldg_code=bldg_code(self)
        #print(self.bldg_code)

test = Parcel ('12345', 5, 'Hotel', 2002, 14, 15, "FL Panhandle")
print(test.bldg_code)