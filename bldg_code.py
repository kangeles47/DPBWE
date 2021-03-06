import random
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from geopy import distance
from shapely.geometry import Point, LineString, Polygon
from code_pressures import PressureCalc
import math


class BldgCode:

    def __init__(self, parcel, loading_flag):
        # Building codes have editions:
        self.hasEdition = self.get_edition(parcel, loading_flag)

    def get_edition(self, parcel, loading_flag):
        # Get the code edition considering parcel location, year built
        # For code-based rulesets (Parcels):
        if not loading_flag:
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
            # For loading descriptions or component capacities using ASCE 7:
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

    def __init__(self, parcel, loading_flag):
        BldgCode.__init__(self, parcel, loading_flag)  # Bring in building code attributes (edition)
        self.bldg_attributes(parcel)

    def bldg_attributes(self, parcel):
        # Knowing the code edition, populate this building-level code-informed attributes for the parcel:
        if parcel.hasLocation['State'] == 'FL':
            if 'FBC' in self.hasEdition or self.hasEdition == '1988 SBC':
                # minimum ceiling height is 7 ft 6 inches - Add to each Story in Building:
                for i in range(0, len(parcel.hasStory)):
                    parcel.hasStory[i].hasElement['Ceiling'][0].hasElevation = parcel.hasStory[i].hasElevation[0] + 7.5
                    parcel.hasStory[i].hasElement['Ceiling'][0].hasGeometry['Height'] = 7.5
            elif 'CABO' in self.hasEdition:
                # minimum ceiling height is 7 ft 6 inches - Add to each Story in Building:
                for i in range(0, len(parcel.hasStory)):
                    parcel.hasStory[i].hasElement['Ceiling'][0].hasElevation = parcel.hasStory[i].hasElevation[0] + 7.5
                    parcel.hasStory[i].hasElement['Ceiling'][0].hasGeometry['Height'] = 7.5
            else:
                print('Building level attributes currently not supported')
        else:
            print('Building level attributes currently not supported')

    def roof_attributes(self, edition, parcel, survey):

        #Populate roof attributes for this instance (parcel)
        roof_element = parcel.hasStory[-1].hasElement['Roof'][0]
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

    def __init__(self, parcel, loading_flag):
        BldgCode.__init__(self, parcel, loading_flag)  # Bring in building code attributes (edition)

    # Code-informed zone and capacity designations:
    def assign_rmwfrs_pressures(self, bldg, edition, exposure, wind_speed):
        """
        Orchestrates designations of Roof MWFRS pressures to zone geometries.

        Provides parameters for get_roof_uplift pressures.
        Creates zone geometries using a minimum rectangle.
        Maps pressures to zones.
        Stores zone geometries and pressures for parallel and normal wind directions in Roof object.

        Parameters:
            bldg: A BOT: Building object
            edition: A string naming the edition of ASCE 7 wind loading provision for the building
            exposure: A string providing the ASCE 7 Exposure Category
            wind_speed: The wind speed the building is subject to
        """
        # Create an instance of PressureCalc:
        pressures = PressureCalc()
        # Assign MWFRS pressures for the roof:
        # Set up parameters to access pressures:
        # (1) Roof pitch
        roof_elem = bldg.hasStory[-1].hasElement['Roof'][0]
        if isinstance(roof_elem.hasPitch, str):
            if roof_elem.hasPitch == 'flat':
                # Assign angle based on 2:12 slope
                pitch = math.degrees(math.atan2(2, 12))
            else:
                print('Roof (str) pitch currently not supported')
        else:
            pass
        # (2) Direction and aspect ratios
        # Roof MWFRS pressure assignments require knowledge of the building aspect ratio for a given "wind direction"
        # (2a) Find the orientation of the building footprint using minimum rotated rectangle:
        rect = bldg.hasGeometry['Footprint']['local'].minimum_rotated_rectangle
        xrect, yrect = rect.exterior.xy
        xfpt, yfpt = bldg.hasGeometry['Footprint']['local'].exterior.xy
        theta = bldg.hasOrientation
        # (2b) Find the length of the rectangle's line segments:
        # Set up placeholders for Roof MWFRS pressures:
        info_rmwfrs = {'side length': [], 'wind direction': [], 'possible wind directions': [], 'direction length': [],
                       'pressures': []}
        # Set up placeholders for LineString objects of each line segment in rectangle:
        rlines1 = []  # for wind directions N-S and E-W
        rlines2 = []  # for wind directions S-N and W-E
        for coord in range(0, 4):
            if coord == 0 or coord == 3:
                new_line1 = LineString([(xrect[coord], yrect[coord]), (xrect[coord + 1], yrect[coord + 1])])
                new_line2 = LineString([(xrect[coord + 1], yrect[coord + 1]), (xrect[coord], yrect[coord])])
            else:
                # Reverse order the points in remaining line segments (useful for zone assignments later):
                new_line1 = LineString([(xrect[coord + 1], yrect[coord + 1]), (xrect[coord], yrect[coord])])
                new_line2 = LineString([(xrect[coord], yrect[coord]), (xrect[coord + 1], yrect[coord + 1])])
            rlines1.append(new_line1)
            rlines2.append(new_line2)
            info_rmwfrs['side length'].append(new_line1.length)
        # (3) Access roof uplift pressures:
        # To get correct pressures, need to know: wind blowing parallel or normal to ridge? AND length of opposite side
        # Store the RMWFRS pressures in dictionary:
        uplift_pressures = dict.fromkeys(['normal', 'parallel'])
        for j in range(0, 2):
            # Assume that the ridge runs along the longer dimension of the building:
            if info_rmwfrs['side length'][j] == max(info_rmwfrs['side length']):
                direction = 'parallel'
                dlength = min(info_rmwfrs['side length'])
                # Given the orientation of the building, find a set of parallel wind directions:
                real_directions = [180 - theta, 360 - theta]
            else:
                direction = 'normal'
                dlength = max(info_rmwfrs['side length'])
                # Given the orientation of the building, find a set of normal wind directions:
                real_directions = [theta, 180 + theta]
            # Save values for this "side" of the building:
            info_rmwfrs['wind direction'].append(direction)
            info_rmwfrs['direction length'].append(dlength)
            info_rmwfrs['possible wind directions'].append(real_directions)
            # Access pressures:
            psim = self.get_roof_uplift_pressure(edition, bldg, dlength, exposure, wind_speed, direction, pitch)
            info_rmwfrs['pressures'].append(psim)
            # (4) Assign zone pressures to the corresponding building geometry:
            prmwfrs = pd.DataFrame()
            prmwfrs['Uplift Pressure'] = psim
            # Need to create polygons to define zone locations:
            # Given wind directions according to station data conventions, pair zone geometries with pressures:
            for wdir in range(0, len(real_directions)):
                # Store the wind direction we are considering:
                dir_name = 'Direction' + str(wdir)
                dir_list = []
                for i in range(0, len(psim)):
                    dir_list.append(real_directions[wdir])
                prmwfrs[dir_name] = dir_list
                # Set up tag for 'ZonePolys' columns:
                zonepoly_name = 'ZonePolys' + str(wdir)
                if edition != 'ASCE 7-88' and edition != 'ASCE 7-93':
                    hdist = [bldg.hasGeometry['Height'] / 2, bldg.hasGeometry['Height'], bldg.hasGeometry['Height'] * 2]
                    if real_directions[wdir] == min(real_directions):
                        ref_lines = rlines1
                    else:
                        ref_lines = rlines2
                    # Zone Polygons can be defined by creating points along two parallel sides:
                    lst_points1 = [Point(ref_lines[j].coords[:][0])]
                    lst_points2 = [Point(ref_lines[j + 2].coords[:][0])]
                    for zone in range(0, len(psim)):
                        if zone == 3:  # Case when there are four zones:
                            pass
                        else:
                            # Create a new point along each line segment:
                            new_point1 = ref_lines[j].interpolate(hdist[zone])
                            new_point2 = ref_lines[j + 2].interpolate(hdist[zone])
                            # Add to the corresponding lists:
                            lst_points1.append(new_point1)
                            lst_points2.append(new_point2)
                    # Finish off with the last point in the line segment:
                    lst_points1.append(Point(ref_lines[j].coords[:][1]))
                    lst_points2.append(Point(ref_lines[j + 2].coords[:][1]))
                    # Create zone geometries:
                    poly_list = []
                    for pt in range(0, len(lst_points1) - 1):
                        rpoly = Polygon([lst_points1[pt], lst_points1[pt + 1], lst_points2[pt + 1],
                                         lst_points2[pt]])  # order ccw like min_rect
                        xpoly, ypoly = rpoly.exterior.xy
                        #plt.plot(xpoly, ypoly, label='Zone ' + str(pt + 1))
                        plt.plot(np.array(xpoly) / 3.281, np.array(ypoly) / 3.281,color='gray', linestyle='dashed')
                        # Add to DataFrame object:
                        poly_list.append(rpoly)
                    prmwfrs[zonepoly_name] = poly_list
                    #plt.legend()
                    plt.plot(np.array(xfpt)/3.281, np.array(yfpt)/3.281, 'k')
                    plt.xlabel('x [m]')
                    plt.ylabel('y [m]')
                    plt.show()
                else:
                    if direction == 'parallel':
                        pass
                    else:
                        pass
                # Once zone geometries have been defined and pressures mapped, store the Dataframe:
                uplift_pressures[direction] = prmwfrs
        bldg.hasElement['Roof'][0].hasCapacity['wind pressure']['total'].append(uplift_pressures)

    def get_roof_uplift_pressure(self, edition, bldg, length, exposure, wind_speed, direction, pitch):
        """
        Determines the roof uplift pressures per zone for the given building.

        This function begins by determining the ASCE7 Roof MWFRS use case for the building.
        It then conducts any necessary similitude mappings of pressures.

        Parameters:
            edition: A string naming the edition of ASCE 7 wind loading provision for the building
            bldg: A BOT: Building object
            length: The building length needed to calculate the h/L ratio to access roof MWFRS pressure coefficients
            exposure: A string providing the ASCE 7 Exposure Category
            wind_speed: The wind speed the building is subject to
            direction: A string describing the wind direction as either parallel or normal to the building's ridge
            pitch: The roof pitch needed to determine the appropriate use case for the building

        Returns:
            df: Zone pressures (row) for each zone number (columns)
        """
        # Step 1: Determine which reference building is needed and the file path:
        pressures = PressureCalc()  # Create an instance of PressureCalc to pull reference building parameters
        if direction == 'parallel' or (direction == 'normal' and pitch < 10):
            ref_exposure, ref_hstory, ref_hbldg, ref_pitch, ref_speed, ref_cat, hpr, h_ocean, encl_class = pressures.ref_bldg()
            file_path = 'C:/Users/Karen/PycharmProjects/DPBWE/Similitude Parameters/Roof_MWFRS/RBLDG1/'
        elif direction == 'normal' and (edition == 'ASCE 7-88' or edition == 'ASCE 7-93'):
            pass
        # Step 2: Determine the use case:
        ratio = bldg.hasGeometry['Height'] / length
        if edition == 'ASCE 7-88' or edition == 'ASCE 7-93':
            if direction == 'parallel':
                if ratio <= 2.5:
                    use_case = [3]
                elif ratio > 2.5:
                    use_case = [4]
            elif direction == 'normal':
                pass
        else:
            if direction == 'parallel' or (direction == 'normal' and pitch < 10):
                if ratio <= 0.5:
                    use_case = [1]
                elif ratio >= 1.0:
                    use_case = [2]
                elif 0.5 < ratio <= 1.0:
                    use_case = [1, 2]
                    iratios = [0.5, 1.0]
            elif direction == 'normal' and pitch >= 10:
                pass
        # Step 3: Determine which "family" of building codes will be needed (if necessary):
        if edition == 'ASCE 7-02' or edition == 'ASCE 7-05':
            edition = 'ASCE 7-98'
        elif edition == 'ASCE 7-88':
            edition = 'ASCE 7-93'
        # Step 4: Extract the respective reference pressure(s) for the use case(s):
        interp_pressures = []
        for case in range(0, len(use_case)):
            pref = pd.read_csv(file_path + 'ref' + str(use_case[case]) + '.csv', index_col='Edition').loc[[edition],:]
            # Step 5: Filter out any zones that are not needed for use cases 1 and 2:
            if use_case[case] == 1 and ratio == 0.5:
                pref = pref[pref.columns[0:3]]  # Case with only 3 zones
            elif use_case[case] == 2 and ratio == 2.0:
                pref = pref[pref.columns[0:1]]  # Case with only 1 zone
            # Step 5: Extract similitude parameters for wind speed, height, and exposure
            # Similitude in wind speed:
            if wind_speed == ref_speed:
                vfactor = 0.0
            else:
                # Check to see if similitude parameter will need to be interpolated:
                if wind_speed not in np.arange(70, 180, 5):
                    if wind_speed % 10 < 5:
                        v1 = wind_speed - wind_speed % 10
                        v2 = 5 - wind_speed % 10 + wind_speed
                    else:
                        v1 = wind_speed - wind_speed % 10 + 5
                        v2 = 10 - wind_speed % 10 + wind_speed
                    input_v = [int(v1), int(v2)]
                else:
                    input_v = [int(wind_speed)]
                # Pull wind speed similitude paramter:
                if edition == 'ASCE 7-93':
                    if len(input_v) == 1:
                        vfactor = pd.read_csv(file_path + 'v93.csv', index_col='Edition')[str(input_v[0])][edition]
                    else:
                        vfactor1 = pd.read_csv(file_path + 'v93.csv', index_col='Edition')[str(input_v[0])][edition]  # Leave here for now, for regional simulation will probably want to load everything somewhere outside
                        vfactor2 = pd.read_csv(file_path + 'v93.csv', index_col='Edition')[str(input_v[1])][edition]
                        vfactor = np.interp(wind_speed, input_v, [vfactor1, vfactor2])
                else:
                    if len(input_v) == 1:
                        vfactor = pd.read_csv(file_path + 'v.csv', index_col='Edition')[str(input_v[0])][edition]
                    else:
                        vfactor1 = pd.read_csv(file_path + 'v.csv', index_col='Edition')[str(input_v[0])][edition]  # Leave here for now, for regional simulation will probably want to load everything somewhere outside
                        vfactor2 = pd.read_csv(file_path + 'v.csv', index_col='Edition')[str(input_v[1])][edition]
                        vfactor = np.interp(wind_speed, input_v, [vfactor1, vfactor2])
            # Similitude in height:
            if bldg.hasGeometry['Height'] == ref_hbldg:
                hfactor = 0.0
            else:
                # First check if building height will need to be interpolated:
                if bldg.hasGeometry['Height'].is_integer():
                    input_height = [bldg.hasGeometry['Height']]
                else:
                    input_height = [math.floor(bldg.hasGeometry['Height']), math.ceil(bldg.hasGeometry['Height'])]
                if edition == 'ASCE 7-93':
                    if len(input_height) == 1:
                        hfactor = pd.read_csv(file_path + 'h93.csv')[str(input_height[0]) + ' ft'][0]
                    else:
                        hfactor1 = pd.read_csv(file_path + 'h93.csv')[str(input_height[0]) + ' ft'][0]
                        hfactor2 = pd.read_csv(file_path + 'h93.csv')[str(input_height[1]) + ' ft'][0]
                        hfactor = np.interp(bldg.hasGeometry['Height'], input_height, [hfactor1, hfactor2])
                else:
                    if len(input_height) == 1:
                        hfactor = pd.read_csv(file_path + 'h.csv')[str(input_height[0]) + ' ft'][0]
                    else:
                        hfactor1 = pd.read_csv(file_path + 'h.csv')[str(input_height[0]) + ' ft'][0]
                        hfactor2 = pd.read_csv(file_path + 'h.csv')[str(input_height[1]) + ' ft'][0]
                        hfactor = np.interp(bldg.hasGeometry['Height'], input_height, [hfactor1, hfactor2])
            # Similitude in exposure categories:
            if exposure == ref_exposure:
                efactor = 0.0
            else:
                efactor = pd.read_csv(file_path + 'e' + edition[-2:] + '.csv', index_col='Height in ft')[exposure][bldg.hasGeometry['Height']]
            # Step 6: Apply the similitude parameters to get the final pressures for each zone:
            factor_lst = [vfactor, hfactor, efactor]
            psim = pref.loc[edition]
            for factor in factor_lst:
                psim = factor * psim + psim
            # Interpolated use cases:
            if len(use_case) == 2:
                interp_pressures.append(psim)
                if case == 1 and use_case == [1,2]:
                    # Set up placeholder for interpolated pressures:
                    ip1 = np.interp(ratio, iratios, [interp_pressures[0][0], interp_pressures[1][0]])
                    ip2 = np.interp(ratio, iratios, [interp_pressures[0][1], interp_pressures[1][1]])
                    ip3 = np.interp(ratio, iratios, [interp_pressures[0][2], interp_pressures[1][1]])
                    ip4 = np.interp(ratio, iratios, [interp_pressures[0][3], interp_pressures[1][1]])
                    uplift_pressures = pd.Series([ip1, ip2, ip3, ip4], index=interp_pressures[0].index)
            else:
                uplift_pressures = psim
        return uplift_pressures

    def assign_wcc_pressures(self, bldg, zone_pts, edition, exposure, wind_speed):
        """
        Orchestrates the designation of pressures on the building facade.

        Provides parameters for get_wcc_pressures.
        Incorporates pressure minimums as needed.
        Uses each elements 1D (line) geometry to determine its Zone location.
        Maps component pressures according to zone location.
        Stores component pressures within each element's hasCapacity attribute.

        Parameters:
            bldg: A BOT: Building object
            zone_pts: A Dataframe with Start/End points (columns) for zones on building facade, per line segment (row)
            edition: A string naming the edition of ASCE 7 wind loading provision for the building
            exposure: A string providing the ASCE 7 Exposure Category
            wind_speed: The wind speed the building is subject to
        """
        # Create an instance of PressureCalc:
        pressures = PressureCalc()
        # Assign C&C pressures given the component type and its location (zone):
        for story in bldg.hasStory:
            # Create a list of all Wall C&C types within this story
            wcc_lst = pd.DataFrame(columns=['Element', 'Type'])
            for elem in story.adjacentElement['Walls']:
                if elem.isExterior and elem.inLoadPath:
                    # Figure out what ctype the wall component is:
                    ctype = pressures.get_ctype(elem)
                    wcc_lst = wcc_lst.append({'Element': elem, 'Type': ctype}, ignore_index=True)
                    elem.hasCapacity['type'].append('C&C Pressure')
                else:
                    pass
            # Find all unique C&C types and calculate (+)/(-) pressures at each zone:
            zone_pressures = pd.DataFrame(columns=['Type', 'Pressures'])
            for ctype in wcc_lst['Type'].unique():
                # (+)/(-) pressures:
                psim = self.get_wcc_pressure(edition, bldg.hasGeometry['Height'], story.hasGeometry['Height'], ctype,
                                        exposure, wind_speed, bldg.hasStory[-1].hasElement['Roof'][0].hasPitch)
                # Incorporate pressure minimums:
                if bldg.hasYearBuilt > 2010 and (abs(psim) < 16):  # [lb]/[ft^2]
                    if psim < 0:
                        psim = -16
                    else:
                        psim = 16
                else:
                    pass
                zone_pressures = zone_pressures.append({'Type': ctype, 'Pressures': psim}, ignore_index=True)
            # Assign zone pressures to each Wall C&C Element
            for elem in wcc_lst['Element']:
                zone4_flag = False
                # Use Zone 4 points and element coordinates to assign pressure
                for seg in range(0, len(zone_pts['NewZoneStart'])):
                    if not zone4_flag:
                        # Create a line segment using zone 4 points
                        zline = LineString([zone_pts['NewZoneStart'][seg], zone_pts['NewZoneEnd'][seg]])
                        # Check if element falls within the zone or is exactly at zone points or is outsidezone 4:
                        if Point(elem.hasGeometry['1D Geometry'].coords[0]).within(zline) and Point(
                                elem.hasGeometry['1D Geometry'].coords[1]).within(zline):
                            zone4_flag = True
                        elif Point(elem.hasGeometry['1D Geometry'].coords[0]) == zone_pts['NewZoneStart'][
                            seg] and Point(elem.hasGeometry['1D Geometry'].coords[1]) == zone_pts['NewZoneEnd'][seg]:
                            zone4_flag = True
                        else:
                            pass
                    else:
                        break
                # Find the element's C&C type:
                ectype = wcc_lst.loc[wcc_lst['Element'] == elem, 'Type'].iloc[0]
                # Find the index where the element C&C type matches with unique types in zone_pressures:
                utype_ind = zone_pressures[zone_pressures['Type'] == ectype].index.values
                if zone4_flag:
                    wp_dict = {'Positive': zone_pressures.iloc[utype_ind]['Pressures'][0]['Zone 4+'],
                               'Negative': zone_pressures.iloc[utype_ind]['Pressures'][0]['Zone 4-']}
                    elem.hasCapacity['value'].append(wp_dict)
                else:
                    wp_dict = {'Positive': zone_pressures.iloc[utype_ind]['Pressures'][0]['Zone 5+'],
                               'Negative': zone_pressures.iloc[utype_ind]['Pressures'][0]['Zone 5-']}
                    elem.hasCapacity['value'].append(wp_dict)

    def get_wcc_pressure(self, edition, h_bldg, h_story, ctype, exposure, wind_speed, pitch):
        """
        Determines the wall (facade) pressures per zone for the given building/component.

        This function begins by determining the ASCE7 edition and component use case.
        It then conducts any necessary similitude mappings of pressures.

        Parameters:
            edition: A string naming the edition of ASCE 7 wind loading provision for the building
            h_bldg: The building height
            h_story: The story height
            ctype: A string naming the component type
            exposure: A string providing the ASCE 7 Exposure Category
            wind_speed: The wind speed the building is subject to
            pitch: The roof pitch needed to determine the appropriate use case for the building

        Returns:
            df: Zone pressures (row) for each zone number (columns) and sign (e.g., Zone4+ vs. Zone4-)
        """
        # Step 1: Determine which "family" of building codes will be needed (if necessary):
        if edition == 'ASCE 7-02' or edition == 'ASCE 7-05':
            edition = 'ASCE 7-98'
        elif edition == 'ASCE 7-88':
            edition = 'ASCE 7-93'
        # Step 2: Access the appropriate reference building and determine the file path:
        pressures = PressureCalc()
        # Semantic translation for survey data:
        if pitch == 'flat':
            # Assign angle considering 2:12 slope
            pitch = math.degrees(math.atan(2 / 12))
        else:
            pitch = 11
        if h_story == 9 and pitch <= 10:  # [ft]
            ref_exposure, ref_hstory, ref_hbldg, ref_pitch, ref_speed, ref_cat, hpr, h_ocean, encl_class = pressures.ref_bldg()
            file_path = 'D:/Users/Karen/PycharmProjects/DPBWE/Similitude Parameters/Wall_CC/RBLDG1/'
        else:
            pass
        # Step 4: Extract the reference pressures for the component type
        pref = pd.read_csv(file_path + ctype + '/ref.csv', index_col='Edition').loc[[edition], :]
        # Step 5: Extract similitude parameters for wind speed, height, and exposure
        # Similitude in wind speed:
        if wind_speed == ref_speed:
            vfactor = 0.0
        else:
            if edition == 'ASCE 7-93':
                vfactor = pd.read_csv(file_path + '/v93.csv', index_col='Edition')[str(wind_speed)][edition]
            else:
                vfactor = pd.read_csv(file_path + '/v.csv', index_col='Edition')[str(wind_speed)][edition]
        # Similitude in height:
        if h_bldg == ref_hbldg:
            hfactor = 0.0
        else:
            if edition == 'ASCE 7-93':
                hfactor = pd.read_csv(file_path + '/h93.csv')[str(h_bldg) + ' ft'][0]
            else:
                hfactor = pd.read_csv(file_path + '/h.csv', index_col='Edition')[str(h_bldg) + ' ft'][edition]
        # Similitude in exposure categories:
        if exposure == ref_exposure:
            efactor = 0.0
        else:
            efactor = pd.read_csv(file_path + '/e' + edition[-2:] + '.csv', index_col='Height in ft')[exposure][h_bldg]
        # Step 6: Apply the similitude parameters to get the final pressures for each zone:
        factor_lst = [vfactor, hfactor, efactor]
        psim = pref.loc[edition]
        for factor in factor_lst:
            psim = factor * psim + psim
        return psim

    def assign_rcc_pressures(self, bldg, zone_pts, int_poly, edition, exposure, wind_speed):
        """
        Orchestrates the designation of C&C pressures on roof.

        Provides parameters for get_rcc_pressures.
        Incorporates pressure minimums as needed.
        In progress: Uses each element's geometry to determine its Zone location.
        Maps component pressures according to zone location.
        Stores component pressures within each element's hasCapacity attribute.

        Parameters:
            bldg: A BOT: Building object
            zone_pts: A Dataframe with Start/End points (columns) for zones on building facade, per line segment (row)
            int_poly: A Shapely Polygon object marking Zone 1 location (ASCE 7 editions < 7-16)
            zone2_polys: Shapely Polygon objects marking Zone 2 locations (ASCE 7 editions < 7-16)
            edition: A string naming the edition of ASCE 7 wind loading provision for the building
            exposure: A string providing the ASCE 7 Exposure Category
            wind_speed: The wind speed the building is subject to
        """
        # Create an instance of PressureCalc:
        pressures = PressureCalc()
        # Assign C&C pressures given the component type and its location (zone):
        roof_elem = bldg.hasStory[-1].hasElement['Roof'][0]
        # Create a list of all C&C types within the roof:
        rcc_lst = pd.DataFrame(columns=['Element', 'Type'])
        # Figure out what ctype the main roof component is:
        ctype = pressures.get_ctype(roof_elem)
        rcc_lst = rcc_lst.append({'Element': roof_elem, 'Type': ctype}, ignore_index=True)
        # Figure out what the ctype is for any additional roof components:
        if roof_elem.hasSubElement is None:
            bldg.hasStory[-1].hasElement['Roof'][0].hasCapacity['type'].append('C&C Pressure')
            # Figure out what ctype the roof cover is:
            ctype = pressures.get_ctype(roof_elem)
            rcc_lst = rcc_lst.append({'Element': roof_elem, 'Type': ctype}, ignore_index=True)
        else:
            for elem in roof_elem.hasSubElement:
                # Figure out what ctype the roof component is:
                ctype = pressures.get_ctype(elem)
                rcc_lst = rcc_lst.append({'Element': elem, 'Type': ctype}, ignore_index=True)
        # Find all unique C&C types and calculate (+)/(-) pressures at each zone:
        zone_pressures = pd.DataFrame(columns=['Type', 'Pressures'])
        for ctype in rcc_lst['Type'].unique():
            # (+)/(-) pressures:
            psim = self.get_rcc_pressure(edition, bldg.hasGeometry['Height'], ctype, exposure, wind_speed,
                                    roof_elem.hasPitch)
            # Incorporate pressure minimums:
            if bldg.hasYearBuilt > 2010 and (abs(psim) < 16):  # [lb]/[ft^2]
                if psim < 0:
                    psim = -16
                else:
                    psim = 16
            else:
                pass
            zone_pressures = zone_pressures.append({'Type': ctype, 'Pressures': psim}, ignore_index=True)
        # Assign zone pressures to each Roof C&C Element:
        for elem in rcc_lst['Element']:
            zone2_flag = False
            zone1_flag = False
            # Use Zone 4 points and element coordinates to assign pressure
            for seg in zone_pts['NewZoneStart']:
                if not zone2_flag and not zone1_flag:
                    # Create a line segment using zone 4 points
                    zline = LineString([zone_pts['NewZoneStart'][seg], zone_pts['NewZoneEnd'][seg]])
                    # Check if element falls within the zone or is exactly at zone points or is outsidezone 4:
                    if elem.hasGeometry['1D Geometry'][0].within(zline) and elem.hasGeometry['1D Geometry'][1].within(
                            zline):
                        zone2_flag = True
                    elif elem.hasGeometry['1D Geometry'][0] == zone_pts['NewZoneStart'][seg] and \
                            elem.hasGeometry['1D Geometry'][1] == zone_pts['NewZoneEnd'][seg]:
                        zone2_flag = True
                    elif elem.hasGeometry['1D Geometry'][0].within(int_poly):
                        zone1_flag = True
                    else:
                        pass
                else:
                    break
            # Find the index where zone_pressures['Type'] matches the element's C&C type:
            etype_ind = rcc_lst.loc[rcc_lst['Element'] == elem]
            type_ind = zone_pressures.loc[zone_pressures['Type'] == rcc_lst['Type'][etype_ind]]
            if zone2_flag:
                rp_dict = {'Positive': zone_pressures['Pressures'][type_ind]['Zone2+'],
                           'Negative': zone_pressures['Pressures'][type_ind]['Zone2-']}
                elem.hasCapacity['value'] = rp_dict
            elif zone1_flag:
                rp_dict = {'Positive': zone_pressures['Pressures'][type_ind]['Zone1+'],
                           'Negative': zone_pressures['Pressures'][type_ind]['Zone1-']}
                elem.hasCapacity['value'] = rp_dict
            else:
                rp_dict = {'Positive': zone_pressures['Pressures'][type_ind]['Zone3+'],
                           'Negative': zone_pressures['Pressures'][type_ind]['Zone3-']}
                elem.hasCapacity['value'] = rp_dict

    def get_rcc_pressure(self, edition, h_bldg, ctype, exposure, wind_speed, pitch):
        """
        Determines the roof uplift pressures per zone for the given building.

        This function begins by determining the ASCE7 Roof MWFRS use case for the building.
        It then conducts any necessary similitude mappings of pressures.

        Parameters:
            edition: A string naming the edition of ASCE 7 wind loading provision for the building
            h_bldg: The building height
            ctype: A string naming the component type
            exposure: A string providing the ASCE 7 Exposure Category
            wind_speed: The wind speed the building is subject to
            pitch: The roof pitch needed to determine the appropriate use case for the building

        Returns:
            df: Zone pressures (row) for each zone number (columns) and sign (e.g., Zone1+ vs. Zone1-)
        """
        # Step 1: Semantic translation of roof pitch:
        if pitch == 'flat':
            # Code editions ASCE 7-98 and earlier use 10 degrees for first use case
            # Code editions ASCE 7-02 and later use 7 degrees for first use case
            # Assign angle < 7 degrees:
            pitch = 6
        # Step 2: Determine which "family" of building codes will be needed (if necessary):
        if pitch < 7:
            if edition == 'ASCE 7-02' or edition == 'ASCE 7-05':
                edition = 'ASCE 7-98'
        else:
            pass
        if edition == 'ASCE 7-88':
            edition = 'ASCE 7-93'
        # Step 2: Access the appropriate reference building and determine the file path:
        pressures = PressureCalc()
        # NOTE: Might need to modify logic here once we add more reference buildings
        if edition == 'ASCE 7-98' or edition == 'ASCE 7-93':
            if pitch <= 10:
                use_case = 1
                ref_exposure, ref_hstory, ref_hbldg, ref_pitch, ref_speed, ref_cat, hpr, h_ocean, encl_class = pressures.ref_bldg()
                file_path = 'D:/Users/Karen/PycharmProjects/DPBWE/Similitude Parameters/Roof_CC/RBLDG1/'
        else:
            if (
                    edition == 'ASCE 7-02' or edition == 'ASCE 7-05' or edition == 'ASCE 7-10') and pitch <= 7:  # Still including this logic for non-Parcel models
                use_case = 1
                ref_exposure, ref_hstory, ref_hbldg, ref_pitch, ref_speed, ref_cat, hpr, h_ocean, encl_class = pressures.ref_bldg()
                file_path = 'D:/Users/Karen/PycharmProjects/DPBWE/Similitude Parameters/Roof_CC/RBLDG1/'
            elif (edition == 'ASCE 7-02' or edition == 'ASCE 7-05' or edition == 'ASCE 7-10') and 7 < pitch <= 27:
                use_case = 2
                print('Roof use case currently not supported')
        # Step 4: Extract the reference pressures for component type -- COME BACK AND CHECK FOR OTHER USE CASES
        pref = pd.read_csv(file_path + ctype + '/ref' + str(use_case) + '.csv', index_col='Edition').loc[[edition], :]
        # Step 5: Extract similitude parameters for wind speed, height, and exposure
        # Similitude in wind speed:
        if wind_speed == ref_speed:
            vfactor = 0.0
        else:
            if edition == 'ASCE 7-93':
                vfactor = pd.read_csv(file_path + '/v93.csv', index_col='Edition')[str(wind_speed)][edition]
            else:
                vfactor = pd.read_csv(file_path + '/v.csv', index_col='Edition')[str(wind_speed)][edition]
        # Similitude in height:
        if h_bldg == ref_hbldg:
            hfactor = 0.0
        else:
            if edition == 'ASCE 7-93':
                hfactor = pd.read_csv(file_path + '/h93.csv')[str(h_bldg) + ' ft'][0]
            else:
                hfactor = pd.read_csv(file_path + '/h.csv', index_col='Edition')[str(h_bldg) + ' ft'][edition]
        # Similitude in exposure categories:
        if exposure == ref_exposure:
            efactor = 0.0
        else:
            efactor = pd.read_csv(file_path + '/e' + edition[-2:] + '.csv', index_col='Height in ft')[exposure][h_bldg]
        # Step 6: Apply the similitude parameters to get the final pressures for each zone:
        factor_lst = [vfactor, hfactor, efactor]
        psim = pref.loc[edition]
        for factor in factor_lst:
            psim = factor * psim + psim
        return psim

    def get_cc_zone_width(self, bldg):
        """ Calculates and returns the ASCE 7 zone width, a, for C&C pressures."""
        # Create an equivalent rectangle for the building:
        rect = bldg.hasGeometry['Footprint'][
            'geodesic'].minimum_rotated_rectangle  # Note: min rect. (not constrained || to coord axis)
        xrect, yrect = rect.exterior.xy
        # Find the least horizontal dimension of the building:
        for ind in range(0, len(xrect) - 1):
            hnew = distance.distance((yrect[ind], xrect[ind]), (yrect[ind + 1], xrect[ind + 1])).miles * 5280  # [ft]
            if ind == 0:
                hdist = hnew
            else:
                if hnew < hdist:
                    hdist = hnew
                else:
                    pass
        a = max(min(0.1 * hdist, 0.4 * bldg.hasGeometry['Height']), 0.04 * hdist, 3)
        return a

    def find_cc_zone_points(self, bldg, zone_width, roof_flag, edition):
        """
        Determines the building's C&C zone start/end points.

        This function uses the building footprint to find C&C zone locations on the building envelope.
        It includes options to calculate both facade and roof zones or only facade zones.

        Parameters:
            bldg: A BOT: Building object
            zone_width: The ASCE 7 zone width, a
            roof_flag: Boolean indicating if roof zones need to be determined (Yes/No, True/False)
            edition: A string naming the edition of ASCE 7 wind loading provision for the building

        Returns:
            zone_pts: A Dataframe with Start/End points (columns) for zones on building facade, per line segment (row).
            int_poly: A Shapely Polygon object marking Zone 1 location (ASCE 7 editions < 7-16)
            zone2_polys: Shapely Polygon objects marking Zone 2 locations (ASCE 7 editions < 7-16)
        """
        # Use the building footprint to find zone boundaries around perimeter:
        xc, yc = bldg.hasGeometry['Footprint']['local'].exterior.xy
        # Find points along building footprint corresponding to zone start/end
        zone_pts = pd.DataFrame(columns=['LinePoint1', 'NewZoneStart', 'NewZoneEnd', 'LinePoint2'])
        for j in range(0, len(xc) - 1):
            # Leverage Shapely LineStrings to find zone start/end points:
            line1 = LineString([(xc[j], yc[j]), (xc[j + 1], yc[j + 1])])
            line2 = LineString([(xc[j + 1], yc[j + 1]), (xc[j], yc[j])])
            point1 = line1.interpolate(zone_width)
            point2 = line2.interpolate(zone_width)
            # Create Shapely Point Objects and store in DataFrame:
            zone_pts = zone_pts.append({'LinePoint1': Point(xc[j], yc[j]), 'NewZoneStart': point1, 'NewZoneEnd': point2,
                                        'LinePoint2': Point(xc[j + 1], yc[j + 1])}, ignore_index=True)
            # Plot points:
            plt.scatter(point1.x, point1.y)
            plt.scatter(point2.x, point2.y)
            # Plot line segment:
            lx, ly = line1.xy
            plt.plot(lx, ly)
        plt.show()
        # Note: zone_pts returns planar coordinates of zone locations
        # Apply to walls with 'NewZoneStart/End' corresponding to Start/End of Zone 4 locations
        # Apply to roof with 'NewZoneStart/End' corresponding to Start/End of Zone 2 locations
        # Roof C&C components additionally have an "interior" zone --> Zone 1
        if roof_flag:
            if edition != 'ASCE 7-16':
                # Derive Zone 1 points from original bldg footprint:
                int_poly = bldg.hasGeometry['Footprint']['local'].buffer(distance=-1 * zone_width, resolution=300,
                                                                         join_style=2)
                # Leave as poly - can easily check if component in/out of geometry
                # Plot for reference
                xpoly, ypoly = int_poly.exterior.xy
                plt.plot(xc, yc)
                plt.plot(xpoly, ypoly)
                plt.show()
                # Find geometries for Zone 2 Locations using zone points
                zone2_polys = []
                for row in range(0, len(zone_pts)):
                    # Create a line object using zone points:
                    zpoint1 = zone_pts['NewZoneStart'].iloc[row]
                    zpoint2 = zone_pts['NewZoneEnd'].iloc[row]
                    zone_line = LineString([zpoint1, zpoint2])
                    point_list = zone_line.coords[:]
                    # Offset the line by the zone width:
                    if (zpoint1.x < zpoint2.x) and (zpoint1.y == zpoint2.y) and (
                            zpoint1.y > bldg.hasGeometry['Footprint']['local'].centroid.y):
                        offset_line = zone_line.parallel_offset(zone_width, side='right')
                        point_list.append(offset_line.coords[0])
                        point_list.append(offset_line.coords[1])
                    else:
                        offset_line = zone_line.parallel_offset(-1 * zone_width, side='right')
                        point_list.append(offset_line.coords[1])
                        point_list.append(offset_line.coords[0])
                    # Create a new polygon using the points in both lines:
                    new_poly = Polygon(point_list)
                    zone2_polys.append(new_poly)
                    # Plotting:
                    xz, yz = new_poly.exterior.xy
                    plt.plot(xz, yz)
                # Plot int_poly
                plt.plot(xc, yc)
                plt.plot(xpoly, ypoly)
                plt.show()
            elif edition == 'ASCE 7-16':
                print('Code edition currently not supported for Roof MWFRS considerations')
        else:
            int_poly = None
            zone2_polys = None

        return zone_pts, int_poly, zone2_polys