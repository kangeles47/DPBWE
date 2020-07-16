import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from geopy import distance
from shapely.geometry import Point, LineString, Polygon
from code_pressures import PressureCalc
from BIM import Parcel
import math

# Goal of this code is to extract the information necessary to assign the correct pressure to building components
# General sequence:
# (1) Provide a building model:
# (2) Conduct an inventory of its components:
# (3) Given those components and the building model:
#   a) Access the correct reference pressures
#   b) Conduct the necessary similitude mappings
#   c) Assign pressures for each zone to the appropriate locations for the building model
def get_roof_uplift_pressure(edition, h_bldg, length, exposure, wind_speed, direction, pitch):
    # Step 1: Determine which reference building is needed and the file path:
    pressures = PressureCalc()  # Create an instance of PressureCalc to pull reference building parameters
    if direction == 'parallel' or (direction == 'normal' and pitch < 10):
        ref_exposure, ref_hstory, ref_hbldg, ref_pitch, ref_speed, ref_cat, hpr, h_ocean, encl_class = pressures.ref_bldg()
        file_path = 'D:/Users/Karen/Documents/Github/DPBWE/Similitude Parameters/Roof_MWFRS/RBLDG1/'
    # Step 2: Determine the use case:
    ratio = h_bldg/length
    if edition == 'ASCE 7-88' or edition == 'ASCE 7-93':
        if direction == 'parallel':
            if ratio <= 2.5:
                use_case = 3
            elif ratio > 2.5:
                use_case = 4
        elif direction == 'normal':
            pass
    else:
        if direction == 'parallel' or (direction == 'normal' and pitch < 10):
            if ratio <= 0.5:
                use_case = 1
            elif ratio >= 1.0:
                use_case = 2
        elif direction == 'normal' and pitch >= 10:
            pass
    # Step 3: Determine which "family" of building codes will be needed (if necessary):
    if edition == 'ASCE 7-02' or edition == 'ASCE 7-05':
        edition = 'ASCE 7-98'
    elif edition == 'ASCE 7-88':
        edition = 'ASCE 7-93'
    # Step 4: Extract the respective reference pressure for the use case:
    pref = pd.read_csv(file_path + 'ref' + str(use_case) + '.csv', index_col='Edition').loc[[edition], :]
    # Step 5: Filter out any zones that are not needed for use cases 1 and 2:
    if use_case == 1 and ratio == 0.5:
        pref = pref[pref.columns[0:3]]  # Case with only 3 zones
    elif use_case == 2 and ratio == 2.0:
        pref = pref[pref.columns[0:1]] # Case with only 1 zone
    # Step 5: Extract similitude parameters for wind speed, height, and exposure
    # Similitude in wind speed:
    if wind_speed == ref_speed:
        vfactor = 0.0
    else:
        if edition == 'ASCE 7-93':
            vfactor = pd.read_csv(file_path + 'v93.csv', index_col='Edition')[str(wind_speed)][edition]
        else:
            vfactor = pd.read_csv(file_path + 'v.csv', index_col='Edition')[str(wind_speed)][edition] # Leave here for now, for regional simulation will probably want to load everything somewhere outside
    # Similitude in height:
    if h_bldg == ref_hbldg:
        hfactor = 0.0
    else:
        if edition == 'ASCE 7-93':
            hfactor = pd.read_csv(file_path + 'h93.csv')[str(h_bldg) + ' ft'][0]
        else:
            hfactor = pd.read_csv(file_path + 'h.csv')[str(h_bldg) + ' ft'][0]
    # Similitude in exposure categories:
    if exposure == ref_exposure:
        efactor = 0.0
    else:
        efactor = pd.read_csv(file_path + 'e' + edition[-2:] + '.csv', index_col='Height in ft')[exposure][h_bldg]
    # Step 6: Apply the similitude parameters to get the final pressures for each zone:
    factor_lst = [vfactor, hfactor, efactor]
    psim = pref.loc[edition]
    for factor in factor_lst:
        psim = factor*psim + psim
    return psim

def get_wcc_pressure(edition, h_bldg, h_story, ctype, exposure, wind_speed, pitch):
    # Step 1: Determine which "family" of building codes will be needed (if necessary):
    if edition == 'ASCE 7-02' or edition == 'ASCE 7-05':
        edition = 'ASCE 7-98'
    elif edition == 'ASCE 7-88':
        edition = 'ASCE 7-93'
    # Step 2: Access the appropriate reference building and determine the file path:
    pressures = PressureCalc()
    if h_story == 9 and pitch <= 10:  #[ft]
        ref_exposure, ref_hstory, ref_hbldg, ref_pitch, ref_speed, ref_cat, hpr, h_ocean, encl_class = pressures.ref_bldg()
        file_path = 'D:/Users/Karen/Documents/Github/DPBWE/Similitude Parameters/Wall_CC/RBLDG1/'
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
            vfactor = pd.read_csv(file_path + ctype + '/v93.csv', index_col='Edition')[str(wind_speed)][edition]
        else:
            vfactor = pd.read_csv(file_path + ctype + '/v.csv', index_col='Edition')[str(wind_speed)][edition]
    # Similitude in height:
    if h_bldg == ref_hbldg:
        hfactor = 0.0
    else:
        if edition == 'ASCE 7-93':
            hfactor = pd.read_csv(file_path + ctype + '/h93.csv')[str(h_bldg) + ' ft'][0]
        else:
            hfactor = pd.read_csv(file_path + ctype + '/h.csv', index_col='Edition')[str(h_bldg) + ' ft'][edition]
    # Similitude in exposure categories:
    if exposure == ref_exposure:
        efactor = 0.0
    else:
        efactor = pd.read_csv(file_path + ctype + '/e' + edition[-2:] + '.csv', index_col='Height in ft')[exposure][h_bldg]
    # Step 6: Apply the similitude parameters to get the final pressures for each zone:
    factor_lst = [vfactor, hfactor, efactor]
    psim = pref.loc[edition]
    for factor in factor_lst:
        psim = factor*psim + psim
    return psim

def get_zone_width(bldg):
    # This function determines the zone width, a, for a given building:
    # a is determined as max(min(0.1*least horizontal dimension, 0.4*h_bldg), 0.4*least horizontal direction, 3 ft)
    # Create an equivalent rectangle for the building:
    rect = bldg.footprint["geometry"].minimum_rotated_rectangle  # Note: min rect. (not constrained || to coord axis)
    xrect, yrect = rect.exterior.xy
    # Find the least horizontal dimension of the building:
    for ind in range(0, len(xrect)-1):
        hnew = distance.distance((yrect[ind], xrect[ind]), (yrect[ind+1], xrect[ind+1])).miles * 5280  # [ft]
        if ind == 0:
            hdist = hnew
        else:
            if hnew < hdist:
                hdist = hnew
            else:
                pass
    a = max(min(0.1*hdist, 0.4*bldg.h_bldg), 0.04*hdist, 3)
    return a

def find_zone_points(bldg, zone_width):
    # Use the building footprint to find zone boundaries around perimeter:
    xs, ys = bldg.footprint["geometry"].exterior.xy
    # Find the distance between exterior points and the building centroid (origin) to define a new coordinate system:
    origin = bldg.footprint['geometry'].centroid
    xc = []
    yc = []
    for ind in range(0, len(xs)):
        # Find the distance between x, y at origin and x, y for each point:
        xdist = distance.distance((origin.y, origin.x), (origin.y, xs[ind])).miles * 5280  # [ft]
        ydist = distance.distance((origin.y, origin.x), (ys[ind], origin.x)).miles * 5280  # [ft]
        if xs[ind] < origin.x:
            xdist = -1*xdist
        else:
            pass
        if ys[ind] < origin.y:
            ydist = -1*ydist
        else:
            pass
        xc.append(xdist)
        yc.append(ydist)
    # Find points along building footprint corresponding to zone start/end
    zone_pts = pd.DataFrame(columns=['LinePoint1', 'Zone4Start', 'Zone4End', 'LinePoint2'])
    for j in range(0, len(xc)-1):
        # Leverage Shapely LineStrings to find zone start/end points:
        line1 = LineString([(xc[j], yc[j]), (xc[j+1], yc[j+1])])
        line2 = LineString([(xc[j+1], yc[j+1]), (xc[j], yc[j])])
        point1 = line1.interpolate(zone_width)
        point2 = line2.interpolate(zone_width)
        # Create Shapely Point Objects and store in DataFrame:
        zone_pts = zone_pts.append({'LinePoint1': Point(xc[j], yc[j]), 'Zone4Start': point1, 'Zone4End': point2, 'LinePoint2': Point(xc[j+1], yc[j+1])}, ignore_index=True)
        # Plot points:
        plt.scatter(point1.x, point1.y)
        plt.scatter(point2.x, point2.y)
        # Plot line segment:
        lx, ly = line1.xy
        plt.plot(lx,ly)
    plt.show()
    return zone_pts

def assign_wcc_pressures(bldg, zone_pts, exposure, wind_speed):
    # Assign C&C pressures given the component type and its location (zone):
    for story in bldg.h_bldg:
        # Create a list of all Wall C&C types within this story
        wcc_lst = pd.DataFrame(columns=['Element', 'Type'])
        for elem in bldg.has_element['Walls']:
            if elem.is_exterior == True and elem.is_loadbearing == False:
                wcc_lst = wcc_lst.append({'Element': elem, 'Type': elem.type}, ignore_index=True)
            else:
                pass
        # Find all unique C&C types and calculate (+)/(-) pressures at each zone:
        zone_pressures = pd.DataFrame(columns=['Type', 'Pressures'])
        for type in wcc_lst['Type'].unique():
            # (+)/(-) pressures:
            psim = get_wcc_pressure(edition, bldg.h_bldg, bldg.h_story, type, exposure, wind_speed, bldg.roof.pitch)
            zone_pressures = zone_pressures.append({'Type': type, 'Pressures': psim}, ignore_index=True)
        # Assign zone pressures to each Wall C&C Element
        for elem in wcc_lst['Element']:
            zone4_flag = False
            # Use Zone 4 points and element coordinates to assign pressure
            for seg in zone_pts['Zone4Start']:
                if zone4_flag == False:
                    # Create a line segment using zone 4 points
                    zline = LineString([zone_pts['Zone4Start'][seg], zone_pts['Zone4End'][seg]])
                    # Check if element falls within the zone or is exactly at zone points or is outsidezone 4:
                    if elem.has_2Dgeometry[0].within(zline) and elem.has_2Dgeometry[1].within(zline):
                        zone4_flag = True
                    elif elem.has_2Dgeometry[0] == zone_pts['Zone4Start'][seg] and elem.has_2Dgeometry[1] ==zone_pts['Zone4End'][seg]:
                        zone4_flag = True
                    else:
                        pass
                else:
                    break
            # Find the index where zone_pressures['Type'] matches the C&C type:
            type_ind = zone_pressures.loc[zone_pressures['Type']==elem.has_type]
            if zone4_flag:
                elem.has_capacity['Positive'] = zone_pressures['Pressures'][type_ind]['Zone4+']
                elem.has_capacity['Negative'] = zone_pressures['Pressures'][type_ind]['Zone4-']
            else:
                elem.has_capacity['Positive'] = zone_pressures['Pressures'][type_ind]['Zone5+']
                elem.has_capacity['Negative'] = zone_pressures['Pressures'][type_ind]['Zone5-']
            
def dist_calc(lon1, lat1, lon2, lat2):
    # Calculate distance between two longitude, latitude points using the Haversine formula:
    earth_radius = 3958.8*5280  # radius of Earth in [ft]
    phi_1 = math.radians(lat1)
    phi_2 = math.radians(lat2)

    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2.0) ** 2 + math.cos(phi_1) * math.cos(phi_2) * math.sin(delta_lambda / 2.0) ** 2

    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    dist = earth_radius * c  # output distance in [ft]

    return dist


#lon = -85.676188
#lat = 30.190142
#test = Parcel('12345', 4, 'Financial', 1989, '1002 23RD ST W PANAMA CITY 32405', 41134, lon, lat)
#lon = -85.666162
#lat = 30.19953
#test = Parcel('12989-113-000', 1, 'SINGLE FAM', 1974, '2820  STATE AVE   PANAMA CITY 32405', 3141, lon, lat)
#a = get_zone_width(test)
#print('zone width in ft:', a)
#zone_pts = find_zone_points(test, a)

# Test it out:
#edition = 'ASCE 7-02'
#h_bldg = 9
#length = 27
#ratio = h_bldg/length
#exposure = 'B'
#wind_speed = 120
#direction = 'parallel'
#ref_pitch = 9
#ref_cat =2
#hpr = True
#h_ocean = True
#encl_class = 'Enclosed'
# Difference in wind speed:
#psim = get_roof_uplift_pressure(edition, h_bldg, length, exposure, wind_speed, direction, ref_pitch)
#pressures = PressureCalc()
#rmps = pressures.rmwfrs_pressure(wind_speed, exposure, edition, h_bldg, length, ratio, ref_pitch, ref_cat, hpr, h_ocean, encl_class)
#print('real pressure:', rmps, 'change in wind speed:', psim)
# Difference in height:
#h_bldg = 27
#length = 27
#ratio = h_bldg/length
#hpsim = get_roof_uplift_pressure(edition, h_bldg, length, exposure, wind_speed, direction, ref_pitch)
#hrmps = pressures.rmwfrs_pressure(wind_speed, exposure, edition, h_bldg, length, ratio, ref_pitch, ref_cat, hpr, h_ocean, encl_class)
#print('real pressure:', hrmps, 'change in height:', hpsim)
# Difference in exposure categories:
#exposure = 'C'
#epsim = get_roof_uplift_pressure(edition, h_bldg, length, exposure, wind_speed, direction, ref_pitch)
#ermps = pressures.rmwfrs_pressure(wind_speed, exposure, edition, h_bldg, length, ratio, ref_pitch, ref_cat, hpr, h_ocean, encl_class)
#print('real pressure:', ermps, 'change in exposure:', epsim)

# Wall C&C:
#edition = 'ASCE 7-02'
#h_bldg = 9
#h_story = 9
#exposure = 'B'
#wind_speed = 120
#ref_pitch = 9
#ref_cat =2
#ctype = 'mullion'
#parcel_flag = True
#hpr = True
#h_ocean = True
#encl_class = 'Enclosed'
# Difference in wind speed:
#psim = get_wcc_pressure(edition, h_bldg, h_story, ctype, exposure, wind_speed, ref_pitch)
#pressures = PressureCalc()
#area_eff = pressures.get_warea(ctype, parcel_flag, h_story)
#wmps = pressures.wcc_pressure(wind_speed, exposure, edition, h_bldg, ref_pitch, area_eff, ref_cat, hpr, h_ocean, encl_class)
#print('real pressure:', wmps, 'change in wind speed:', psim)
# Difference in height:
#h_bldg = 27
#hpsim = get_wcc_pressure(edition, h_bldg, h_story, ctype, exposure, wind_speed, ref_pitch)
#hwmps = pressures.wcc_pressure(wind_speed, exposure, edition, h_bldg, ref_pitch, area_eff, ref_cat, hpr, h_ocean, encl_class)
#print('real pressure:', hwmps, 'change in wind speed:', hpsim)
# Difference in exposure categories:
#exposure = 'C'
#epsim = get_wcc_pressure(edition, h_bldg, h_story, ctype, exposure, wind_speed, ref_pitch)
#ewmps = pressures.wcc_pressure(wind_speed, exposure, edition, h_bldg, ref_pitch, area_eff, ref_cat, hpr, h_ocean, encl_class)
#print('real pressure:', ewmps, 'change in wind speed:', epsim)
