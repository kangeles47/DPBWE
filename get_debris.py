from pandas import read_csv, DataFrame
from scipy.stats import norm, uniform
from scipy.interpolate import interp1d
from geopy import distance
from shapely.geometry import Polygon, Point, LineString
from shapely.ops import split
from shapely.affinity import rotate
from OBDM.zone import Site, Building
from OBDM.element import Roof
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import rcParams

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
    traj_dict = {'wind speed': [], 'debris name': [], 'alongwind': [], 'acrosswind': []}
    for speed in wind_speed:
        for key in site_source.hasDebris:
            for row in range(0, len(site_source.hasDebris[key])):
                model_input = site_source.hasDebris[key].iloc[row]
                alongwind_dist, acrosswind_dist = get_trajectory(model_input, speed, length_unit, mcs_flag=False)
                traj_dict['alongwind'].append(alongwind_dist)
                traj_dict['acrosswind'].append(acrosswind_dist)
                traj_dict['wind speed'].append(speed)
                traj_dict['debris name'].append(site_source.hasDebris[key]['debris name'][row])
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
        darea_list = []
        for name in debris_type[key]:
            # Step 2a: Find the debris class:
            debris_class = get_debris_class(key, name)
            dclass_list.append(debris_class)
            # Step 2b: Find the debris mass:
            debris_area, debris_mass = get_debris_mass(debris_class, name, length_unit)
            dmass_list.append(debris_mass)
            darea_list.append(debris_area)
            # Step 2c: Find the debris' remaining trajectory parameters:
            param_dict = get_traj_params(debris_class)
        # Step 3: Compile into dictionary for the debris type:
        dtype_dict['debris class'] = dclass_list
        dtype_dict['debris mass'] = dmass_list
        dtype_dict['debris area'] = darea_list
        dtype_dict.update(param_dict)
        # Step 4: Integrate into site's data model:
        site.hasDebris[key] = DataFrame(dtype_dict)


def get_source_bldgs(bldg, site, wind_direction, wind_speed, crs, length_unit):
    """
    A function that defines the potential source region for the given Building location and wind direction.
    A function that then loops through the given Site object to identify Buildings within the potential source region.

    :param bldg: A Building object with location information
    :param site: A Site object containing Building objects with location and debris information (e.g., roof cover)
    :return: site_source: A Site object with Building objects within the specified potential source region (see Site.hasBuilding)
    """
    # Step 1: Extract trajectory information for each unique debris type:
    df = pd.read_csv('C:/Users/Karen/Desktop/DebrisTypicalDistances.csv')  # Distances in [ft]
    df_source = pd.DataFrame(columns=df.columns)
    # Set up plotting:
    rcParams['font.family'] = "Times New Roman"
    rcParams.update({'font.size': 18})
    fig, ax = plt.subplots()
    # Set up dividing (unit conversion) if needed:
    if length_unit == 'ft':
        div = 3.281
    else:
        div = 1
    # Find probable source buildings:
    if wind_direction is None:
        # Find exposure region for each debris type:
        traj_list = []
        debris_name = []
        for key in site.hasDebris:
            for d in site.hasDebris[key]['debris name']:
                debris_name.append(d)
                if wind_speed in df['wind speed'].unique():
                    idx = df.loc[(df['debris name'] == d) & (df['wind speed'] == wind_speed)].index[0]
                    traj_list.append(df.iloc[idx]['alongwind_mean'] + df.iloc[idx]['alongwind_std_dev'])
                else:
                    # Interpolate the alongwind distance:
                    # Find the wind speed's nearest multiple of five:
                    nearest_five = 5 * round(wind_speed / 5)
                    if nearest_five > wind_speed:
                        idx_upper = df.loc[(df['debris name'] == d) & (df['wind speed'] == nearest_five)].index[0]
                        idx_lower = df.loc[(df['debris name'] == d) & (df['wind speed'] == nearest_five-5)].index[0]
                        xi = np.array([nearest_five-5, nearest_five])
                    else:
                        idx_upper = df.loc[(df['debris name'] == d) & (df['wind speed'] == nearest_five + 5)].index[0]
                        idx_lower = df.loc[(df['debris name'] == d) & (df['wind speed'] == nearest_five)].index[0]
                        xi = np.array([nearest_five, nearest_five + 5])
                    yi = np.array([df.iloc[idx_lower]['alongwind_mean'] + df.iloc[idx_lower]['alongwind_std_dev'],
                                   df.iloc[idx_upper]['alongwind_mean'] + df.iloc[idx_upper]['alongwind_std_dev']])
                    f = interp1d(xi, yi)
                    traj_list.append(f(wind_speed))
        if crs == 'reference cartesian':
            # Plot the building footprint:
            xo, yo = bldg.hasGeometry['Footprint']['local'].exterior.xy
            ax.plot(np.array(xo)/div, np.array(yo)/div, 'r')
            linestyle_list = ['-', '--', ':', '-.', '+', '^', 's', '*', '8']
            # Use the reference building's footprint as origin:
            origin = bldg.hasGeometry['Footprint']['local'].centroid
            for i in range(0, len(traj_list)):
                if traj_list[i] != 0:
                    buffer_poly = origin.buffer(traj_list[i])
                    xb, yb = buffer_poly.exterior.xy
                else:
                    pass
                ax.plot(np.array(xb)/div, np.array(yb)/div, linestyle_list[i], label=debris_name[i])
            plt.legend(fontsize=14)
            plt.show()
        else:
            pass
    else:
        # Find the wind speed's nearest multiple of five:
        nearest_five = 5 * round(wind_speed / 5)
        for key in site.hasDebris:
            for d in site.hasDebris[key]['debris name']:
                idx = df.loc[(df['debris name'] == d) & (df['wind speed'] == nearest_five)].index[0]
                df_source = df_source.append(df.iloc[idx], ignore_index=True)
        # Step 2: Find the maximum probable debris source distance (mean + std_dev):
        max_idx = df_source.loc[df_source['alongwind_mean'] == max(df_source['alongwind_mean'])].index[0]
        max_dist = df_source['alongwind_mean'][max_idx] + df_source['alongwind_std_dev'][max_idx]
        # Step 3: Find potential source buildings using the wind direction and max probable distance:
        if crs == 'geographic':
            wdirs = np.arange(wind_direction-90, wind_direction+90, 5)
            pt_list = [bldg.hasLocation['Geodesic']]
            for dir in wdirs:
                if length_unit == 'ft':
                    new_point = distance.distance(miles=max_dist/5280).destination((bldg.hasLocation['Geodesic'].y, bldg.hasLocation['Geodesic'].x), dir)
                    pt_list.append(Point(new_point[1], new_point[0]))
                elif length_unit == 'm':
                    new_point = distance.distance(kilometers=max_dist/3281).destination((bldg.hasLocation['Geodesic'].y, bldg.hasLocation['Geodesic'].x), dir)
                    pt_list.append(Point(new_point[1], new_point[0]))
            # Create a Polygon object for the debris source region:
            debris_region = Polygon(pt_list)
            # Pull the reference building's footprint geometry for plotting:
            xr, yr = bldg.hasGeometry['Footprint']['geodesic'].exterior.xy
        elif crs == 'reference cartesian':
            # Convert max_dist if necessary:
            if length_unit == 'ft':
                pass
            elif length_unit == 'm':
                max_dist = max_dist/3.281
            # Use the reference building's footprint as origin:
            origin = bldg.hasGeometry['Footprint']['local'].centroid
            # Create a circle geometry that we will then segment to find debris region:
            buffer_poly = origin.buffer(max_dist)
            # Create intersecting line:
            new_pt1 = Point(origin.x + max_dist, origin.y)
            new_pt2 = Point(origin.x - max_dist, origin.y)
            iline = LineString([new_pt1, new_pt2])
            # Rotate line according to wind direction:
            iline = rotate(iline, -1*wind_direction+180)
            # Split the circle using the intersecting line:
            spolys = split(buffer_poly, iline)
            # Grab the half corresponding to wind direction's query area:
            if 0 < wind_direction < 180:
                if spolys[0].centroid.x > origin.x:
                    debris_region = spolys[0]
                else:
                    debris_region = spolys[1]
            elif 180 < wind_direction < 360:
                if spolys[0].centroid.x < origin.x:
                    debris_region = spolys[0]
                else:
                    debris_region = spolys[1]
            elif wind_direction == 0:
                if spolys[0].centroid.y > origin.y:
                    debris_region = spolys[0]
                else:
                    debris_region = spolys[1]
            elif wind_direction == 180:
                if spolys[0].centroid.y < origin.y:
                    debris_region = spolys[0]
                else:
                    debris_region = spolys[1]
            # Pull the reference building's footprint geometry for plotting:
            xr, yr = bldg.hasGeometry['Footprint']['local'].exterior.xy
    # Plot the debris region:
    xpoly, ypoly = debris_region.exterior.xy
    plt.plot(np.array(xpoly)/3.281, np.array(ypoly)/3.281, 'b', linewidth=2)
    # Step 4: Find potential source buildings and add to new Site object:
    site_source = Site()
    for i in site.hasBuilding:
        if crs == 'geographic':
            bldg_loc = i.hasGeometry['Footprint']['geodesic']
        elif crs == 'reference cartesian':
            bldg_loc = i.hasGeometry['Footprint']['reference cartesian']
        if debris_region.contains(bldg_loc) or debris_region.intersects(bldg_loc):
            # Add this potential source bldg to new Site object:
            site_source.hasBuilding.append(i)
            xi, yi = bldg_loc.exterior.xy
            plt.plot(np.array(xi)/div, np.array(yi)/div, 'k')
        else:
            pass
    # Plot the reference building's footprint:
    plt.plot(np.array(xr)/div, np.array(yr)/div, 'r')
    plt.xlabel('x [m]')
    plt.ylabel('y [m]')
    plt.show()
    return site_source


def get_trajectory(model_input, wind_speed, length_unit, mcs_flag):
    """
    A function to generate random variables for the debris alongwind and acrosswind trajectory.

    :param model_input: Dictionary with input parameters for trajectory calculation: debris mass, coefficients (C, c1, c2, c3), flight time
    :param wind_speed: The wind speed value to calculate the trajectory distances for (in mph or m/s)
    :param length_unit: The length unit for the wind speed, set to 'mi' or 'm'
    :param mcs_flag: (Boolean) True if this is an MCS simulation and report mean values for along/across wind distance
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
    tachikawa_num = air_density*(wind_speed**2)/(2*model_input['debris mass']*gravity)
    # Populate coefficients and flight time RV:
    c, c1, c2, c3, flight_time = model_input['c'], model_input['c1'], model_input['c2'], model_input['c3'], model_input['flight time']
    if mcs_flag:
        samples = 5000
    else:
        samples = 1
    # Calculate the alongwind and acrosswind distance:
    alongwind_dist = []
    acrosswind_dist = []
    for i in range(0, samples):
        norm_time = flight_time.rvs() * gravity / wind_speed  # roof-level or use basic wind speed at site
        # Calculate mu_x (mean of alongwind distance):
        alongwind_mu = (2*model_input['debris mass']/air_density)*((0.5*c*(tachikawa_num*norm_time)**2) + (c1*(tachikawa_num*norm_time)**3) + (c2*(tachikawa_num*norm_time)**4) + (c3*(tachikawa_num*norm_time)**5))
        count = 0
        while alongwind_mu < 0:
            norm_time = flight_time.rvs() * gravity / wind_speed  # roof-level or use basic wind speed at site
            # Calculate mu_x (mean of alongwind distance):
            alongwind_mu = (2 * model_input['debris mass'] / air_density) * (
                        (0.5 * c * (tachikawa_num * norm_time) ** 2) + (c1 * (tachikawa_num * norm_time) ** 3) + (
                            c2 * (tachikawa_num * norm_time) ** 4) + (c3 * (tachikawa_num * norm_time) ** 5))
            count += 1
            if count == 200:
                alongwind_mu = 0
                break
            else:
                pass
        # Initialize remaining distribution parameters:
        sigma_along = 0.35*alongwind_mu
        sigma_across = 0.35*alongwind_mu
        # Current data availability --> alongwind and across wind displacements are independent:
        alongwind_dist.append(norm.rvs(loc=alongwind_mu, scale=sigma_along))
        acrosswind_dist.append(norm.rvs(loc=0, scale=sigma_across))
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
    sheet_type = ['TILE', 'SHINGLE', 'SLATE', 'BUR', 'BUILT-UP', 'SHAKE', 'PLY', 'SPM', 'POLY', 'METAL',
                  'SHNGL', 'STAND', 'MODULAR MT', 'ENG SHINGL', 'COMP SHNGL']
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
    df = read_csv('C:/Users/Karen/PycharmProjects/DPBWE/Datasets/Debris/Typical_Debris_Masses.csv')
    df.astype({'TYPICAL AREA FT2': 'float64', 'MASS PER AREA LB/FT2': 'float64', 'TYPICAL AREA M2': 'float64',
               'MASS PER AREA KG/M2': 'float64'})
    if debris_class == 'sheet':
        if 'ASPHALT' in debris_name.upper() or 'ENG' in debris_name.upper():
            df_sub = df.loc[df['DEBRIS NAME'].str.contains('ASPHALT')]
            # Search for any special cases:
            scase = ['ARCH', 'LAM', 'DIM']
            if any([case in debris_name.upper() for case in scase]):
                if length_unit == 'ft':
                    debris_area = df_sub.loc[df_sub['DEBRIS NAME'].str.contains('ARCH')]['TYPICAL AREA FT2'].values[0]
                    debris_mass = df_sub.loc[df_sub['DEBRIS NAME'].str.contains('ARCH')]['MASS PER AREA LB/FT2'].values[0]
                else:
                    debris_area = df_sub.loc[df_sub['DEBRIS NAME'].str.contains('ARCH')]['TYPICAL AREA M2'].values[0]
                    debris_mass = df_sub.loc[df_sub['DEBRIS NAME'].str.contains('ARCH')]['MASS PER AREA KG/M2'].values[0]
            else:
                if length_unit == 'ft':
                    debris_area = df_sub.loc[df_sub['DEBRIS NAME'].str.contains('TAB')]['TYPICAL AREA FT2'].values[0]
                    debris_mass = df_sub.loc[df_sub['DEBRIS NAME'].str.contains('TAB')]['MASS PER AREA LB/FT2'].values[0]
                else:
                    debris_area = df_sub.loc[df_sub['DEBRIS NAME'].str.contains('TAB')]['TYPICAL AREA M2'].values[0]
                    debris_mass = df_sub.loc[df_sub['DEBRIS NAME'].str.contains('TAB')]['MASS PER AREA KG/M2'].values[0]
        else:
            if 'COMP' in debris_name.upper():
                df_sub = df.loc[df['DEBRIS NAME'] == 'COMPOSITE SHINGLE']
            elif 'MOD METAL' in debris_name.upper() or 'MODULAR MT' in debris_name.upper():
                df_sub = df.loc[df['DEBRIS NAME'] == 'METAL ROOFING - ALUMINUM OR STEEL - PANEL']
            elif 'BUILT' in debris_name.upper() and 'GRAVEL' not in debris_name.upper():
                df_sub = df.loc[df['DEBRIS NAME'] =='BUILT-UP ROOF MEMBRANE 3-PLY SMOOTH-SURFACED']
            elif 'STAND' in debris_name.upper():
                df_sub = df.loc[df['DEBRIS NAME'] == 'STANDING SEAM METAL 0.032 IN. ALUMINUM PANEL WIDTH: 12 INCHES']
            elif 'TPO' in debris_name.upper():
                df_sub = df.loc[df['DEBRIS NAME'] == 'TPO ROOF MEMBRANE 60-MIL FULLY-ADHERED (MEMBRANE ONLY)']
            else:
                print('No debris mass or area information available for :' + debris_name)
                debris_area = None
                debris_mass = None
            if length_unit == 'ft':
                debris_area = df_sub['TYPICAL AREA FT2'].values[0]
                debris_mass = df_sub['MASS PER AREA LB/FT2'].values[0]
            else:
                debris_area = df_sub['TYPICAL AREA M2'].values[0]
                debris_mass = df_sub['MASS PER AREA KG/M2'].values[0]
    else:
        debris_area = None
        debris_mass = None
        print('No debris mass or area information available for :' + debris_name)
    return debris_area, debris_mass


def get_traj_params(debris_class):
    param_dict = {'c': None, 'c1': None, 'c2': None, 'c3': None, 'flight time': None}
    # Find flight time and coefficients for the debris class:
    if debris_class == 'sheet':
        param_dict['flight time'] = uniform(1, 1.5)  # This will be a uniform distribution
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


# # Testing the workflow:
# # Step 1: Generate Building data models for each building in a site:
# site = Site()
# df = pd.read_csv('C:/Users/Karen/PycharmProjects/DPBWE/BC_CParcels.csv')
# for row in range(0, len(df['Parcel Id'])):
#     new_bldg = Building()
#     pid, num_stories, occupancy = df['Parcel Id'][row], df['Stories'][row], df['Use Code'][row]
#     yr_built, address, area = df['Year Built'][row], df['Address'][row], df['Square Footage'][row]
#     lon, lat, length_unit = df['Longitude'][row], df['Latitude'][row], 'ft'
#     if 'PANAMA CITY BEACH' in address or 'MEXICO BEACH' in address:
#         pass
#     else:
#         new_bldg.add_parcel_data(pid, num_stories, occupancy, yr_built, address, area, lon, lat, length_unit, loc_flag=True)
#         # Add roof element and data:
#         new_roof = Roof()
#         new_roof.hasCover = df['Roof Cover'][row]
#         new_roof.hasType = df['Roof Cover'][row]
#         new_bldg.hasStory[-1].adjacentElement['Roof'] = [new_roof]
#         new_bldg.hasStory[-1].update_elements()
#         new_bldg.update_zones()
#         new_bldg.update_elements()
#         new_bldg.update_interfaces()
#         site.hasBuilding.append(new_bldg)
#         # Pull case study building:
#         if new_bldg.hasID == '13209-055-000':
#             bldg = new_bldg
#         else:
#             pass
# site.update_zones()
# site.update_elements()
# site.update_interfaces()
# # Step 2: Run through the debris workflow:
# wind_speed = np.arange(70, 200, 10)
# wind_direction = 0
# run_debris(bldg, site, length_unit, wind_direction, wind_speed)