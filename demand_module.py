import pandas as pd
import geopandas as gpd
from shapely import affinity
from shapely.ops import split
from shapely.geometry import Polygon, Point, LineString
from scipy import spatial
from scipy.stats import uniform
import matplotlib.pyplot as plt
from matplotlib import rcParams
from geopy import distance
from math import sqrt, sin, atan2, degrees, pi
import numpy as np
from parcel import Parcel
from bldg_code import ASCE7, FBC
from OBDM.zone import Site, Building
from OBDM.element import Roof, Floor, Wall, Ceiling
from code_pressures import PressureCalc
from get_debris import run_debris, get_site_debris, get_trajectory, get_source_bldgs
from survey_data import SurveyData
from queries import get_bldgs_at_dist
from bdm_tpu_pressures import map_tpu_ptaps, convert_to_tpu_wdir, map_ptaps_to_components
from fault_tree import wind_pressure_ftree, wbd_ftree
from get_debris import get_num_dobjects, get_traj_line


def assign_footprint(parcel, num_stories):
    # Access file with region's building footprint information:
    if parcel.hasLocation['State'] == 'FL' and parcel.hasLocation['County'] == 'Bay':
        jFile = 'D:/Users/Karen/Documents/Github/DPBWE/Datasets/Geojson/BayCounty.geojson'
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
    theta = degrees(atan2((spts[2][1] - spts[1][1]), (spts[2][0] - spts[1][0])))  # input (y, x)
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
    else:
        pass
    # Update elements:
    bldg.update_elements()


def get_cc_min_capacity(bldg, exposure, high_value_flag, roof_flag, wall_flag, source_gable_flag):
    # 1) find C&C zones:
    asce7 = ASCE7(bldg, loading_flag=True)
    if high_value_flag:
        a = asce7.get_cc_zone_width(bldg)
        zone_pts, roof_polys = asce7.find_cc_zone_points(bldg, a, roof_flag, asce7.hasEdition)
    else:
        original_footprint = Polygon(list(bldg.hasGeometry['Footprint']['local'].exterior.coords))
        bldg.hasGeometry['Footprint']['local'] = bldg.hasGeometry['Footprint']['local'].minimum_rotated_rectangle
        a = asce7.get_cc_zone_width(bldg)
        if source_gable_flag:
            zone_pts, roof_polys = asce7.find_cc_zone_points(bldg, a, roof_flag, asce7.hasEdition)
            # # Create temporary bldg objects and grab their roof polys:
            # xrect, yrect = bldg.hasGeometry['Footprint']['local'].exterior.xy
            # clist = []
            # for i in range(0, len(xrect)-1):
            #     new_centroid = LineString([(xrect[i], yrect[i]), (xrect[i+1], yrect[i+1])]).centroid
            #     clist.append(new_centroid)
            # split_line = LineString([clist[1], clist[3]])
            # split_poly = split(bldg.hasGeometry['Footprint']['local'], split_line)
            # zone_pts = []
            # roof_polys = []
            # for poly in split_poly:
            #     new_bldg = Building()
            #     new_bldg.hasGeometry['Footprint']['local'] = poly
            #     zpts, rpolys = asce7.find_cc_zone_points(new_bldg, a, roof_flag, asce7.hasEdition)
            #     zone_pts.append(zpts)
            #     roof_polys.append(rpolys)
            # # Combine dictionaries in zone_pts and roof_polys:
        else:
            zone_pts, roof_polys = asce7.find_cc_zone_points(bldg, a, roof_flag, asce7.hasEdition)
        # Update building with original footprint:
        bldg.hasGeometry['Footprint']['local'] = original_footprint
    # 2) Calculate zone pressures:
    design_wind_speed = asce7.get_code_wind_speed(bldg)
    pressure_calc = PressureCalc()
    edition = asce7.hasEdition
    h_bldg = bldg.hasGeometry['Height']
    pitch = bldg.hasElement['Roof'][0].hasPitch
    cat = 2
    hpr = True
    h_ocean = True
    encl_class = 'Enclosed'
    tpu_flag = True
    if wall_flag:
        wall_height = bldg.hasStory[0].hasElevation[1] - bldg.hasStory[0].hasElevation[0]
        span_area_eff = wall_height * wall_height / 3
        spacing_area_eff = wall_height*5
        if spacing_area_eff > span_area_eff:
            area_eff = spacing_area_eff
        else:
            area_eff = span_area_eff
        wcc = pressure_calc.wcc_pressure(design_wind_speed, exposure, edition, h_bldg, pitch, area_eff, cat, hpr, h_ocean,
                                     encl_class, tpu_flag)
    else:
        wcc = None
    if roof_flag:
        area_eff = 10
        rcc = pressure_calc.rcc_pressure(design_wind_speed, exposure, edition, h_bldg, pitch, area_eff, cat, hpr, h_ocean,
                                     encl_class, tpu_flag)
        # Go ahead and map to roof C&C pressures to new set of roof subelements:
        if len(bldg.hasElement['Roof'][0].hasSubElement['cover']) == 0:
            # Create sub-elements for roof structure:
            for key in roof_polys:
                for poly in roof_polys[key]:
                    new_subelement = Roof()
                    new_subelement.hasGeometry['2D Geometry']['local'] = poly
                    new_subelement.hasCover = bldg.adjacentElement['Roof'][0].hasCover
                    new_subelement.hasType = bldg.adjacentElement['Roof'][0].hasType
                    new_subelement.hasPitch = bldg.adjacentElement['Roof'][0].hasPitch
                    if asce7.hasEdition == 'ASCE 7-88' or asce7.hasEdition == 93:
                        if key == 'Zone 1':
                            new_subelement.hasCapacity['wind pressure']['external']['negative'] = rcc[0]
                        elif key == 'Zone 2':
                            new_subelement.hasCapacity['wind pressure']['external']['negative'] = rcc[1]
                        elif key == 'Zone 3':
                            new_subelement.hasCapacity['wind pressure']['external']['negative'] = rcc[2]
                        # Add minimum positive wind pressure for C&C:
                        new_subelement.hasCapacity['wind pressure']['external']['positive'] = 10
                    else:
                        if key == 'Zone 1':
                            new_subelement.hasCapacity['wind pressure']['external']['positive'] = rcc[0]
                            new_subelement.hasCapacity['wind pressure']['external']['negative'] = rcc[3]
                        elif key == 'Zone 2':
                            new_subelement.hasCapacity['wind pressure']['external']['positive'] = rcc[1]
                            new_subelement.hasCapacity['wind pressure']['external']['negative'] = rcc[4]
                        elif key == 'Zone 3':
                            new_subelement.hasCapacity['wind pressure']['external']['positive'] = rcc[2]
                            new_subelement.hasCapacity['wind pressure']['external']['negative'] = rcc[5]
                    bldg.adjacentElement['Roof'][0].hasSubElement['cover'].append(new_subelement)
        else:
            pass
    else:
        rcc = None
        
    return zone_pts, roof_polys, rcc, wcc

# 1a) Asset Description: target_bldg Building Parcel Model
# Parcel Models
lon = -85.676188
lat = 30.190142
target_bldg = Parcel('12345', 4, 'financial', 1996, '1002 23RD ST W PANAMA CITY 32405', 41134, lon, lat, length_unit='ft', plot_flag=False)  # 1989
num_wall_elems = [4, 9, 17, 9, 4, 9, 17, 9]
wall_height = target_bldg.hasGeometry['Height']/8
story_wall_elev = []
for story in target_bldg.hasStory:
    story_wall_elev.append([story.hasElevation[0], story.hasElevation[0]+wall_height, story.hasElevation[1]])
# Create augmented elements:
augmented_elements_wall(target_bldg, num_wall_elems, story_wall_elev, plot_flag=False)
for wall in target_bldg.hasElement['Walls']:
    wall.hasType = 'GLASS THRM; COMMON BRK'
# Add roof information:
target_bldg.hasElement['Roof'][0].hasShape['flat'] = True
target_bldg.hasElement['Roof'][0].hasPitch = 0
target_bldg.hasElement['Roof'][0].hasCover = 'BUILT-UP'
target_bldg.hasElement['Roof'][0].hasType = 'BUILT-UP'

# 1b) Asset Description: Minimum code-informed capacities:
# Find zone locations and calculate zone pressures:
exposure = 'B'
roof_flag = True
wall_flag = True
high_value_flag=True
zone_pts, roof_polys, rcc, wcc = get_cc_min_capacity(target_bldg, exposure, high_value_flag, roof_flag, wall_flag, source_gable_flag=True)  # includes roof mapping
# Map capacities to wall elements:
# Figure to show zones and component mapping:
fig = plt.figure()
ax = plt.axes(projection='3d')
# Wall C&C first:
for wall in target_bldg.hasElement['Walls']:
    for row in range(0, len(zone_pts.index)):
        xl, yl = LineString([zone_pts['LinePoint1'][row], zone_pts['LinePoint2'][row]]).xy
        zone_box = Polygon([(max(xl), max(yl)), (min(xl), max(yl)), (min(xl), min(yl)), (max(xl), min(yl))])
        if wall.hasGeometry['1D Geometry']['local'].within(zone_box) or wall.hasGeometry['1D Geometry']['local'].intersects(zone_box):
            x5, y5 = LineString([zone_pts['NewZoneStart'][row], zone_pts['NewZoneEnd'][row]]).xy
            zone5_box = Polygon([(max(x5), max(y5)), (min(x5), max(y5)), (min(x5), min(y5)), (max(x5), min(y5))])
            # Aside: pull wall 3d geometry for plotting:
            xw, yw, zw = [], [], []
            wall_coords = list(wall.hasGeometry['3D Geometry']['local'].exterior.coords)
            for c in wall_coords:
                xw.append(c[0])
                yw.append(c[1])
                zw.append(c[2])
            # Figure out is this wall is in Zone 4 or 5 or both and designate capacity:
            if wall.hasGeometry['1D Geometry']['local'].within(zone5_box) or wall.hasGeometry['1D Geometry']['local'].intersects(zone5_box):
                wall.hasCapacity['wind pressure']['external']['positive'] = wcc[1]
                wall.hasCapacity['wind pressure']['external']['negative'] = wcc[3]
                ax.plot(np.array(xw) / 3.281, np.array(yw) / 3.281, np.array(zw) / 3.281, 'k')
            else:
                # The element is in Zone 4:
                wall.hasCapacity['wind pressure']['external']['positive'] = wcc[0]
                wall.hasCapacity['wind pressure']['external']['negative'] = wcc[2]
                ax.plot(np.array(xw)/3.281, np.array(yw)/3.281, np.array(zw)/3.281, 'r')
        else:
            pass
    # Add impact resistance:
    wall.hasCapacity['debris impact'] = 0.0336 #0.0168  # lb ft/s, Vanmarcke paper, 3.1717 Barbato
# 1c) Asset Description: DAD pressure coefficients (wind loading):
wind_direction = 315
tpu_wdir = convert_to_tpu_wdir(wind_direction, target_bldg)
df_target_bldg_cps = map_tpu_ptaps(target_bldg, tpu_wdir, high_value_flag)
target_bldg.hasDemand['wind pressure']['external'] = df_target_bldg_cps  # Add coefficients/trib areas to data model
# Map pressure coefficients to building components:
map_ptaps_to_components(target_bldg, df_target_bldg_cps, roof_flag=True, facade_flag=True)
# Pressure fault tree:
#michael_wind_speed = 170
michael_wind_speed = 123.342  # 126? data model paper: 123.342
# Calculate the equivalent wind speed for Exposure B using the wind speed in Exposure C:
vg = (michael_wind_speed/2.237) / ((10 / 274.32) ** (1 / 9.5))
zg_b = 365.76
alpha_b = 7
michael_wind_speed_b = (vg * (10 / zg_b) ** (1 / alpha_b))*2.237
# Plot wind pressure damage to wall elements:
# fig = plt.figure()
# ax = plt.axes(projection='3d')
# wall_fail = df_fail_target.loc[df_fail_target['roof element']!= True, 'fail regions']
# for idx in wall_fail.index:
#     wall_geometry = wall_fail.loc[idx]
#     xw, yw, zw = [], [], []
#     for pt in list(wall_geometry.exterior.coords):
#         xw.append(pt[0])
#         yw.append(pt[1])
#         zw.append(pt[2])
#     ax.plot(xw, yw, zw, 'r')
# # Plot the building's geometry:
# for story in target_bldg.hasStory:
#     for poly in story.hasGeometry['3D Geometry']['local']:
#         xpoly, ypoly, zpoly = [], [], []
#         for pt in list(poly.exterior.coords):
#             xpoly.append(pt[0])
#             ypoly.append(pt[1])
#             zpoly.append(pt[2])
#         ax.plot(xpoly,ypoly,zpoly,'k')
# 2) Asset Descriptions: Source Building Parcel Models
df = pd.read_csv('C:/Users/Karen/Desktop/Parcel_data.csv')  # Parcel data
# Create data models for each potential source building:
site = Site()
plot_flag=False
length_unit='ft'
for p in df.index:
    if df['Parcel Id'][p] == '13209-060-000' or df['Parcel Id'][p] == '13209-040-000':
        new_bldg = Building()
        new_bldg.add_parcel_data(df['Parcel Id'][p], df['Stories'][p], df['Use Code'][p], df['Year Built'][p],
                                 df['Address'][p], df['Square Footage'][p], df['Longitude'][p], df['Latitude'][p],
                                 'ft', loc_flag=True)
        # Add roof element and data:
        new_roof = Roof()
        new_roof.hasCover = df['Roof Cover'][p]
        new_roof.hasType = df['Roof Cover'][p]
        if 'ENG' in df['Roof Cover'][p] or 'COMP' in df['Roof Cover'][p]:
            new_roof.hasShape['gable'] = True
            new_roof.hasPitch = degrees(atan2(2,12))
        else:
            new_roof.hasShape['flat'] = True
        if df['Roof Permit Year'][p] is not 'NONE':
            new_roof.hasYearBuilt = int(df['Roof Permit Year'][p])
            new_bldg.hasYearBuilt = new_roof.hasYearBuilt
        else:
            new_roof.hasYearBuilt = int(df['Year Built'][p])
        new_bldg.hasStory[-1].adjacentElement['Roof'] = [new_roof]
        new_bldg.hasStory[-1].update_elements()
        new_bldg.update_zones()
        new_bldg.update_elements()
        # Add height information:
        survey_data = SurveyData()
        survey_data.doe_ref_bldg(new_bldg, window_flag=False)
        # Get building footprint:
        assign_footprint(new_bldg, df['Stories'][p])
        get_ref_bldg_crs(target_bldg, new_bldg, length_unit)
        site.hasBuilding.append(new_bldg)
    else:
        pass
site.update_zones()
site.update_interfaces()
site.update_elements()
# 3) Probable wind-borne debris sources and source region:
length_unit = 'ft'
get_site_debris(site, length_unit)  # Grab all the debris types in this site
# Step 3: Calculate the trajectory of each debris type:
#wind_speed_arr = np.arange(70, 200, 5)
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
# df_debris.to_csv('D:/Users/Karen/Documents/Github/Typical_Debris_Distances.csv', index=False)
#run_debris(target_bldg, site, length_unit, wind_direction, wind_speed_arr)
# Find potential source buildings:
crs = 'reference cartesian'
wind_direction = 315
site_source = get_source_bldgs(target_bldg, site, wind_direction, michael_wind_speed_b, crs, length_unit)
# 4) Asset Description: Probable Source Buildings
# Here we add minimum component capacities and wind pressure coefficients to source buildings
roof_polys_list = []
rcc_list = []
for source_bldg in site_source.hasBuilding:
    # 4a) Specify the value of the property:
    high_value_flag = False
    # 4b) Populate C&C minimum capacities: Roof
    code_informed = FBC(source_bldg, loading_flag=False)
    code_informed.roof_attributes(code_informed.hasEdition, source_bldg)  # Add missing data --> roof pitch:
    exposure = 'B'
    roof_flag = True
    wall_flag = False
    zone_pts, roof_polys, rcc, wcc = get_cc_min_capacity(source_bldg, exposure, high_value_flag, roof_flag, wall_flag, source_gable_flag=True)
    roof_polys_list.append(roof_polys)
    rcc_list.append(rcc)
    # 4c) Get DAD pressure coefficients:
    tpu_wdir = convert_to_tpu_wdir(wind_direction, source_bldg)
    df_source_bldg_cps = map_tpu_ptaps(source_bldg, tpu_wdir, high_value_flag)  # taps and trib areas
    source_bldg.hasDemand['wind pressure']['external'] = df_source_bldg_cps
    # 5) Map pressure coefficients to building components:
    map_ptaps_to_components(source_bldg, df_source_bldg_cps, roof_flag=True, facade_flag=False)
# Fault tree analyses:
# Set up empty DataFrame:
df_site_debris = site_source.hasDebris['roof cover']
num_realizations = 500
target_pressure_list = []
target_debris = []
source_pressure_ftree = []
source2_pressure_list = []
source_roof_fail = []
for n in range(0, num_realizations):
    # Target building: Wind pressure fault tree
    df_pfail_target = wind_pressure_ftree(target_bldg, michael_wind_speed, facade_flag=True)
    target_pressure_list.append(df_pfail_target)
    pressure_fail_target = df_pfail_target['fail elements'].values
    # Source buildings: Wind pressure fault tree
    roof_fail = False
    source_pressure_list = []
    target_debris_list =[]
    for b in site_source.hasBuilding:
        df_fail_source = wind_pressure_ftree(b, michael_wind_speed, facade_flag=False)
        source_pressure_list.append(df_fail_source)
        df_roof_elems = df_fail_source.loc[df_fail_source['roof element']==True]
        if len(df_roof_elems.index.to_list()) > 0:
            roof_fail = True
            target_debris_dict = wbd_ftree(target_bldg, b, df_fail_source, df_site_debris, pressure_fail_target, michael_wind_speed_b,
                                   wind_direction, length_unit, plot_flag=True)
            target_debris_list.append(target_debris_dict)
        else:
            pass
    source_pressure_ftree.append(source_pressure_list)
    source_roof_fail.append(roof_fail)
    target_debris.append(target_debris_list)
    if roof_fail and (len(df_pfail_target) > 0):
        # Plot the target building's response to wind and WBD hazards:
        fig = plt.figure()
        ax = plt.axes(projection='3d')
        # Plot the roof damage and wbd trajectories:
        fig_plan, ax_plan = plt.subplots()
        # Walls first:
        wall_fail = df_pfail_target.loc[df_pfail_target['roof element'] != True, 'fail regions']
        for idx in wall_fail.index:
            wall_geometry = wall_fail.loc[idx]
            xw, yw, zw = [], [], []
            for pt in list(wall_geometry.exterior.coords):
                xw.append(pt[0])
                yw.append(pt[1])
                zw.append(pt[2])
            ax.plot(np.array(xw) / 3.281, np.array(yw) / 3.281, np.array(zw) / 3.281, 'r')
        # Roof next:
        roof_fail = df_pfail_target.loc[df_pfail_target['roof element'] == True, 'fail regions']
        for ridx in roof_fail.index:
            roof_geometry = roof_fail.loc[ridx]
            xroof, yroof, zroof = [], [], []
            for pt in list(roof_geometry.exterior.coords):
                xroof.append(pt[0])
                yroof.append(pt[1])
            ax.plot(np.array(xroof) / 3.281, np.array(yroof) / 3.281, np.ones(len(yroof))*target_bldg.hasGeometry['Height']/3.281 / 3.281, 'r')
        # Plot the building's wireframe geometry:
        for story in target_bldg.hasStory:
            for poly in story.hasGeometry['3D Geometry']['local']:
                xpoly, ypoly, zpoly = [], [], []
                for pt in list(poly.exterior.coords):
                    xpoly.append(pt[0])
                    ypoly.append(pt[1])
                    zpoly.append(pt[2])
                ax.plot(np.array(xpoly) / 3.281, np.array(ypoly) / 3.281, np.array(zpoly) / 3.281, 'k')
        # Plot the target building response to WBD:
        for tdict in target_debris_list:
            if len(tdict['fail element']) > 0:
                # Add target building fail elements due to WBD impact
                for i in range(0, len(tdict['fail region'])):
                    xf, yf = target_debris_dict['fail region'][i].exterior.xy
                    ax_plan.plot(np.array(xf) / 3.281, np.array(yf) / 3.281, 'b')
                    for elem in tdict['fail element'][i]:
                        if elem is None:
                            pass
                        else:
                            xe, ye, ze = [], [], []
                            for pt in list(elem.hasGeometry['3D Geometry']['local'].exterior.coords):
                                xe.append(pt[0])
                                ye.append(pt[1])
                                ze.append(pt[2])
                            ax.plot(np.array(xe)/3.281, np.array(ye)/3.281, np.array(ze)/3.281, 'b')
                    for j in target_debris_dict['flight path'][i]:
                        if j is not None:
                            xl, yl = j.xy
                            ax_plan.plot(np.array(xl) / 3.281, np.array(yl) / 3.281, 'b', linestyle='dashed')
                        else:
                            pass
            else:
                pass
        for b in site_source.hasBuilding:
            xb, yb = b.hasGeometry['Footprint']['reference cartesian'].minimum_rotated_rectangle.exterior.xy
            ax_plan.plot(np.array(xb) / 3.281, np.array(yb) / 3.281, 'k')
            dir_debris_region = df_site_debris.loc[
                df_site_debris['debris name'] == b.adjacentElement['Roof'][0].hasCover, 'directional debris region'].values[
                0]
            xdir, ydir = dir_debris_region.exterior.xy
            ax_plan.plot(np.array(xdir) / 3.281, np.array(ydir) / 3.281, color='orange', linewidth=2)
        xt, yt = target_bldg.hasGeometry['Footprint']['local'].exterior.xy
        ax_plan.plot(np.array(xt) / 3.281, np.array(yt) / 3.281, 'r')
        ax_plan.set_xlabel('x [m]')
        ax_plan.set_ylabel('y [m]')
        ax_plan.set_yticks(np.arange(-50, 200, 50))
        fig_plan.set_tight_layout(True)
        # Finish up 3D image:
        fig.set_tight_layout(True)
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
        # Set label styles:
        ax.set_zticks(np.arange(0, 20, 4))
        ax.xaxis.set_tick_params(labelsize=16)
        ax.yaxis.set_tick_params(labelsize=16)
        ax.zaxis.set_tick_params(labelsize=16)
        plt.show()
    else:
        pass
df_ftree = pd.DataFrame({'Target Wind Pressure': target_pressure_list})
# count_source += 1
# col_name = 'Source Pressure Ftree ' + str(count_source)
# df_ftree[col_name] = source_pressure_ftree
# df_ftree['Source WBD' + str(count_source)] = source_roof_fail
    # df_site_debris = site_source.hasDebris['roof cover']
    # for j in range(0, 100):
    #     target_bldg = wbd_ftree(target_bldg, source_bldg, df_fail_source, df_site_debris, michael_wind_speed, wind_direction, length_unit, plot_flag=True)
# Debris Fault Tree:
#df_ftree = pd.DataFrame({'Target Pressure Ftree': target_pressure_ftree})
#df_site_debris = site_source.hasDebris['roof cover']
# target_debris_ftree = []
# source_col_ftrees = []
# source_col_rdamage = []
# for b in range(0, len(site_source.hasBuilding)):
#     source_col_ftrees.append('Source Pressure Ftree ' + str(b+1))
#     source_col_rdamage.append('Source WBD' + str(b+1))
# for idx in df_ftree.index.to_list():
#     # First see if there was any source building damage to begin with:
#     if df_ftree.loc[idx][source_col_rdamage].any(axis='index'):
#         # Run WBD fault tree for each target and source pair:
#         for scol in range(0, len(source_col_ftrees)):
#             source_bldg = site_source.hasBuilding[scol]
#             df_fail_source = df_ftree.loc[idx][source_col_ftrees[scol]]
#             df_roof_elems = df_fail_source.loc[df_fail_source['roof element']==True]
#             if len(df_fail_source.loc[df_fail_source['roof element']==True]) > 0:
#                 target_wbd = wbd_ftree(target_bldg, source_bldg, df_fail_source, df_site_debris, michael_wind_speed,
#                               wind_direction,
#                               length_unit, plot_flag=True)
#             else:
#                 pass
#                 df_ftree['Target Debris Ftree']
#     else:
#         target_debris_ftree = 0
# fig, ax = plt.subplots()
# a = 0
# # Populate the building's Hurricane Michael loading demand:
# unit = 'english'
# # #wind_speed_file_path = 'D:/Users/Karen/Documents/Github/DPBWE/Datasets/WindFields/2018-Michael_windgrid_ver36.csv'
#generate_pressure_loading(target_bldg, michael_wind_speed, tpu_wind_direction, tpu_flag=True, csv_flag=False)