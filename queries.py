import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import geopandas as gpd
from geopy.distance import distance
from shapely.geometry import Polygon, Point
from OBDM.zone import Site
from parcel import Parcel
from OBDM.element import Wall, Roof


def get_bldgs_at_dist(site, ref_bldg, dist, unit, plot_flag):
    # Given that a ref_bldg is within a site, what bldgs are within distance=dist from ref_bldg?
    ref_pt = ref_bldg.hasLocation['Geodesic']  # Shapely Point object
    if plot_flag:
        fig = plt.figure()
        ax = plt.axes()
    else:
        pass
    # Define the site area:
    angles = np.linspace(0, 360, 100)
    pt_list = []
    for angle in angles:
        if unit == 'mi':
            new_pt = distance(miles=dist).destination((ref_pt.y, ref_pt.x), angle)
        elif unit == 'km':
            new_pt = distance(kilometers=dist).destination((ref_pt.y, ref_pt.x), angle)
        pt_list.append((new_pt[1], new_pt[0]))
    query_area = Polygon(pt_list)  # Shapely Polygon
    # Create an empty list to hold any qualifying bldg:
    bldg_list = []
    for bldg in site.hasBuilding:
        bldg_location = bldg.hasLocation['Geodesic']  # Shapely Point object
        # Check if the building is within the specified distance:
        if bldg_location.within(query_area):
            bldg_list.append(bldg)
            if plot_flag:
                # Plot the bldg's footprint:
                xs, ys = bldg.hasGeometry['Footprint']['geodesic'].exterior.xy
                ax.plot(xs, ys)
        else:
            pass
    # Finish plotting:
    if plot_flag:
        # Plot the ref_bldg footprint:
        rxs, rys = ref_bldg.hasGeometry['Footprint']['geodesic'].exterior.xy
        ax.plot(rxs, rys)
        # Plot the query area:
        xq, yq = query_area.exterior.xy
        ax.plot(xq, yq)
        # Add axes labels:
        ax.set_xlabel('Longitude')
        ax.set_ylabel('Latitude')
        plt.show()
    else:
        pass
    return bldg_list


def get_debris_types(bldg_list):
    # What are the debris types of the buildings in bldg_list?
    debris_type_list = []
    for bldg in bldg_list:
        debris_type_list.append(bldg.adjacentElement['Roof'].hasType[0])
    return debris_type_list


def get_debris_types_at_dist(site, ref_bldg, dist, unit, plot_flag):
    # What are the debris types of buildings at dist from ref_bldg?
    # Find the buildings at dist from ref_bldg:
    bldg_list = get_bldgs_at_dist(site, ref_bldg, dist, unit, plot_flag)
    # Find their debris types:
    debris_type_list = get_debris_types(bldg_list)
    return debris_type_list


def calculate_new_opening_internal_pressure(bldg):
    # Internal pressure recalculated as average of external pressures at breaches
    # Create empty list to hold external pressures at breaches:
    ext_pressures = []
    # Create an empty list to hold undamaged components:
    comp_list = []
    for key in bldg.adjacentElement:
        if key == 'Walls' or key == 'Roof' or key == 'Windows':
            for component in bldg.adjacentElement[key]:
                # Identify envelope components that have failed due to wind pressure or debris:
                if component.hasFailure['wind pressure'] or component.hasFailure['debris impact']:
                    # Access the component's wind pressure demand:
                    ext_pressures.append(component.hasDemand['wind pressure']['external'])
                else:
                    # Add undamaged component:
                    comp_list.append(component)
        else:
            pass
    # Calculate the new internal pressure:
    int_pressure = np.array(ext_pressures).mean()
    # Recalculate wind pressures for each undamaged component:
    for comp in comp_list:
        comp.hasDemand['wind pressure']['internal'] = int_pressure
        comp.hasDemand['wind pressure']['total'] = comp.hasDemand['wind pressure']['external'] + int_pressure

def redistribute_r2w_loads(bldg):
    # Access the interfaces in the bldg and collect the r2w connections:
    # Create an empty list to hold all r2w connections:
    r2w_list = []
    # Create an empty list to hold all failed r2w connections:
    r2w_fail = []
    for interface in bldg.hasStorey[-1].hasInterface:
        # Check if this interface object includes a Roof object:
        if isinstance(interface.interfaceOf[0], Roof) or isinstance(interface.interfaceOf[1], Roof):
            # Check if this interface object includes a Wall object:
            if isinstance(interface.interfaceOf[0], Wall) or isinstance(interface.interfaceOf[1], Wall):
                r2w_list.append(interface)
                # Check the r2w connection for failure:
                if interface.hasFailure['shear force']:
                    r2w_fail.append(interface)
                else:
                    pass
            else:
                pass
        else:
            pass
    # For each failed r2w connection, find its nearest neighbors:
    for conn in r2w_fail:
        # For each failed r2w connection, find its nearest neighbors:
        near_conn = []
        for j in r2w_list:
            j.hasLocation




def get_num_and_dir_wtype(bldg, story_num, wtype, is_exterior, is_interior, direction):
    # For a given building, how many walls of type wtype are in Story story_num?
    # Create a dummy variable to start the count:
    count = 0
    # If direction query is needed, create empty list to hold all identified walls of wtype:
    if direction == 'x' or direction == 'y':
        wtype_list = []
    else:
        pass
    # Facilitate faster queries for strictly exterior components:
    if is_exterior:
        for wall in bldg.hasStorey[story_num-1].adjacentElement['Walls']:
            if wall.hasType == wtype:
                count = count + 1
                if direction == 'x' or direction == 'y':
                    wtype_list.append(wall)
            else:
                pass
    elif is_interior:
        # Facilitate faster queries for strictly interior components:
        if is_interior:
            for wall in bldg.hasStorey[story_num-1].containsElement['Walls']:
                if wall.hasType == wtype:
                    count = count + 1
                    if direction == 'x' or direction == 'y':
                        wtype_list.append(wall)
                else:
                    pass
    else:
        # Count the number of wtypes over all wall components:
        for wall in bldg.hasStorey[story_num-1].hasElement['Walls']:
            if wall.hasType == wtype:
                count = count+1
                if direction == 'x' or direction == 'y':
                    wtype_list.append(wall)
            else:
                pass
    # Determine the number of walls in the specified direction:
    if direction == 'x' or direction == 'y':
        direction_count = 0
        for wall in wtype_list:
            wline = wall.hasGeometry['1D Geometry']
            xs, ys = wline.xy
            xdist = xs[1]-xs[0]
            ydist = ys[1]-ys[0]
            if direction == 'x' and xdist > ydist:
                direction_count = direction_count + 1
            elif direction == 'y' and ydist > xdist:
                direction_count = direction_count + 1
            else:
                pass
    else:
        direction_count = None

    return count, direction_count


def get_story_wtype(bldg, story_num, wtype, is_exterior, is_interior):
    wall_list = []  # Create empty list to store Wall objects:
    if is_exterior:  # Query for exterior components
        for wall in bldg.hasStorey[story_num-1].adjacentElement['Walls']:
            if wall.hasType == wtype:
                wall_list.append(wall)
            else:
                pass
    elif is_interior:  # Query for interior components
        if is_interior:
            for wall in bldg.hasStorey[story_num-1].containsElement['Walls']:
                if wall.hasType == wtype:
                    wall_list.append(wall)
                else:
                    pass
    else:  # Loop through all components
        for wall in bldg.hasStorey[story_num-1].hasElement['Walls']:
            if wall.hasType == wtype:
                wall_list.append(wall)
            else:
                pass
    print('Number of walls with type ' + wtype + '=' + str(len(wall_list)))
    return wall_list


def get_wall_dir(wall, geom_rep):
    if geom_rep == 'rotated':
        wline = wall.hasGeometry['1D Geometry']['rotated']  # Shapely LineString Object
        xs, ys = wline.xy  # Access line points
        xdist = xs[1] - xs[0]  # Calculate x distance
        ydist = ys[1] - ys[0]  # Calculate y distance
        if xdist > ydist:
            wall.hasOrientation = 'x'
        else:
            wall.hasOrientation = 'y'
    else:
        print('Please define rotated Cartesian geometry')

# parcel_data = pd.read_csv('D:/Users/Karen/Documents/GitHub/DPBWE/Datasets/Parcels/ResSub.csv')
# bldg_list = []
# lon = -85.676188
# lat = 30.190142
# test = Parcel('12345', 4, 'Financial', 1989, '1002 23RD ST W PANAMA CITY 32405', 41134, lon, lat)
# # Define the site area:
# angles = np.linspace(0, 360, 100)
# pt_list = []
# unit = 'mi'
# dist = 0.25
# ref_pt = test.hasLocation['Geodesic']  # Shapely Point object
# for angle in angles:
#     if unit == 'mi':
#         new_pt = distance(miles=dist).destination((ref_pt.y, ref_pt.x), angle)
#     elif unit == 'km':
#         new_pt = distance(kilometers=dist).destination((ref_pt.y, ref_pt.x), angle)
#     pt_list.append((new_pt[1], new_pt[0]))
# site_poly = Polygon(pt_list)  # Shapely Polygon
# # Access file with region's building footprint information:
# jFile = 'D:/Users/Karen/Documents/GitHub/DPBWE/Datasets/Geojson/BayCounty.geojson'
# data = gpd.read_file(jFile)
# poly_list = []
# for row in range(0, len(data['geometry'])):
#     # Check if point is within the polygon in this row:
#     poly = data['geometry'][row]
#     bldg_pt = poly.centroid
#     if bldg_pt.within(site_poly):
#         poly_list.append(poly)
#     else:
#         pass
# fig = plt.figure()
# ax = plt.axes()
# for poly in poly_list:
#     xs, ys = poly.exterior.xy
#     ax.plot(xs, ys, 'k')
# xf, yf = test.hasGeometry['Footprint']['geodesic'].exterior.xy
# ax.plot(xf, yf)
# xsite, ysite = site_poly.exterior.xy
# ax.plot(xsite, ysite)
# plt.show()
# site = Site(bldg_list)
# new_list = get_bldgs_at_dist(site, test, 0.400, 'km', plot_flag=True)