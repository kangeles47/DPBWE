#from asset import Parcel
import numpy as np
import random


class BldgCode:

    def __init__(self, parcel, desc_flag):
        # Building codes have editions:
        desc_flag = True
        self.hasEdition = self.get_edition(parcel, desc_flag)

    def get_edition(self, parcel, desc_flag):
        # Get the code edition considering parcel location, year built
        # For code-based rulesets (Parcels):
        if desc_flag:
            if parcel.hasLocation['State'] == 'FL':
                # Create an instance of FBC and assign its edition:
                if parcel.isComm:
                    if parcel.hasYearBuilt > 1988 & parcel.hasYearBuilt <= 1991:
                        if parcel.hasLocation['County'] != 'Broward' or parcel.hasLocation['County'] != 'Dade':
                            edition = '1988 SBC'
                        else:
                            edition = '1988 SFBC'
                    elif parcel.hasYearBuilt > 2001 & parcel.hasYearBuilt <= 2004:
                        edition = '2001 FBC - Building'
                    elif parcel.hasYearBuilt > 2004 & parcel.hasYearBuilt <= 2008:
                        edition = '2004 FBC - Building'
                    elif parcel.hasYearBuilt > 2008 & parcel.hasYearBuilt <= 2011:
                        edition = '2007 FBC - Building'
                    elif parcel.hasYearBuilt > 2011 & parcel.hasYearBuilt <= 2014:
                        edition = '2010 FBC - Building'
                    elif parcel.hasYearBuilt > 2014 & parcel.hasYearBuilt <= 2017:
                        edition = '2014 FBC - Building'
                    elif parcel.hasYearBuilt > 2017 & parcel.hasYearBuilt <= 2020:
                        edition = '2017 FBC - Building'
                    else:
                        print('Building code and edition currently not supported', parcel.hasYearBuilt)
                else:
                    if parcel.hasYearBuilt > 1983 & parcel.hasYearBuilt <= 1986:
                        edition = '1983 CABO'
                    elif parcel.hasYearBuilt > 1986 & parcel.hasYearBuilt <= 1989:
                        edition = '1986 CABO'
                    elif parcel.hasYearBuilt > 1989 & parcel.hasYearBuilt <= 1991:
                        edition = '1989 CABO'
                    elif parcel.hasYearBuilt > 1991 & parcel.hasYearBuilt <= 1995:
                        edition = '1992 CABO'
                    elif parcel.hasYearBuilt > 1995 & parcel.hasYearBuilt <= 2001:
                        edition = '1995 CABO'
                    elif parcel.hasYearBuilt > 2001 & parcel.hasYearBuilt <= 2004:
                        edition = '2001 FBC - Residential'
                    elif parcel.hasYearBuilt > 2004 & parcel.hasYearBuilt <= 2008:
                        edition = '2004 FBC - Residential'
                    elif parcel.hasYearBuilt > 2008 & parcel.hasYearBuilt <= 2011:
                        edition = '2007 FBC - Residential'
                    elif parcel.hasYearBuilt > 2011 & parcel.hasYearBuilt <= 2014:
                        edition = '2010 FBC - Residential'
                    elif parcel.hasYearBuilt > 2014 & parcel.hasYearBuilt <= 2017:
                        edition = '2014 FBC - Residential'
                    elif parcel.hasYearBuilt > 2017 & parcel.hasYearBuilt <= 2020:
                        edition = '2017 FBC - Residential'
                    else:
                        print('Building code and edition currently not supported', parcel.hasYearBuilt)
        else:
            # For code-informed capacities using ASCE 7:
            if parcel.hasYearBuilt <= 1988:
                edition = 'ASCE 7-88'
            elif 1988 < parcel.hasYearBuilt <= 1993:
                edition = 'ASCE 7-88'
            elif 1993 < parcel.hasYearBuilt <= 1995:
                edition = 'ASCE 7-93'
            elif 1995 < parcel.hasYearBuilt <= 1998:
                edition = 'ASCE 7-95'
            elif 1998 < parcel.hasYearBuilt <= 2002:
                edition = 'ASCE 7-98'
            elif 2002 < parcel.hasYearBuilt <= 2005:
                edition = 'ASCE 7-02'
            elif 2005 < parcel.hasYearBuilt <= 2010:
                edition = 'ASCE 7-05'
            elif 2010 < parcel.hasYearBuilt <= 2016:
                edition = 'ASCE 7-10'
            elif parcel.hasYearBuilt > 2016:
                edition = 'ASCE 7-16'
        return edition


class FBC(BldgCode):

    def __init__(self, parcel, desc_flag):
        BldgCode.__init__(self, parcel, desc_flag)  # Bring in building code attributes (edition)
        self.bldg_attributes(parcel)

    def bldg_attributes(self, parcel):
        # Knowing the code edition, populate this building-level code-informed attributes for the parcel:
        if parcel.hasLocation['State'] == 'FL':
            if 'FBC' in self.hasEdition or self.hasEdition == '1988 SBC':
                # 9 ft standard ceiling height - Add to each Storey in Building:
                for i in range(0, len(parcel.hasStorey)):
                    parcel.hasStorey[i].hasElevation = [9*i, 9*(i+1)]
                    parcel.hasStorey[i].hasHeight = 9
                parcel.hasHeight = len(parcel.hasStorey) * 9  # min. ceiling height used to calculate building height [ft]
            elif 'CABO' in self.hasEdition:
                # 8 ft standard ceiling height for older construction
                for i in range(0, len(parcel.hasStorey)):
                    parcel.hasStorey[i].hasElevation = [8*i, 8*(i+1)]
                    parcel.hasStorey[i].hasHeight = 8
                parcel.hasHeight = len(parcel.hasStorey) * 8  # min. ceiling height used to calculate building height [ft]
            else:
                print('Building level attributes currently not supported')
        else:
            print('Building level attributes currently not supported')

    def roof_attributes(self, edition, parcel, survey):

        #Populate roof attributes for this instance (parcel)
        roof_element = parcel.hasStorey[-1].containsElement['Roof']
        if edition == '2001 FBC' and survey == 'CBECS' and parcel.hasYearBuilt < 2003:
            # Assign qualitative descriptions of roof pitch given roof cover type from survey data:
            if roof_element.hasCover == 'Built-up' or roof_element.hasCover == 'Concrete' or roof_element.hasCover == 'Plastic/rubber/synthetic sheeting' or roof_element.hasCover == 'Metal surfacing':
                roof_element.hasPitch = 'flat'  # roof slopes under 2:12
                roof_element.hasShape = 'flat'
            elif roof_element.hasCover == 'Asphalt/fiberglass/other shingles' or roof_element.hasCover == 'Wood shingles/shakes/other wood' or roof_element.hasCover == 'Slate or tile shingles':
                roof_element.hasPitch = 'shallow or steeper'  # roof slopes 2:12 and greater
            else:
                roof_element.hasPitch = 'unknown'
        elif edition == '1988 SBC' and survey == 'CBECS' and parcel.hasYearBuilt < 1990:
            # Assign qualitative descriptions of roof pitch given roof cover type from survey data:
            roof_element = parcel.hasStorey[-1].containsElement['Roof']
            if roof_element.hasCover == 'Built-up' or roof_element.hasCover == 'Metal surfacing' or roof_element.hasCover == 'Single/multiple ply' or roof_element.hasCover == 'Concrete roof' or roof_element.hasCover == 'Metal & rubber' or roof_element.hasCover == 'Slate & built-up' or roof_element.hasCover == 'Built-up & metal' or roof_element.hasCover == 'Built-up & s/m ply':
                roof_element.hasPitch = 'flat'  # roof slopes under 2:12
                roof_element.hasShape = 'flat'
            elif roof_element.hasCover == 'Wooden materials' or roof_element.hasCover == 'Slate or tile' or roof_element.hasCover == 'Shingles (not wood)' or roof_element.hasCover == 'Shingles & metal':
                roof_element.hasPitch = 'shallow or steeper'  # roof slopes 2:12 and greater
            else:
                roof_element.hasPitch = 'unknown'
        else:
            # Assign qualitative descriptions of roof cover type given roof pitch from survey data:
            if roof_element.hasCover == None:
                if roof_element.hasPitch == 'flat':
                    roof_matls = ['Builtup', 'Concrete', 'Metal Surfacing', 'Synthetic or Rubber']
                    roof_weights = [211, 0, 244, 78]
                    roof_element.hasType = random.choices(roof_matls, roof_weights)
                elif roof_element.hasPitch == 'shallow':
                    roof_matls = ['Shingles (Not Wood)','Metal Surfacing', 'Wooden Materials']
                    roof_weights = [234, 244, 0]
                    roof_element.hasType = random.choices(roof_matls, roof_weights)
                elif roof_element.hasPitch == 'steeper':
                    roof_matls = ['Shingles (Not Wood)', 'Slate or Tile', 'Wooden Materials']
                    roof_weights = [234, 66, 0]
                    roof_element.hasType = random.choices(roof_matls, roof_weights)
                else:
                    print('Roof pitch not supported')
            else:
                print('Problem with roof cover/type attributes: check supporting data')


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

class ASCE7(BldgCode):

    def __init__(self, parcel, desc_flag):
        BldgCode.__init__(self, parcel, desc_flag)  # Bring in building code attributes (edition)

