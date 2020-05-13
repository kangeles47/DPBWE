# from parcel import parcel
import numpy as np
import random


class BldgCode:

    def __init__(self, parcel):
        # First determine what code we need to pull based off of the location and year built:
        if parcel.state == "FL":
            if parcel.is_comm:
                if parcel.yr_built > 1988 & parcel.yr_built <= 1991:
                    if parcel.county != 'Broward' or parcel.county != 'Dade':
                        self.edition = '1988 SBC'
                    else:
                        self.edition = '1988 SFBC'
                elif parcel.yr_built > 2001 & parcel.yr_built <= 2004:
                    self.edition = '2001 FBC - Building'
                elif parcel.yr_built > 2004 & parcel.yr_built <= 2008:
                    self.edition = '2004 FBC - Building'
                elif parcel.yr_built > 2008 & parcel.yr_built <= 2011:
                    self.edition = '2007 FBC - Building'
                elif parcel.yr_built > 2011 & parcel.yr_built <= 2014:
                    self.edition = '2010 FBC - Building'
                elif parcel.yr_built > 2014 & parcel.yr_built <= 2017:
                    self.edition = '2014 FBC - Building'
                elif parcel.yr_built > 2017 & parcel.yr_built <= 2020:
                    self.edition = '2017 FBC - Building'
                else:
                    print('Building code and edition currently not supported', parcel.yr_built)
            else:
                if parcel.yr_built > 1983 & parcel.yr_built <= 1986:
                    self.edition = '1983 CABO'
                elif parcel.yr_built > 1986 & parcel.yr_built <= 1989:
                    self.edition = '1986 CABO'
                elif parcel.yr_built > 1989 & parcel.yr_built <= 1991:
                    self.edition = '1989 CABO'
                elif parcel.yr_built > 1991 & parcel.yr_built <= 1995:
                    self.edition = '1992 CABO'
                elif parcel.yr_built > 1995 & parcel.yr_built <= 2001:
                    self.edition = '1995 CABO'
                elif parcel.yr_built > 2001 & parcel.yr_built <= 2004:
                    self.edition = '2001 FBC - Residential'
                elif parcel.yr_built > 2004 & parcel.yr_built <= 2008:
                    self.edition = '2004 FBC - Residential'
                elif parcel.yr_built > 2008 & parcel.yr_built <= 2011:
                    self.edition = '2007 FBC - Residential'
                elif parcel.yr_built > 2011 & parcel.yr_built <= 2014:
                    self.edition = '2010 FBC - Residential'
                elif parcel.yr_built > 2014 & parcel.yr_built <= 2017:
                    self.edition = '2014 FBC - Residential'
                elif parcel.yr_built > 2017 & parcel.yr_built <= 2020:
                    self.edition = '2017 FBC - Residential'
                else:
                    print('Building code and edition currently not supported', parcel.yr_built)
        # Knowing the building code and edition, populate bldg level attributes:
        self.bldg_attributes(self.edition, parcel)

    def bldg_attributes(self, edition, parcel):
        # Knowing the code edition, populate this building-level code-informed attributes for the parcel:
        if parcel.state == "FL":
            if parcel.is_comm:
                if 'FBC' in edition or edition == '1988 SBC':
                    # 9 ft standard ceiling height
                    parcel.h_story = np.arange(9, 9 * parcel.num_stories, parcel.num_stories)/3.281  # story elevations (meters)
                    parcel.h_bldg = parcel.num_stories * 9/3.281  # min. ceiling height used to calculate building height (meters)
                    parcel.num_rooms = 6 #assigning number of rooms based off of occupancy, structural system
                    #self.roof_survey_data(self.edition, parcel) #populate missing data for the parcel from national survey (CBECS)
                else:
                    print('Building level attributes currently not supported')
            else:
                if 'FBC' in edition:
                    # Story height, building height, number of rooms
                    # 9 ft standard ceiling height
                    parcel.h_story = np.arange(9, 9*parcel.num_stories, parcel.num_stories)/3.281  # story elevations (meters)
                    parcel.h_bldg = parcel.num_stories * 9/3.281  # min. ceiling height used to calculate building height
                elif 'CABO' in edition:
                    # 8 ft standard ceiling height for older construction
                    parcel.h_story = np.arange(8, 8 * parcel.num_stories, parcel.num_stories)/3.281
                    parcel.h_bldg = parcel.num_stories * 8/3.281

    def roof_attributes(self, edition, parcel, survey):

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
