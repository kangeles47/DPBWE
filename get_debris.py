from pandas import read_csv, DataFrame
from scipy.stats import norm, uniform
from geopy import distance
from shapely.geometry import Polygon, Point
from OBDM.zone import Site, Building
from OBDM.element import Roof
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
# Create decision trees to characterize missile environment and consequent debris trajectories
    # Might want to include here consideration of roof assembly condition (age)
    # Typical debris types: roof covers, roof sheathing, frame/joist elements (e.g., timber)
# Develop rulesets for site-specific debris classification for range of common typologies
# Map debris classes to appropriate trajectory models
# Develop decision trees to extract relevant component data from manufacturer's specifications to refine site-specific debris models
# Implement similitude parameters to project source building damage


def run_debris(bldg, site, length_unit, wind_direction, wind_speed):
    # Step 1: Identify potential source buildings given wind direction and target bldg:
    site_source = get_source_bldgs(bldg, site, wind_direction)
    # Step 2: Get debris characteristics and corresponding trajectory parameters for the site:
    get_site_debris(site_source, length_unit)
    # Step 3: Calculate the trajectory of each debris type:
    # traj_dict = {'wind speed': [], 'debris name': [], 'alongwind': [], 'acrosswind': []}
    # for speed in wind_speed:
    #     for key in site_source.hasDebris:
    #         for row in range(0, len(site_source.hasDebris[key])):
    #             model_input = site_source.hasDebris[key].iloc[row]
    #             alongwind_dist, acrosswind_dist = get_trajectory(model_input, speed, length_unit)
    #             traj_dict['alongwind'].append(alongwind_dist)
    #             traj_dict['acrosswind'].append(acrosswind_dist)
    #             traj_dict['wind speed'].append(speed)
    #             traj_dict['debris name'].append(site_source.hasDebris[key]['debris name'][row])
    #a=0


def get_site_debris(site, length_unit):
    """
    A function that populates debris types within a site and their parameters for subsequent trajectory calculations.
    Updates the site.hasDebris attribute.

    :param site: A Site object containing all potential source buildings (derived using get_source_bldgs)
    :param length_unit: String, set to 'ft' or 'm'. Supports query of debris characteristics in get_debris_mass.
    :return:
    """
    debris_type = {'roof cover': [], 'roof sheathing': [], 'roof member': []}  # 3 most common debris types
    for bldg in site.hasBuilding:
        # Step 1: Extract roof information for each building in the Site description:
        # Roof Cover
        if bldg.adjacentElement['Roof'][0].hasCover not in debris_type['roof cover'] and (
                bldg.adjacentElement['Roof'][0].hasCover is not None):
            debris_type['roof cover'].append(bldg.adjacentElement['Roof'][0].hasCover)
        # Roof Sheathing
        if bldg.adjacentElement['Roof'][0].hasSheathing not in debris_type['roof sheathing'] and (
                bldg.adjacentElement['Roof'][0].hasSheathing is not None):
            debris_type['roof sheathing'].append(bldg.adjacentElement['Roof'][0].hasSheathing)
        # Roof Structure
        if bldg.adjacentElement['Roof'][0].hasStructureType not in debris_type['roof member'] and (
                bldg.adjacentElement['Roof'][0].hasStructureType is not None):
            debris_type['roof member'].append(bldg.adjacentElement['Roof'][0].hasStructureType)
    # Step 2: Get debris characteristics:
    for key in debris_type:
        dtype_dict = {'debris name': debris_type[key]}
        dclass_list = []
        dmass_list = []
        for name in debris_type[key]:
            # Step 2a: Find the debris class:
            debris_class = get_debris_class(key, name)
            dclass_list.append(debris_class)
            # Step 2b: Find the debris mass:
            debris_area, debris_mass = get_debris_mass(debris_class, name, length_unit)
            dmass_list.append(debris_mass)
            # Step 2c: Find the debris' remaining trajectory parameters:
            param_dict = get_traj_params(debris_class)
        # Step 3: Compile into dictionary for the debris type:
        dtype_dict['debris class'] = dclass_list
        dtype_dict['debris mass'] = dmass_list
        dtype_dict.update(param_dict)
        # Step 4: Integrate into site's data model:
        site.hasDebris[key] = DataFrame(dtype_dict)


def get_source_bldgs(bldg, site, wind_direction):
    """
    A function that defines the potential source region for the given Building location and wind direction.
    A function that then loops through the given Site object to identify Buildings within the potential source region.

    :param bldg: A Building object with location information
    :param site: A Site object containing Building objects with location and debris information (e.g., roof cover)
    :return: site_source: A Site object with Building objects within the specified potential source region (see Site.hasBuilding)
    """
    # Step 1: Define a maximum debris source region using the wind direction:
    wdirs = np.arange(wind_direction-45, wind_direction+45, 5)
    pt_list = [bldg.hasLocation['Geodesic']]
    for dir in wdirs:
        if bldg.hasGeometry['Length Unit'] == 'ft':
            new_point = distance.distance(miles=1).destination((bldg.hasLocation['Geodesic'].y, bldg.hasLocation['Geodesic'].x), dir)
            pt_list.append(Point(new_point[1], new_point[0]))
        elif bldg.hasGeometry['Length Unit'] == 'm':
            new_point = distance.distance(kilometers=1.61).destination((bldg.hasLocation['Geodesic'].y, bldg.hasLocation['Geodesic'].x), dir)
            pt_list.append(Point(new_point[1], new_point[0]))
    # Create a Polygon object for the debris source region:
    debris_region = Polygon(pt_list)
    xpoly, ypoly = debris_region.exterior.xy
    ax, fig = plt.subplots()
    plt.plot(xpoly, ypoly)
    # Step 2: Find potential source buildings and add to new Site object:
    site_source = Site()
    for i in site.hasBuilding:
        if debris_region.contains(i.hasLocation['Geodesic']):
            # Add this potential source bldg to new Site object:
            site_source.hasBuilding.append(i)
            plt.scatter(i.hasLocation['Geodesic'].x, i.hasLocation['Geodesic'].y)
        else:
            pass
    plt.show()
    return site_source


def get_trajectory(model_input, wind_speed, length_unit):
    """
    A function to generate random variables for the debris alongwind and acrosswind trajectory.

    :param model_input: Dictionary with input parameters for trajectory calculation: debris mass, coefficients (C, c1, c2, c3), flight time
    :param wind_speed: The wind speed value to calculate the trajectory distances for (in mph or m/s)
    :param length_unit: The length unit for the wind speed, set to 'mi' or 'm'
    :return: alongwind_dist: A random variable for the alongwind distance, evaluated at the given wind speed.
    acrosswind_dist: A random variable for the acrosswind distance, evaluated at the given wind speed.
    """
    # Set up global parameter values:
    if length_unit == 'm':
        air_density = 1.225  # kg/m^3
        gravity = 9.81  # m/s^2
    elif length_unit == 'ft':
        air_density = 0.0765  # lb/ft^3
        gravity = 32.2  # ft/s^2
        wind_speed = wind_speed*1.467  # ft/s
    # Populate parameters for stochastic flight trajectory model:
    # Calculate Tachikawa number:
    idx = model_input['debris mass'].index[0]
    tachikawa_num = air_density*(wind_speed**2)/(2*model_input['debris mass'][idx]*gravity)
    # Populate coefficients and flight time RV:
    c, c1, c2, c3, flight_time = model_input['c'], model_input['c1'], model_input['c2'], model_input['c3'], model_input['flight time']
    norm_time = flight_time.rvs()*gravity/wind_speed  # roof-level or use basic wind speed at site
    # Calculate mu_x (mean of alongwind distance):
    alongwind_mean = (2*model_input['debris mass'][idx]/air_density)*((0.5*c*(tachikawa_num*norm_time)**2) + (c1*(tachikawa_num*norm_time)**3) + (c2*(tachikawa_num*norm_time)**4) + (c3*(tachikawa_num*norm_time)**5))
    if alongwind_mean < 0:
        alongwind_mean = 0
    # Initialize remaining distribution parameters:
    sigma_along = 0.35*alongwind_mean
    sigma_across = 0.35*alongwind_mean
    # Current data availability --> alongwind and across wind displacements are independent:
    alongwind_dist = norm.rvs(loc=alongwind_mean, scale=sigma_along)
    acrosswind_dist = norm.rvs(loc=0, scale=sigma_across)
    # Add to building data model:
    #bldg.hasDebrisTrajectory[key]['alongwind'], bldg.adjacentElement['Roof'][0].hasDebrisTrajectory[key]['alongwind'] = alongwind_dist, alongwind_dist
    #bldg.hasDebrisTrajectory[key]['acrosswind'], bldg.adjacentElement['Roof'][0].hasDebrisTrajectory[key]['acrosswind'] = acrosswind_dist, acrosswind_dist

    return alongwind_dist, acrosswind_dist


def get_debris_class(debris_type, debris_name):
    """
    A function to determine the given debris_type's corresponding debris class according to (Wills et al. 2002)

    :param debris_type: String, set to 'roof cover', 'roof sheathing', or 'roof member'
    :param debris_name: String, the common name for the debris type (e.g., asphalt shingles)
    :return: debris_class: String, set to 'compact', 'sheet' or 'rod' depending on debris type and name
    """
    # Three debris classes to choose from: sheet/plate, compact, and rod-like:
    # Define global types:
    sheet_type = ['TILE', 'SHINGLE', 'SLATE', 'BUR', 'BUILT-UP', 'SHAKE', 'PLY', 'SPM', 'POLY', 'METAL', 'SHNGL']
    rod_type = ['WOOD', 'JOIST', 'OWSJ', 'TRUSS']  # global list of structural types with frame members
    if debris_type == 'roof cover':
        if 'GRAVEL' in debris_name.upper():
            debris_class = 'compact'
        elif any([stype in debris_name.upper() for stype in sheet_type]):
            debris_class = 'sheet'
    elif debris_type == 'roof sheathing':
        debris_class = 'sheet'
    elif debris_type == 'roof member':
        if any([rtype in debris_name.upper() for rtype in rod_type]):
            debris_class = 'rod'
        else:
            debris_class = None
    return debris_class


def get_debris_mass(debris_class, debris_name, length_unit):
    """
    A function to extract the typical debris mass (and area, if applicable) for the given debris class and name.
    Values for mass and area are derived from open data sources and are populated into Typical_Debris_Masses.csv
    See REFERENCES and ACCESS DATE data fields for provenance information for each data entry.

    :param debris_class: String, the Wills et al. (2002) classification for the debris.
    :param debris_name: String, the common name for the debris type (e.g., asphalt shingles)
    :param length_unit: String, set to 'ft' or 'm'
    :return: debris_mass: Float, the typical debris mass (derived from open data sources)
    """
    # Load debris mass data (in the future, extend to regional manufacturers):
    df = read_csv('D:/Users/Karen/Documents/Github/DPBWE/Datasets/Debris/Typical_Debris_Masses.csv')
    if debris_class == 'sheet':
        if 'ASPHALT' in debris_name.upper():
            df_sub = df['DEBRIS NAME'].str.contains('ASPHALT')
            # Search for any special cases:
            scase = ['ARCH', 'LAM', 'DIM']
            if any([case in debris_name.upper() for case in scase]):
                if length_unit == 'ft':
                    debris_area = df_sub['DEBRIS NAME'].str.contains('ARCH')['TYPICAL AREA FT2']
                    debris_mass = df_sub['DEBRIS NAME'].str.contains('ARCH')['MASS PER AREA LB/FT2']
                else:
                    debris_area = df_sub['DEBRIS NAME'].str.contains('ARCH')['TYPICAL AREA M2']
                    debris_mass = df_sub['DEBRIS NAME'].str.contains('ARCH')['MASS PER AREA KG/M2']
            else:
                if length_unit == 'ft':
                    debris_area = df_sub['DEBRIS NAME'].str.contains('TAB')['TYPICAL AREA FT2']
                    debris_mass = df_sub['DEBRIS NAME'].str.contains('TAB')['MASS PER AREA LB/FT2']
                else:
                    debris_area = df_sub['DEBRIS NAME'].str.contains('TAB')['TYPICAL AREA M2']
                    debris_mass = df_sub['DEBRIS NAME'].str.contains('TAB')['MASS PER AREA KG/M2']
        else:
            if 'COMP' in debris_name.upper():
                df_sub = df.loc[df['DEBRIS NAME'] == 'COMPOSITE SHINGLE']
            elif 'MOD METAL' in debris_name.upper() or 'MODULAR MT' in debris_name.upper():
                df_sub = df.loc[df['DEBRIS NAME'] == 'METAL ROOFING - ALUMINUM OR STEEL - PANEL']
            elif 'BUILT' in debris_name.upper() and 'GRAVEL' not in debris_name.upper():
                df_sub = df.loc[df['DEBRIS NAME']=='BUILT-UP ROOF MEMBRANE 3-PLY SMOOTH-SURFACED']
            if length_unit == 'ft':
                debris_area = df_sub['TYPICAL AREA FT2']
                debris_mass = df_sub['MASS PER AREA LB/FT2']
            else:
                debris_area = df_sub['TYPICAL AREA M2']
                debris_mass = df_sub['MASS PER AREA KG/M2']
    else:
        debris_area = None
        debris_mass = None
        print('No debris mass or area information available for this type')
    return debris_area, debris_mass


def get_traj_params(debris_class):
    param_dict = {'c': None, 'c1': None, 'c2': None, 'c3': None, 'flight time': None}
    # Find flight time and coefficients for the debris class:
    if debris_class == 'sheet':
        param_dict['flight time'] = uniform(1, 2.5-1)  # This will be a uniform distribution
        param_dict['c'] = 0.911
        param_dict['c1'] = -0.148
        param_dict['c2'] = 0.024
        param_dict['c3'] = -0.0014
    elif debris_class == 'rod':
        param_dict['c'] = 0.801
        param_dict['c1'] = -0.16
        param_dict['c2'] = 0.036
        param_dict['c3'] = -0.0032
    elif debris_class == 'spheres' or debris_class == 'compact':
        param_dict['c'] = 0.496
        param_dict['c1'] = 0.084
        param_dict['c2'] = -0.1
        param_dict['c3'] = 0.006
    elif debris_class == 'cube':
        param_dict['c'] = 0.809
        param_dict['c1'] = -0.036
        param_dict['c2'] = -0.052
        param_dict['c3'] = 0.008
    return param_dict


def calc_impact_momentum(debris_mass, debris_area, horiz_impact_vel):
    return debris_mass* debris_area* horiz_impact_vel


def get_horiz_impact_vel(wind_speed, c, tachikawa_num, gravity, horiz_fdist):
    from math import exp, sqrt
    x = gravity*horiz_fdist/(wind_speed**2)
    horiz_impact_vel = wind_speed*(1-exp(-1*sqrt(2*c*tachikawa_num*x)))
    return horiz_impact_vel


# Testing the workflow:
# Step 1: Generate Building data models for each building in a site:
site = Site()
df = pd.read_csv('D:/Users/Karen/Documents/Github/DPBWE/BC_CParcels.csv')
for row in range(0, len(df['Parcel Id'])):
    new_bldg = Building()
    pid, num_stories, occupancy = df['Parcel Id'][row], df['Stories'][row], df['Use Code'][row]
    yr_built, address, area = df['Year Built'][row], df['Address'][row], df['Square Footage'][row]
    lon, lat, length_unit = df['Longitude'][row], df['Latitude'][row], 'ft'
    if 'PANAMA CITY BEACH' in address or 'MEXICO BEACH' in address:
        pass
    else:
        new_bldg.add_parcel_data(pid, num_stories, occupancy, yr_built, address, area, lon, lat, length_unit, loc_flag=True)
        # Add roof element and data:
        new_roof = Roof()
        new_roof.hasCover = df['Roof Cover'][row]
        new_roof.hasType = df['Roof Cover'][row]
        new_bldg.hasStory[-1].adjacentElement['Roof'] = [new_roof]
        new_bldg.hasStory[-1].update_elements()
        new_bldg.update_zones()
        new_bldg.update_elements()
        new_bldg.update_interfaces()
        site.hasBuilding.append(new_bldg)
        # Pull case study building:
        if new_bldg.hasID == '13209-055-000':
            bldg = new_bldg
        else:
            pass
site.update_zones()
site.update_elements()
site.update_interfaces()
# Step 2: Run through the debris workflow:
wind_speed = np.arange(70, 200, 10)
wind_direction = 0
run_debris(bldg, site, length_unit, wind_direction, wind_speed)