import matplotlib.pyplot as plt
import numpy as np
from geopy.distance import distance
from asset import Site, Building


def get_bldgs_at_dist(site, ref_bldg, dist, unit, plot_flag):
    # Given that a ref_bldg is within a site, what bldgs are within distance=dist from ref_bldg?
    ref_pt = ref_bldg.hasLocation['Geodesic']
    # Create an empty list to hold any qualifying bldg:
    bldg_list = []
    for bldg in site.hasBuilding:
        bldg_location = bldg.hasLocation['Geodesic']
        # Calculate the distance between ref_bldg and bldg:
        if unit == 'mi':
            bldg_dist = distance(ref_pt, bldg_location).miles
        elif unit == 'km':
            bldg_dist = distance(ref_pt, bldg_location).km
        # Check if the building is within the specified distance:
        if bldg_dist < dist:
            bldg_list.append(bldg)
            if plot_flag:
                # Plot the bldg's footprint:
                xs, ys = bldg.hasGeometry['Footprint']['geodesic'].exterior.xy
                plt.plot(xs, ys)
        else:
            pass
    # Finish plotting:
    if plot_flag:
        # Plot the ref_bldg footprint:
        rxs, rys = ref_bldg.hasGeometry['Footprint']['geodesic'].exterior.xy
        plt.plot(rxs, rys)
        # Add axes labels:
        plt.xlabel('Longitude')
        plt.ylabel('Latitude')
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


def calculate_new_internal_pressure(bldg):
    # Internal pressure recalculated as the average of external pressures at breached locations
    # Create an empty list to hold external pressures at breached locations:
    ext_pressures = []
    # Create an empty list to hold undamaged components:
    comp_list = []
    for key in bldg.adjacentElement:
        if key != 'Floor':
            for component in bldg.adjacentElement[key]:
                # Identify envelope components that have failed due to wind pressure:
                if component.hasFailure['wind pressure']:
                    # Access the component's wind pressure demand:
                    ext_pressures.append(component.hasDemand['wind pressure'])
                else:
                    comp_list.append(component)
    # Calculate the new internal pressure:
    ip = np.array(ext_pressures).mean()
    # Recalculate the wind pressures for each of the undamaged components:


def get_num_wtype(bldg, story_num, wtype, is_exterior, is_interior, direction):
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
                count = count+1
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
