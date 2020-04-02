class BIM:

    # Here we might have to write some sort of function that parses the .JSON file from the SimCenter BIM Model

    def __init__(self, PID, num_stories, occupancy, yr_built, address, sq_ft):
        self.PID = PID
        self.num_stories = num_stories
        self.occupancy = occupancy
        self.yr_built = yr_built
        self.address = address
        self.sq_ft = sq_ft
        self.walls = {}
        self.roof = {}
        self.floors = {}
        self.struct_sys = {}
        self.ceilings = {}
        self.footprint = {}  # in the case of parcel models, the footprint is going to be assumed as regular: Let's see if we can find data on this

        # Let's say I wanted to add something to my empty dictionary for the walls:
        self.walls['matls'] = 'concrete'

        # Using basic building attributes, set up building metavariables:
        # 1) Tag the building as "commercial" or "not commercial"
        if self.occupancy == "Profession" or "Hotel" or "Motel" or "Financial":
            self.is_comm = True
        else:
            self.is_comm = False

        # 2) Define additional attributes regarding the building location:
        self.location_data(self)

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

class Walls:

    def create_wall(self, bldg_model):
        # List out the attributes we would like to capture for each wall:
        #Data structure: I would like to go into
        wall_dict = dict.fromkeys(['type', 'is_loadbearing', 'is_impact_resistant', 'height', 'length', 'materials','thicknesses', 'is_exterior','base_floor'])