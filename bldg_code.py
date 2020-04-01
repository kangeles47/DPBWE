# from parcel import parcel
import numpy as np
import random


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
            parcel.h_story = np.arange(7.5, 7.5 * parcel.num_stories, parcel.num_stories) #building elevation for each story
            parcel.h_bldg = parcel.num_stories * 7.5  # minimum ceiling height per room is used to calculate height of building
            parcel.num_rooms = 6 #assigning number of rooms based off of occupancy, structural system
            print(parcel.h_story, parcel.h_bldg)
            self.roof_survey_data(self.edition, parcel) #populate missing data for the parcel from national survey (CBECS)

    def roof_survey_data(self, edition, parcel):
        if edition == "2001 FBC":
            # Assign a roof pitch or predominant roof material given response from survey data (CBECS and RECS):
            if 'type' in parcel.roof: #if the National survey data populates a 'type' key for the parcel
                if parcel.roof['type'] == 'Built-up' or 'Concrete' or 'Synthetic or Rubber':
                    parcel.roof['pitch'] = 'flat' #roof slopes under 2:12
                elif parcel.roof['type'] == 'Slate or tile':
                    parcel.roof['pitch'] = 'steeper' #roof slopes 4:12 and greater
                elif parcel.roof['type'] == 'Metal Surfacing':
                    parcel.roof['pitch'] = "flat or shallow" #roof slopes up to 4:12
                elif parcel.roof['type'] == 'Shingles (Not Wood)' or 'Wooden Materials':
                    parcel.roof['pitch'] = 'shallow or steeper' #roof slopes 2:12 and greater
                else:
                    print('Roof type not supported')
            else: #Assign the roof type (national survey data) using the roof pitch and code-informed rulesets
                if parcel.roof['pitch'] == 'flat':
                    roof_matls = ['Builtup', 'Concrete', 'Metal Surfacing', 'Synthetic or Rubber']
                    roof_weights = [211, 0, 244, 78]
                    parcel.roof['type'] = random.choices(roof_matls, roof_weights)
                elif parcel.roof['pitch'] == 'shallow':
                    roof_matls = ['Shingles (not wood)','Metal Surfacing', 'Wooden Materials']
                    roof_weights = [234, 244, 0]
                    parcel.roof['type'] = random.choices(roof_matls, roof_weights)
                elif parcel.roof['pitch'] == 'steeper':
                    roof_matls = ['Shingles (not wood)', 'Slate or Tile', 'Wooden Materials']
                    roof_weights = [234, 66, 0]
                    parcel.roof['type'] = random.choices(roof_matls, roof_weights)
                else:
                    print('Roof pitch not supported')
        else:
            print('Code edition/national survey currently not supported')





#What we would like this class to do is define all of the relevant building parameters:
#Predominant exterior wall material
#roof pitch
#roof type
#


# test = parcel ('12345', 5, 'Hotel', 2002, 14, 15, "FL Panhandle")
# test2 = bldg_code(test)
