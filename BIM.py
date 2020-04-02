import numpy as np
from NatlSurveyData import NatlSurveyData

class BIM:

    # Here we might have to write some sort of function that parses the .JSON file from the SimCenter BIM Model

    def __init__(self, PID, num_stories, occupancy, yr_built, address, sq_ft):
        self.PID = PID
        self.num_stories = num_stories
        self.occupancy = occupancy
        self.yr_built = yr_built
        self.address = address
        self.sq_ft = sq_ft
        self.h_bldg = None #every building will have a height, building model fidelity will determine actual value
        self.walls = []
        self.roof = []
        self.floors = []
        self.struct_sys = []
        self.ceilings = []
        self.footprint = []  # in the case of parcel models, the footprint is going to be assumed as regular: Let's see if we can find data on this

        # Using basic building attributes, set up building metavariables:
        # 1) Tag the building as "commercial" or "not commercial"
        if self.occupancy == "Profession" or "Hotel" or "Motel" or "Financial":
            self.is_comm = True
        else:
            self.is_comm = False

        # 2) Define additional attributes regarding the building location:
        self.location_data(self)

    def location_data(self, BIM):
        # Here is where we are going to populate any characteristics relevant to the parcel's location:
        # What we get back from the parcel data is the address and zip code:
        zipcode = int(BIM.address.split()[-1])
        BayCountyZipCodes = np.arange(32401, 32418)
        BayCountyZipCodes = np.append(BayCountyZipCodes, [32438, 32444, 32466])

        if zipcode in BayCountyZipCodes:
            BIM.state = 'FL'
            BIM.county = 'Bay'
        else:
            print('County and State Information not currently supported')


# Now that we have defined the BIM superclass, it is time to define the Parcel subclass (we want all of our parcels to inherit the basic attributes outlined above)

class Parcel(BIM):

    def __init__(self, PID, num_stories, occupancy, yr_built, address, sq_ft):
        BIM.__init__(self, PID, num_stories, occupancy, yr_built, address, sq_ft) #Bring in all of the attributes that are defined in the BIM class for the parcel model
        # Define any building attributes that are specific to parcel models
        #Populate instance attributes informed by national survey data:
        survey_data = NatlSurveyData() #create an instance of the survey data class
        survey_data.run(self) #populate the parcel information
        a=1



test = Parcel('12345', 5, 'Hotel', 2002, "801 10th CT E Panama City 32401",'3200')
print(test.is_comm)
print(test.state)
print(test.h_bldg)