# -------------------------------------------------------------------------------
# Name:             query.py
# Purpose:          Provide example queries to access building information using the ontology-based data model
#
# Author:           Karen Irely Angeles (kangeles@nd.edu)
# Affiliation:      Department of Civil and Environmental Engineering and Earth Sciences,
#                   University of Notre Dame, Notre Dame, IN

# Last updated:          (v1) 01/20/2021
# ------------------------------------------------------------------------------
import matplotlib.pyplot as plt
import numpy as np
from geopy.distance import distance
from shapely.geometry import Polygon
from OBDM.element import Wall, Roof


def get_bldgs_at_dist(site, ref_bldg, dist, unit, plot_flag):
    """
    A function to determine what buildings are within a given distance from the provided reference building.

    Uses the reference building's geodesic location to create a circle with radius = dist
    Determines what buildings in site are within the specified distance
    Plots the reference building and its surrounding buildings (if plot_flag == True and all buildings have footprints)

    :param site: A Site object with Building objects in its hasBuilding attribute
    :param ref_bldg: A Building object with at least geodesic description of its location and footprint
    :param dist: A numeric value providing the query distance in either miles or kilometers
    :param unit: A string equal to either 'mi' or 'km'
    :param plot_flag: A Boolean equal to True if plotting is desired or False if otherwise
    :return: bldg_lst: A list of Building objects within the specified query distance from the reference building
    """
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
            new_pt = distance(miles=dist).destination((ref_pt.y, ref_pt.x), angle)  # input point (lat, lon)
        elif unit == 'km':
            new_pt = distance(kilometers=dist).destination((ref_pt.y, ref_pt.x), angle)  # input point (lat, lon)
        pt_list.append((new_pt[1], new_pt[0]))
    query_area = Polygon(pt_list)  # Shapely Polygon
    # Create an empty list to hold any qualifying bldg:
    bldg_list = []
    for bldg in site.hasBuilding:
        bldg_footprint = bldg.hasGeometry['Footprint']['geodesic']  # Shapely Point object
        # Check if the building is within the specified distance:
        if bldg_footprint.within(query_area) or bldg_footprint.intersects(query_area):
            bldg_list.append(bldg)
            if plot_flag:
                # Plot the bldg's footprint:
                xs, ys = bldg_footprint.exterior.xy
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


def calculate_new_opening_internal_pressure(bldg):
    """
    A function that recalculates the internal pressure for a Building object.

    :param bldg: A Building object with Elements and their corresponding loading and failure descriptions
    :return: updates component-specific attributes of loading demand
    """
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


def get_story_wtype(bldg, story_num, wtype, is_exterior, is_interior):
    """
    A function to find all the walls within a Story that are of the given type, wtype

    :param bldg: A Building object with Wall descriptions
    :param story_num: The story number the query will be executed on (e.g., 1 = first story)
    :param wtype: A string describing the wall type the quantity takeoff will be performed for
    :param is_exterior: A Boolean indicating whether the given wtype is strictly for exterior walls (True if yes)
    :param is_interior: A Boolean indicating whether the given wtype is strictly for exterior walls (True if yes)
    :return: wall_list: A list of Wall objects with type, wtype
    """
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
