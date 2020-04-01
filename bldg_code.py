# from parcel import parcel
import numpy as np


class BldgCode:

    def __init__(self, parcel):
        # First determine what code we need to pull based off of the location and year built:
        if parcel.location == "FL":
            if parcel.year_built > 2001 & parcel.year_built < 2004:
                self.edition = "2001 FBC"
                print(self.edition)

        # Knowing the code edition, populate this parcel's code-informed attributes:
        if self.edition == "2001 FBC":
            # Story height, building height, number of rooms
            parcel.h_story = np.arange(7.5, 7.5 * parcel.num_stories, parcel.num_stories)
            parcel.h_bldg = parcel.num_stories * 7.5  # minimum ceiling height per room
            print(parcel.h_story, parcel.h_bldg)

        # Filter through the predominant roof material options considering code-based rulesets:
        if parcel.roof.pitch == 'flat':
            roof_matls = ['built-up', 'concrete', 'metal surfacing', 'synthetic or rubber']
            weights = [211, 0, 244, 78] #number of buildings in CBECS...ideally we would want this to get pulled from some sort of KB
        elif parcel.roof.pitch == 'shallow':
            roof_matls = ['shingles (not wood)','metal surfacing', 'wooden materials']
            weights = [234, 244, 0]
        elif parcel.roof.pitch == 'steeper':
            roof_matls = ['shingles (not wood)','slate or tile shingles', 'wooden materials']
            weights = [234, 66, 0]

        # randomly select one of the predominant roof material options
        # this will be written as follows:
        # parcel.roof.type = random.choices(roof_matls, weights)





#What we would like this class to do is define all of the relevant building parameters:
#Predominant exterior wall material
#roof pitch
#roof type
#


# test = parcel ('12345', 5, 'Hotel', 2002, 14, 15, "FL Panhandle")
# test2 = bldg_code(test)
