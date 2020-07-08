import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from geopy import distance
from shapely.geometry import Polygon
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
    a = max(min(0.1*hdist, 0.4*bldg.h_bldg), 0.4*hdist, 3)
    return a

def assign_zone_pressures(bldg, zone_width, exposure, wind_speed):
    # Use the building footprint to find the lon, lat points for zone boundaries around perimeter:
    xs, ys = bldg.footprint["geometry"].exterior.xy
    # Find the distance between exterior points and the building centroid (origin) to define a new coordinate system:
    origin = bldg.footprint['geometry'].centroid
    xc = []
    yc = []
    for ind in range(0, len(xs)-1):
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
    zones = pd.DataFrame()
    for j in range(0, len(xc)-1):
        # Step 1: Find the angle between two consecutive points:
        # Use the first point as the reference point and find angle between two points:
        ya = yc[j+1] - yc[j]
        xa = xc[j+1] - xc[j]
        angle = math.degrees(math.atan2(ya, xa))  # angle (in degrees)
        print(angle)
        # Step 2: Find the points marking the various zones:
        # Step 2a: Use cases - same latitude/longitude:
        if angle == 0:
            x1 = xc[j] + zone_width
            x2 = xc[j+1] - zone_width
            y1 = yc[j]
            y2 = yc[j+1]
        elif angle == -180 or angle == 180:
            x1 = xc[j] - zone_width
            x2 = xc[j + 1] + zone_width
            y1 = yc[j]
            y2 = yc[j + 1]
        elif angle == 90:
            x1 = xc[j]
            x2 = xc[j + 1]
            y1 = yc[j] + zone_width
            y2 = yc[j + 1] - zone_width
        elif angle == -90 or angle == 270:
            x1 = xc[j]
            x2 = xc[j + 1]
            y1 = yc[j] - zone_width
            y2 = yc[j + 1] + zone_width
        else:  # Step 2b: All other angles - Use similar triangles
            angle2 = 180 - abs(angle)-90
            if angle > 0:
                if xc[j] < xc[j+1]:
                    x1 = xc[j] + zone_width*math.cos(math.radians(angle))
                    x2 = xc[j + 1] - zone_width*math.sin(math.radians(angle2))
                    y1 = yc[j] + zone_width*math.sin(math.radians(angle))
                    y2 = yc[j + 1] - zone_width*math.cos(math.radians(angle2))
                else:
                    x1 = xc[j] + zone_width * math.cos(math.radians(angle))
                    x2 = xc[j + 1] - zone_width * math.sin(math.radians(angle2))
                    y1 = yc[j] + zone_width * math.sin(math.radians(angle))
                    y2 = yc[j + 1] - zone_width * math.cos(math.radians(angle2))
            elif angle < 0:
                if xc[j] < xc[j+1]:
                    x1 = xc[j] + zone_width*math.cos(math.radians(angle))
                    x2 = xc[j + 1] - zone_width*math.sin(math.radians(angle2))
                    y1 = yc[j] + zone_width*math.sin(math.radians(angle))
                    y2 = yc[j + 1] + zone_width*math.cos(math.radians(angle2))
                else:
                    x1 = xc[j] + zone_width * math.cos(math.radians(angle))
                    x2 = xc[j + 1] - zone_width * math.sin(math.radians(angle2))
                    y1 = yc[j] + zone_width * math.sin(math.radians(angle))
                    y2 = yc[j + 1] + zone_width * math.cos(math.radians(angle2))
        # Organize the points:
        xlist = [xc[j], x1, x2, xc[j+1]]
        ylist = [yc[j], y1, y2, yc[j+1]]
        # Plot to verify:
        plt.plot(xc[j:j + 2], yc[j:j + 2])
        for ind in range(0,len(xlist)):
            plt.scatter(xlist[ind], ylist[ind])
    plt.show()
    # Assign C&C pressures given the component type and its location (zone):
    # Get a list of all wall types:
    ctype_lst = []
    for wall in bldg.walls:
        ctype_lst.append(wall.type)
    ctype_lst = set(ctype_lst)
    # Determine the Wall C&C pressures:
    wcc_plist = []
    for ctype in ctype_lst:
        wcc_pressure = get_wcc_pressure(edition, bldg.h_bldg, bldg.h_story, ctype, exposure, wind_speed, bldg.roof.pitch)
        wcc_plist.append(wcc_pressure)
    # For each floor, figure out which surfaces have the given ctype:
    #for story in range(0, bldg.num_stories):
        # Figure out which walls are contained within the specified story:
       # pass
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


lon = -85.676188
lat = 30.190142
test = Parcel('12345', 4, 'Financial', 1989, '1002 23RD ST W PANAMA CITY 32405', 41134, lon, lat)
#lon = -85.666162
#lat = 30.19953
#test = Parcel('12989-113-000', 1, 'SINGLE FAM', 1974, '2820  STATE AVE   PANAMA CITY 32405', 3141, lon, lat)
a = 3
assign_zone_pressures(test, a, 'B', 100)

# Test it out:
edition = 'ASCE 7-02'
h_bldg = 9
length = 27
ratio = h_bldg/length
exposure = 'B'
wind_speed = 120
direction = 'parallel'
ref_pitch = 9
ref_cat =2
hpr = True
h_ocean = True
encl_class = 'Enclosed'
# Difference in wind speed:
psim = get_roof_uplift_pressure(edition, h_bldg, length, exposure, wind_speed, direction, ref_pitch)
pressures = PressureCalc()
rmps = pressures.rmwfrs_pressure(wind_speed, exposure, edition, h_bldg, length, ratio, ref_pitch, ref_cat, hpr, h_ocean, encl_class)
print('real pressure:', rmps, 'change in wind speed:', psim)
# Difference in height:
h_bldg = 27
length = 27
ratio = h_bldg/length
hpsim = get_roof_uplift_pressure(edition, h_bldg, length, exposure, wind_speed, direction, ref_pitch)
hrmps = pressures.rmwfrs_pressure(wind_speed, exposure, edition, h_bldg, length, ratio, ref_pitch, ref_cat, hpr, h_ocean, encl_class)
print('real pressure:', hrmps, 'change in height:', hpsim)
# Difference in exposure categories:
exposure = 'C'
epsim = get_roof_uplift_pressure(edition, h_bldg, length, exposure, wind_speed, direction, ref_pitch)
ermps = pressures.rmwfrs_pressure(wind_speed, exposure, edition, h_bldg, length, ratio, ref_pitch, ref_cat, hpr, h_ocean, encl_class)
print('real pressure:', ermps, 'change in exposure:', epsim)

# Wall C&C:
edition = 'ASCE 7-02'
h_bldg = 9
h_story = 9
exposure = 'B'
wind_speed = 120
ref_pitch = 9
ref_cat =2
ctype = 'mullion'
parcel_flag = True
hpr = True
h_ocean = True
encl_class = 'Enclosed'
# Difference in wind speed:
psim = get_wcc_pressure(edition, h_bldg, h_story, ctype, exposure, wind_speed, ref_pitch)
pressures = PressureCalc()
area_eff = pressures.get_warea(ctype, parcel_flag, h_story)
wmps = pressures.wcc_pressure(wind_speed, exposure, edition, h_bldg, ref_pitch, area_eff, ref_cat, hpr, h_ocean, encl_class)
print('real pressure:', wmps, 'change in wind speed:', psim)
# Difference in height:
h_bldg = 27
hpsim = get_wcc_pressure(edition, h_bldg, h_story, ctype, exposure, wind_speed, ref_pitch)
hwmps = pressures.wcc_pressure(wind_speed, exposure, edition, h_bldg, ref_pitch, area_eff, ref_cat, hpr, h_ocean, encl_class)
print('real pressure:', hwmps, 'change in wind speed:', hpsim)
# Difference in exposure categories:
exposure = 'C'
epsim = get_wcc_pressure(edition, h_bldg, h_story, ctype, exposure, wind_speed, ref_pitch)
ewmps = pressures.wcc_pressure(wind_speed, exposure, edition, h_bldg, ref_pitch, area_eff, ref_cat, hpr, h_ocean, encl_class)
print('real pressure:', ewmps, 'change in wind speed:', epsim)
