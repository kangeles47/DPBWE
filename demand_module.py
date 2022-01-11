import pandas as pd
import geopandas as gpd
from shapely import affinity
from shapely.geometry import Polygon, Point, LineString
from scipy import spatial
from scipy.stats import uniform
import matplotlib.pyplot as plt
from matplotlib import rcParams
from geopy import distance
from math import sqrt, sin, atan2, degrees, pi
import numpy as np
from parcel import Parcel
from bldg_code import ASCE7
from OBDM.zone import Site, Building
from OBDM.element import Roof, Floor, Wall, Ceiling
from code_pressures import PressureCalc
from OBDM.interface import Interface
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


def augmented_elements_wall(bldg, num_wall_elems, story_wall_elev, plot_flag):
    rcParams['font.family'] = "Times New Roman"
    rcParams.update({'font.size': 18})
    x, y = bldg.hasGeometry['Footprint']['local'].exterior.xy
    lines = []
    for i in range(0, len(x) - 1):
        new_line = LineString([(x[i], y[i]), (x[i + 1], y[i + 1])])
        lines.append(new_line)
        plt.plot(np.array([x[i], x[i + 1]])/3.281, np.array([y[i], y[i + 1]])/3.281, 'k')
    new_pt_list = []
    for j in range(0, len(lines)):
        length = lines[j].length/num_wall_elems[j]
        for k in range(1, num_wall_elems[j]+1):
            # Interpolate new point:
            idist = length*k
            new_pt = lines[j].interpolate(idist)
            new_pt_list.append(new_pt)
            plt.scatter(new_pt.x/3.281, new_pt.y/3.281, color='b')
    plt.xlabel('x [m]')
    plt.ylabel('y [m]')
    plt.show()
    bldg.hasGeometry['Footprint']['augmented local'] = Polygon(new_pt_list)
    # Create building elements:
    if plot_flag:
        fig = plt.figure()
        ax = plt.axes(projection='3d')
    else:
        pass
    for story in range(0, len(bldg.hasStory)):
        # Create an empty list to hold all elements:
        element_dict = {'Floor': [], 'Walls': [], 'Ceiling': [], 'Roof': []}
        # Generate floor and ceiling instance(s):
        if story == 0:
            new_floor1 = Floor()
            new_floor1.hasElevation = bldg.hasStory[story].hasElevation[0]
            new_floor1.hasGeometry['2D Geometry'] = bldg.hasGeometry['Footprint']['local']
            new_floor1.hasGeometry['Area'] = new_floor1.hasGeometry['2D Geometry'].area
            element_dict['Floor'].append(new_floor1)
        else:
            # Reference the prior story's top floor:
            floor1 = bldg.hasStory[story - 1].hasElement['Floor'][1]
            floor1.hasGeometry['2D Geometry'] = bldg.hasGeometry['Footprint']['local']
            new_floor1.hasGeometry['Area'] = new_floor1.hasGeometry['2D Geometry'].area
            element_dict['Floor'].append(floor1)
        # Top floor:
        if story == len(bldg.hasStory) - 1:
            new_roof = Roof()
            # Add two-dimensional geometry:
            for key in ['local', 'geodesic']:
                new_roof.hasGeometry['2D Geometry'][key] = bldg.hasGeometry['Footprint'][key]
                # Add three-dimensional geometry:
                xroof, yroof = new_roof.hasGeometry['2D Geometry'][key].exterior.xy
                rpt_list = []
                for x in range(0, len(xroof)):
                    new_pt = Point(xroof[x], yroof[x], bldg.hasGeometry['Height'])
                    rpt_list.append(new_pt)
                new_roof.hasGeometry['3D Geometry'][key] = Polygon(rpt_list)
            # Add roof to the story:
            new_roof.hasGeometry['Area'] = new_roof.hasGeometry['2D Geometry']['local'].area
            bldg.hasStory[story].adjacentElement.update({'Roof': [new_roof]})
            element_dict['Roof'].append(new_roof)
        else:
            new_floor2 = Floor()
            new_floor2.hasElevation = bldg.hasStory[story].hasElevation[1]
            new_floor2.hasGeometry['2D Geometry'] = bldg.hasGeometry['Footprint']['local']
            new_floor2.hasGeometry['Area'] = new_floor2.hasGeometry['2D Geometry'].area
            # new_floor_list.append(new_floor2)
            element_dict['Floor'].append(new_floor2)
        # Create a new ceiling for the floor:
        new_ceiling = Ceiling()
        # Add the ceiling to element_dict:
        element_dict['Ceiling'].append(new_ceiling)
        # Create wall elements for the story:
        new_wall_list = []
        wall_lengths = []
        xf, yf = bldg.hasGeometry['Footprint']['augmented local'].exterior.xy
        for e in range(0, len(story_wall_elev[story])-1):
            for pt in range(0, len(xf) - 1):
                # Create a new Wall Instance:
                ext_wall = Wall()
                ext_wall.isExterior = True
                ext_wall.inLoadPath = True
                ext_wall.hasGeometry['Height'] = story_wall_elev[story][e+1] - story_wall_elev[story][e]
                ext_wall.hasGeometry['1D Geometry']['local'] = LineString([(xf[pt], yf[pt]), (xf[pt + 1], yf[
                    pt + 1])])  # Line segment with start/end coordinates of wall (respetive to building origin)
                ext_wall.hasGeometry['Length'] = ext_wall.hasGeometry['1D Geometry']['local'].length
                ext_wall.hasGeometry['Area'] = ext_wall.hasGeometry['Height'] * ext_wall.hasGeometry['Length']
                # Add local 3D geometry:
                zbottom = story_wall_elev[story][e]
                ztop = story_wall_elev[story][e+1]
                xline, yline = ext_wall.hasGeometry['1D Geometry']['local'].xy
                wall_xyz_poly = Polygon([Point(xline[0], yline[0], zbottom), Point(xline[1], yline[1], zbottom),
                                         Point(xline[1], yline[1], ztop), Point(xline[0], yline[0], ztop),
                                         Point(xline[0], yline[0], zbottom)])
                ext_wall.hasGeometry['3D Geometry']['local'] = wall_xyz_poly
                # Add rotated geometry:
                new_rline = affinity.rotate(ext_wall.hasGeometry['1D Geometry']['local'], bldg.hasOrientation,
                                            origin=bldg.hasGeometry['Footprint']['local'].centroid)
                ext_wall.hasGeometry['1D Geometry']['rotated'] = new_rline
                bldg.get_wall_dir(ext_wall, 'rotated')
                new_wall_list.append(ext_wall)
                wall_lengths.append(ext_wall.hasGeometry['Length'])
                if plot_flag:
                    xw, yw, zw = [], [], []
                    wall_coords = list(ext_wall.hasGeometry['3D Geometry']['local'].exterior.coords)
                    for c in wall_coords:
                        xw.append(c[0])
                        yw.append(c[1])
                        zw.append(c[2])
                    plt.plot(np.array(xw)/3.281, np.array(yw)/3.281, np.array(zw)/3.281, 'k')
        # Add all walls to element_dict:
        element_dict['Walls'] = new_wall_list
        # Each wall shares interfaces with the walls before and after it:
        # for w in range(0, len(new_wall_list) - 1):
        #     # Create new Interface instance
        #     new_interface = Interface([new_wall_list[w], new_wall_list[w + 1]])
        #     bldg.hasStory[story].hasInterface.append(new_interface)
        # Add all elements to the story's "hasElement" attribute:
        bldg.hasStory[story].containsElement.update({'Ceiling': element_dict['Ceiling']})
        bldg.hasStory[story].adjacentElement.update({'Floor': element_dict['Floor']})
        bldg.hasStory[story].adjacentElement.update({'Walls': element_dict['Walls']})
        # Update hasElement attribute for the story:
        bldg.hasStory[story].hasElement.update(element_dict)
    if plot_flag:
        # Make the panes transparent:
        ax.w_xaxis.set_pane_color((1.0, 1.0, 1.0, 1.0))
        ax.w_yaxis.set_pane_color((1.0, 1.0, 1.0, 1.0))
        ax.w_zaxis.set_pane_color((1.0, 1.0, 1.0, 1.0))
        # Make the grids transparent:
        ax.xaxis._axinfo["grid"]['color'] = (1, 1, 1, 0)
        ax.yaxis._axinfo["grid"]['color'] = (1, 1, 1, 0)
        ax.zaxis._axinfo["grid"]['color'] = (1, 1, 1, 0)
        # Plot labels
        ax.set_xlabel('x [m]', fontsize=16, labelpad=10)
        ax.set_ylabel('y [m]', fontsize=16, labelpad=10)
        ax.set_zlabel('z [m]', fontsize=16, labelpad=10)
        ax.set_zlim3d(0, 16)
        ax.set_xticks(np.arange(-20, 25, 5))
        ax.set_yticks(np.arange(-20, 25, 5))
        ax.set_zticks(np.arange(0, 20, 4))
        ax.xaxis.set_tick_params(labelsize=16)
        ax.yaxis.set_tick_params(labelsize=16)
        ax.zaxis.set_tick_params(labelsize=16)
        plt.show()

# Asset Description
# Parcel Models
lon = -85.676188
lat = 30.190142
test = Parcel('12345', 4, 'financial', 1989, '1002 23RD ST W PANAMA CITY 32405', 41134, lon, lat, length_unit='ft', plot_flag=False)
num_wall_elems = [4, 9, 17, 9, 4, 9, 17, 9]
wall_height = test.hasGeometry['Height']/8
story_wall_elev = []
for story in test.hasStory:
    story_wall_elev.append([story.hasElevation[0], story.hasElevation[0]+wall_height, story.hasElevation[1]])
# Create augmented elements:
augmented_elements_wall(test, num_wall_elems, story_wall_elev, plot_flag=False)
# Update the Building's Elements:
test.update_elements()
# Add roof information:
test.hasElement['Roof'][0].hasShape['flat'] = True
test.hasElement['Roof'][0].hasPitch = 0
test.hasElement['Roof'][0].hasCover = 'BUILT-UP'
test.hasElement['Roof'][0].hasType = 'BUILT-UP'
# Populate code-informed capacities
#code_informed = bldg_code.FBC(test, loading_flag=False)
#code_informed.bldg_attributes(test)
#code_informed.roof_attributes(code_informed.hasEdition, test)
# Update roof cover sub-elements (if-applicable):
if len(test.adjacentElement['Roof'][0].hasSubElement['cover']) > 0:
    for elem in test.adjacentElement['Roof'][0].hasSubElement['cover']:
        elem.hasCover = test.adjacentElement['Roof'][0].hasCover
        elem.hasPitch = test.adjacentElement['Roof'][0].hasPitch
else:
    pass
# Code-informed capacities:
# 1) Find zone locations:
asce7 = ASCE7(test, loading_flag=True)
a = asce7.get_cc_zone_width(test)
roof_flag = True
zone_pts, roof_polys = asce7.find_cc_zone_points(test, a, roof_flag, asce7.hasEdition)
# Create sub-elements for roof structure:
for poly in roof_polys:
    new_subelement = Roof()
    new_subelement.hasGeometry['2D Geometry']['local'] = poly
    new_subelement.hasCover = test.adjacentElement['Roof'][0].hasCover
    new_subelement.hasType = test.adjacentElement['Roof'][0].hasType
    new_subelement.hasPitch = test.adjacentElement['Roof'][0].hasPitch
# 2) Calculate zone pressures:
# pressure_calc = PressureCalc()
# design_wind_speed = 100
# exposure = 'B'
# edition = asce7.hasEdition
# h_bldg = test.hasGeometry['Height']
# pitch = test.hasElement['Roof'][0].hasPitch
# area_eff = wall_height*wall_height/3
# cat = 2
# hpr = True
# h_ocean = True
# encl_class = 'Enclosed'
# tpu_flag = True
# wcc = pressure_calc.wcc_pressure(design_wind_speed, exposure, edition, h_bldg, pitch, area_eff, cat, hpr, h_ocean, encl_class, tpu_flag)
# # 3) Map pressures to elements:
# for wall in test.hasElement['Walls']:
#     wall.hasType = 'GLASS THRM; COMMON BRK'
#     for row in range(0, len(zone_pts.index)):
#         zone_line = LineString([zone_pts['LinePoint1'][row], zone_pts['LinePoint2'][row]])
#         if wall.hasGeometry['1D Geometry']['local'].within(zone_line) or wall.hasGeometry['1D Geometry']['local'].intersects(zone_line):
#             zone4_1 = LineString([zone_pts['LinePoint1'][row], zone_pts['NewZoneStart'][row]])
#             zone4_2 = LineString([zone_pts['NewZoneEnd'][row], zone_pts['LinePoint2'][row]])
#             zone5 = LineString([zone_pts['NewZoneStart'][row], zone_pts['NewZoneEnd'][row]])
#             if wall.hasGeometry['1D Geometry']['local'].within(zone4_1) or wall.hasGeometry['1D Geometry']['local'].within(zone4_2):
#                 wall.hasCapacity['wind pressure']['external']['positive'] = wcc[0]
#                 wall.hasCapacity['wind pressure']['external']['negative'] = wcc[2]
#             elif wall.hasGeometry['1D Geometry']['local'].within(zone5):
#                 wall.hasCapacity['wind pressure']['external']['positive'] = wcc[1]
#                 wall.hasCapacity['wind pressure']['external']['negative'] = wcc[3]
#             else:
#                 # Wall is in both zones: choose worse case:
#                 wall.hasCapacity['wind pressure']['external']['positive'] = max(wcc)
#                 wall.hasCapacity['wind pressure']['external']['negative'] = min(wcc)
#         else:
#             pass
# # Populate the building's Hurricane Michael loading demand:
# unit = 'english'
michael_wind_speed = 123.342  # 126? data model paper: 123.342
# # #wind_speed_file_path = 'D:/Users/Karen/Documents/Github/DPBWE/Datasets/WindFields/2018-Michael_windgrid_ver36.csv'
# # tpu_wind_direction = 0
# # #cc_flag, mwfrs_flag = True, True
# # generate_pressure_loading(test, michael_wind_speed, tpu_wind_direction, tpu_flag=True, csv_flag=True)
# # find_peak_pressure_response(test, zone_flag=True, time_flag=True)
# # Read in parcel data from surrounding buildings:
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
#wind_direction = 360-45
#wind_speed_arr = np.arange(70, 200, 5)  # Need to figure out what wind speed this is
# Grab all the debris types in this site:
length_unit = 'ft'
get_site_debris(site, length_unit)
# Step 3: Calculate the trajectory of each debris type:
# traj_dict = {'wind speed': [], 'debris name': [], 'alongwind_mean': [], 'alongwind_std_dev': [],
#              'acrosswind_mean': [], 'acrosswind_std_dev': []}
# for speed in wind_speed_arr:
#     for key in site.hasDebris:
#         for row in range(0, len(site.hasDebris[key])):
#             model_input = site.hasDebris[key].iloc[row]
#             if 'POLY TPO' in site.hasDebris[key]['debris name'][row]:
#                 model_input['flight time'] = uniform(0, 1)
#             else:
#                 pass
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
wind_direction = 45
site_source = get_source_bldgs(test, site, wind_direction, michael_wind_speed, crs, length_unit)
for b in site_source.hasBuilding:
    print(b.hasLocation['Address'])
    print(b.hasID)
