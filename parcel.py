from bldg_code import BldgCode
import numpy as np

class Parcel:

    def __init__(self,PID, num_stories, occupancy, yr_built, address):
        # First define all building attributes available from building tax data
        self.PID = PID
        self.num_stories = num_stories
        self.occupancy = occupancy
        self.yr_built = yr_built
        self.address = address

        # Using basic building attributes, set up building metavariables:
        # 1) Tag the building as "commercial" or "not commercial"
        if self.occupancy == "Profession" or "Hotel" or "Motel" or "Financial":
            self.is_comm = True
        else:
            self.is_comm = False

        # Derived quantities from national survey data: Commercial Buildings Energy Consumption Survey
        print(self.yr_built)

        self.location_data(self)

        # Pull this parcel's code-informed attributes:
        #self.bldg_code = BldgCode(self)
        #self.bldg_code=bldg_code(self)
        #print(self.bldg_code)

    def location_data(self, parcel):
        # Here is where we are going to populate any characteristics relevant to the parcel's location:
        # What we get back from the parcel data is the address and zip code:
        zipcode = int(parcel.address.split()[-1])
        BayCountyZipCodes = np.arange(32401, 32418)
        BayCountyZipCodes = np.append(BayCountyZipCodes, [32438, 32444, 32466])
        print(BayCountyZipCodes)

        if zipcode in BayCountyZipCodes:
            parcel.state = 'FL'
            parcel.county = 'Bay'
        else:
            print('County and State Information not currently supported')
        # Census division for CBECS:
        if parcel.state == 'FL' or 'DE' or 'DC' or 'GA' or 'MD' or 'NC' or 'SC' or 'VA' or 'WV':
            parcel.census_div = 'South Atlantic'
            print(parcel.census_div)

test = Parcel ('12345', 5, 'Hotel', 2002, "801 10th CT E Panama City 32401")
#print(test.bldg_code)