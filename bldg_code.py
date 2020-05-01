# from parcel import parcel
import numpy as np
import random


class BldgCode:

    def __init__(self, parcel):
        # First determine what code we need to pull based off of the location and year built:
        if parcel.state == "FL":
            if parcel.yr_built > 1988 & parcel.yr_built <= 1991:
                self.edition = '1988 SBC'
            elif parcel.yr_built > 2001 & parcel.yr_built <= 2004:
                self.edition = '2001 FBC'
            elif parcel.yr_built > 2004 & parcel.yr_built <= 2007:
                self.edition = '2004 FBC'
            elif parcel.yr_built > 2007 & parcel.yr_built <= 2010:
                self.edition = '2007 FBC'
            else:
                self.edition = '1988 SBC' # Minimum building code for all other construction as per FL statutes
        self.bldg_attributes(self.edition, parcel)

    def bldg_attributes(self, edition, parcel):
        # Knowing the code edition, populate this building-level code-informed attributes for the parcel:
        if edition == '2001 FBC' or '1988 SBC':
            # Story height, building height, number of rooms
            parcel.h_story = np.arange(7.5, 7.5 * parcel.num_stories, parcel.num_stories) #building elevation for each story
            parcel.h_bldg = parcel.num_stories * 7.5  # minimum ceiling height per room is used to calculate height of building
            parcel.num_rooms = 6 #assigning number of rooms based off of occupancy, structural system
            print(parcel.h_story, parcel.h_bldg)
            #self.roof_survey_data(self.edition, parcel) #populate missing data for the parcel from national survey (CBECS)

    def roof_attributes(self, roof_choice, edition, parcel, survey):

        #Populate roof attributes for this instance (parcel)
        if edition == '2001 FBC' and survey == 'CBECS' and parcel.yr_built < 2003:
            # Assign qualitative descriptions of roof pitch given roof cover type from survey data:
            if parcel.roof.cover == 'Built-up' or 'Concrete' or 'Plastic/rubber/synthetic sheeting':
                parcel.roof.pitch = 'flat'  # roof slopes under 2:12
            elif parcel.roof.cover == 'Slate or tile shingles':
                parcel.roof.pitch = 'steeper'  # roof slopes 4:12 and greater
            elif parcel.roof.cover == 'Metal surfacing':
                parcel.roof.pitch = 'flat or shallow'  # roof slopes up to 4:12
            elif parcel.roof.cover == 'Asphalt/fiberglass/other shingles' or 'Wood shingles/shakes/other wood':
                parcel.roof.pitch = 'shallow or steeper'  # roof slopes 2:12 and greater
            else:
                parcel.roof.pitch = 'unknown'


            if parcel.roof.cover == None:
                if parcel.roof.pitch == 'flat':
                    roof_matls = ['Builtup', 'Concrete', 'Metal Surfacing', 'Synthetic or Rubber']
                    roof_weights = [211, 0, 244, 78]
                    parcel.roof.type = random.choices(roof_matls, roof_weights)
                elif parcel.roof.pitch == 'shallow':
                    roof_matls = ['Shingles (Not Wood)','Metal Surfacing', 'Wooden Materials']
                    roof_weights = [234, 244, 0]
                    parcel.roof.type = random.choices(roof_matls, roof_weights)
                elif parcel.roof.pitch == 'steeper':
                    roof_matls = ['Shingles (Not Wood)', 'Slate or Tile', 'Wooden Materials']
                    roof_weights = [234, 66, 0]
                    parcel.roof.type = random.choices(roof_matls, roof_weights)
                else:
                    print('Roof pitch not supported')
            else:
                if parcel.roof.cover == 'Built-up' or 'Concrete' or 'Synthetic or Rubber':
                    parcel.roof.pitch = 'flat' #roof slopes under 2:12
                elif parcel.roof.cover == 'Slate or tile':
                    parcel.roof.pitch = 'steeper' #roof slopes 4:12 and greater
                elif parcel.roof.cover == 'Metal Surfacing':
                    parcel.roof.pitch = 'flat or shallow' #roof slopes up to 4:12
                elif parcel.roof.cover == 'Shingles (Not Wood)' or 'Wooden Materials':
                    parcel.roof.pitch = 'shallow or steeper' #roof slopes 2:12 and greater
                else:
                    print('Roof cover not supported')
        else:
            print('Code edition/national survey currently not supported')

    def assign_masonry(self, parcel):
        # Assigns the wall width and determines necessary additional lateral support for the building considering its geometry:
        parcel.walls.ext['thickness'] = 8/12 #ft

        if parcel.walls.ext['loadbearing']:
            if parcel.walls.ext['construction'] == 'solid or solid grouted':
                max_lratio = 20
            else:
                max_lratio = 18
        else:
            if parcel.walls.subtype == 'nonbearing wall':
                max_lratio = 18
            else:
                max_lratio = 36

        #Based off of the maximum lateral support ratio, adjust the story height and add in additional walls:
        #for each story, calculate the height to width ratio of the masonry walls on that floor and if the ratio is bigger than allowed, reduce the height of the wall.
        allowed = max_lratio*parcel.walls.ext['thickness']

        # First check the wall heights:
        if parcel.walls.ext['height'] > allowed:
            parcel.walls.ext['height'] = allowed
        else:
            pass

        # Now check the wall lengths:
        if parcel.walls.ext['length'] > allowed:
            #If the wall length needs to be reduced, then a new wall spacing is required:
            #Could always assign a longer number of placeholders than needed based off of the smaller ratio...if you have a bigger ratio, then you would have less walls
            #We would then need to divide by something
            parcel.walls.ext['length'] = allowed
            # Since the length of the walls had to be reduced
        else:
            pass


#What we would like this class to do is define all of the relevant building parameters:
#Predominant exterior wall material
#roof pitch
#roof type
#


# test = parcel ('12345', 5, 'Hotel', 2002, 14, 15, "FL Panhandle")
# test2 = bldg_code(test)
