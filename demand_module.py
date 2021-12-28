import pandas as pd
import geopandas as gpd
from shapely import affinity
from shapely.geometry import Polygon, Point
from scipy import spatial
from geopy import distance
from math import sqrt, sin, atan2, degrees, pi
import numpy as np
from parcel import Parcel
from OBDM.zone import Site, Building
from bldg_code import ASCE7
from OBDM.element import Roof
from fault_tree import populate_code_capacities, generate_pressure_loading, find_peak_pressure_response
from get_debris import run_debris, get_site_debris, get_trajectory, get_source_bldgs
from survey_data import SurveyData
from queries import get_bldgs_at_dist


def assign_footprint(parcel, num_stories):
    # Access file with region's building footprint information:
    if parcel.hasLocation['State'] == 'FL' and parcel.hasLocation['County'] == 'Bay':
        jFile = 'C:/Users/Karen/PycharmProjects/DPBWE/Datasets/Geojson/BayCounty.geojson'
    else:
        print('Footprints for this region currently not supported')

    data = gpd.read_file(jFile)
    # data is a DataFrame object with column label = ['geometry'] and indexes = [0: end]
    # Accessing a specific Polygon object then requires: data['geometry'][index]

    # Need to access Polygon geometry in order to determine if the parcel's location is within that polygon:
    # Create a Point object with the parcel's lon, lat coordinates:
    ref_pt = parcel.hasLocation['Geodesic']

    # Loop through dataset to find the parcel's corresponding footprint:
    for row in range(0, len(data['geometry'])):
        # Check if point is within the polygon in this row:
        poly = data['geometry'][row]
        if ref_pt.within(poly):
            parcel.hasGeometry['Footprint']['geodesic'] = poly
            parcel.hasGeometry['Footprint']['type'] = 'open data'
        else:
            pass
    # If the lon, lat of the parcel does not fall within bounds of any of the footprints, assign nearest neighbor:
    if parcel.hasGeometry['Footprint']['type'] is None:
        # Populate the KD tree using the centroids of the building footprints:
        centroids = data['geometry'].apply(lambda ind: [ind.centroid.x, ind.centroid.y]).tolist()
        kdtree = spatial.KDTree(centroids)
        # Set up an array of (small) longitude, latitude radii:
        radii = np.arange(0.0001, 0.01, 0.0001)
        # Find the nearest neighbors within the radius (increase until neighbors are present):
        neigh_list = []
        for rad in radii:
            neigh_list.append(kdtree.query_ball_point([ref_pt.x, ref_pt.y], r=rad))
            if len(neigh_list) > 1:
                break
            else:
                pass
        # Find the identified building footprints:
        if len(neigh_list[1]) == 1:
            parcel.hasGeometry['Footprint']['geodesic'] = data['geometry'][neigh_list[1][0]]
            parcel.hasGeometry['Footprint']['type'] = 'open data'
        else:
            print('More than 1 building footprint identified', parcel.hasID, parcel.hasLocation['Address'])
            # In the future, might be able to do a match by considering the height of the parcel and it's area

    # Assign a regular footprint to any buildings without an open data footprint:
    if parcel.hasGeometry['Footprint']['type'] == 'open data':
        pass
    else:
        parcel.hasGeometry['Footprint']['type'] = 'default'
        length = (sqrt(parcel.hasGeometry['Total Floor Area'] / num_stories)) * (1 / (2 * sin(
            pi / 4)))  # Divide total building area by number of stories and take square root, divide by 2
        p1 = distance.distance(miles=length / 5280).destination((ref_pt.y, ref_pt.x), 45)
        p2 = distance.distance(miles=length / 5280).destination((ref_pt.y, ref_pt.x), 135)
        p3 = distance.distance(miles=length / 5280).destination((ref_pt.y, ref_pt.x), 225)
        p4 = distance.distance(miles=length / 5280).destination((ref_pt.y, ref_pt.x), 315)
        parcel.hasGeometry['Footprint']['geodesic'] = Polygon(
            [(p1.longitude, p1.latitude), (p2.longitude, p2.latitude), (p3.longitude, p3.latitude),
             (p4.longitude, p4.latitude)])
        print('default building footprint:' + parcel.hasLocation['Address'])
    # Given the geodesic footprint, calculate the local (x,y) coordinates for the building footprint:
    # Find the distance between exterior points and the building centroid (origin) to define a new coordinate system:
    xs, ys = parcel.hasGeometry['Footprint']['geodesic'].exterior.xy
    origin = parcel.hasGeometry['Footprint']['geodesic'].centroid
    point_list = []
    for ind in range(0, len(xs)):
        # Find the distance between x, y at origin and x, y for each point:
        xdist = distance.distance((origin.y, origin.x), (origin.y, xs[ind])).miles * 5280  # [ft]
        ydist = distance.distance((origin.y, origin.x), (ys[ind], origin.x)).miles * 5280  # [ft]
        if xs[ind] < origin.x:
            xdist = -1 * xdist
        else:
            pass
        if ys[ind] < origin.y:
            ydist = -1 * ydist
        else:
            pass
        point_list.append(Point(xdist, ydist))
    # Create a new polygon object:
    xy_poly = Polygon(point_list)
    if parcel.hasLocation['Address'] == '1002 23RD ST W PANAMA CITY 32405':
        xcoord, ycoord = xy_poly.exterior.xy
        new_point_list = []
        for idx in range(2, len(xcoord) - 2):
            new_point_list.append(Point(xcoord[idx], ycoord[idx]))
        xy_poly = Polygon(new_point_list)
    # Add to Parcel:
    parcel.hasGeometry['Footprint']['local'] = xy_poly
    # Rotate the footprint to create a "rotated cartesian" axis:
    rect = parcel.hasGeometry['Footprint']['local'].minimum_rotated_rectangle
    spts = list(rect.exterior.coords)
    theta = degrees(atan2((spts[1][0] - spts[2][0]), (spts[1][1] - spts[2][1])))
    parcel.hasOrientation = theta
    # Rotate the the building footprint to create the TPU axis:
    rotated_b = affinity.rotate(parcel.hasGeometry['Footprint']['local'], theta, origin='centroid')
    parcel.hasGeometry['Footprint']['rotated'] = rotated_b


def get_ref_bldg_crs(ref_bldg, bldg, length_unit):
    # Use the reference building's footprint centroid as origin:
    origin = ref_bldg.hasGeometry['Footprint']['geodesic'].centroid
    # Pull other building footprint - geographic coordinates:
    xb, yb = bldg.hasGeometry['Footprint']['geodesic'].exterior.xy
    new_pts = []
    for i in range(0, len(xb)):
        # Find the new (x,y) pairs for each longitude-latitude:
        if length_unit == 'ft':
            # Find the distance between x, y at origin and x, y for each point:
            xdist = distance.distance((origin.y, origin.x), (origin.y, xb[i])).miles * 5280  # [ft]
            ydist = distance.distance((origin.y, origin.x), (yb[i], origin.x)).miles * 5280  # [ft]
        else:
            pass
        if xb[i] < origin.x:
            xdist = -1 * xdist
        else:
            pass
        if yb[i] < origin.y:
            ydist = -1 * ydist
        else:
            pass
        new_pts.append(Point(xdist, ydist))
    bldg.hasGeometry['Footprint']['reference cartesian'] = Polygon(new_pts)

# Asset Description
# Parcel Models
lon = -85.676188
lat = 30.190142
test = Parcel('12345', 4, 'financial', 2000, '1002 23RD ST W PANAMA CITY 32405', 41134, lon, lat, length_unit='ft', plot_flag=False)
#test.hasElement['Roof'][0].hasShape['flat'] = True
#test.hasElement['Roof'][0].hasPitch = 0
#wind_speed_file_path = 'D:/Users/Karen/Documents/Github/DPBWE/Datasets/WindFields/2018-Michael_windgrid_ver36.csv'
exposure = 'B'
unit = 'english'
basic_wind_speed = 123.342  # 126?
wind_direction = 0
cc_flag, mwfrs_flag = True, True
# populate_code_capacities(test, cc_flag, mwfrs_flag, exposure)
# generate_pressure_loading(test, basic_wind_speed, wind_direction, tpu_flag=True, csv_flag=True)
# find_peak_pressure_response(test, zone_flag=True, time_flag=True)
#test.hasGeometry['Height'] = 9*4
#test.hasGeometry['Height'] = 52.5
# Read in parcel data from surrounding buildings:
df = pd.read_csv('C:/Users/Karen/Desktop/Parcel_data.csv')
# Create data models for each building:
site = Site()
plot_flag=False
length_unit='ft'
for p in df.index:
    new_bldg = Building()
    new_bldg.add_parcel_data(df['Parcel Id'][p], df['Stories'][p], df['Use Code'][p], df['Year Built'][p],
                             df['Address'][p], df['Square Footage'][p], df['Longitude'][p], df['Latitude'][p],
                             'ft', loc_flag=True)
    # Add roof element and data:
    new_roof = Roof()
    new_roof.hasCover = df['Roof Cover'][p]
    new_roof.hasType = df['Roof Cover'][p]
    new_bldg.hasStory[-1].adjacentElement['Roof'] = [new_roof]
    new_bldg.hasStory[-1].update_elements()
    new_bldg.update_zones()
    new_bldg.update_elements()
    # Add height information:
    survey_data = SurveyData()
    survey_data.doe_ref_bldg(new_bldg, window_flag=False)
    # Get building footprint:
    assign_footprint(new_bldg, df['Stories'][p])
    get_ref_bldg_crs(test, new_bldg, length_unit)
    site.hasBuilding.append(new_bldg)
site.update_zones()
site.update_interfaces()
site.update_elements()
# Plot the the site that is 150 meters from the building:
#dist = .150
#unit = 'km'
#plot_flag = True
#get_bldgs_at_dist(site, test, dist, unit, plot_flag)
# Find building-specific debris vulnerability:
wind_direction = 360-45
wind_speed_arr = np.arange(70, 200, 5)  # Need to figure out what wind speed this is
# Grab all the debris types in this site:
get_site_debris(site, length_unit)
# Step 3: Calculate the trajectory of each debris type:
# traj_dict = {'wind speed': [], 'debris name': [], 'alongwind_mean': [], 'alongwind_std_dev': [],
#              'acrosswind_mean': [], 'acrosswind_std_dev': []}
# for speed in wind_speed_arr:
#     for key in site.hasDebris:
#         for row in range(0, len(site.hasDebris[key])):
#             model_input = site.hasDebris[key].iloc[row]
#             alongwind_dist, acrosswind_dist = get_trajectory(model_input, speed, length_unit, mcs_flag=True)
#             traj_dict['alongwind_mean'].append(np.mean(alongwind_dist))
#             traj_dict['acrosswind_mean'].append(np.mean(acrosswind_dist))
#             traj_dict['alongwind_std_dev'].append(np.std(alongwind_dist))
#             traj_dict['acrosswind_std_dev'].append(np.std(alongwind_dist))
#             traj_dict['wind speed'].append(speed)
#             traj_dict['debris name'].append(site.hasDebris[key]['debris name'][row])
# df_debris = pd.DataFrame(traj_dict)
# df_debris.to_csv('C:/Users/Karen/Desktop/DebrisTypicalDistances.csv', index=False)
#run_debris(test, site, length_unit, wind_direction, wind_speed_arr)
# Find potential source buildings:
crs = 'reference cartesian'
site_source = get_source_bldgs(test, site, wind_direction, basic_wind_speed, crs, length_unit)
