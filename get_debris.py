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
    linestyle_list = ['-', '--', '8-', ':', '-.', '+-', '^-', 's-', '*-']
    color_list = ['c', 'g', 'saddlebrown', 'orange', 'm', 'b', 'blueviolet', 'darkgray', 'violet']
    df_linestyle = pd.DataFrame({'debris name': df['debris name'].unique(), 'linestyle': linestyle_list[0: len(df['debris name'].unique())],
                                 'color': color_list[0: len(df['debris name'].unique())]})
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
    # Find probable debris trajectories based on the given intensity:
    # Find exposure region for each debris type:
    along_traj_list = []
    across_traj_list = []  # For wind direction-specific queries
    debris_name = []
    for key in site.hasDebris:
        for d in site.hasDebris[key]['debris name']:
            debris_name.append(d)
            if wind_speed in df['wind speed'].unique():
                idx = df.loc[(df['debris name'] == d) & (df['wind speed'] == wind_speed)].index[0]
                along_traj_list.append(df.iloc[idx]['alongwind_mean'] + df.iloc[idx]['alongwind_std_dev'])
                across_traj_list.append(df.iloc[idx]['acrosswind_mean'] + df.iloc[idx]['acrosswind_std_dev'])
            else:
                # Interpolate the alongwind distance:
                # Find the wind speed's nearest multiple of five:
                nearest_five = 5 * round(wind_speed / 5)
                if nearest_five > wind_speed:
                    idx_upper = df.loc[(df['debris name'] == d) & (df['wind speed'] == nearest_five)].index[0]
                    idx_lower = df.loc[(df['debris name'] == d) & (df['wind speed'] == nearest_five-5)].index[0]
                    xi = np.array([nearest_five-5, nearest_five])
                    # Repeat for acrosswind:
                else:
                    idx_upper = df.loc[(df['debris name'] == d) & (df['wind speed'] == nearest_five + 5)].index[0]
                    idx_lower = df.loc[(df['debris name'] == d) & (df['wind speed'] == nearest_five)].index[0]
                    xi = np.array([nearest_five, nearest_five + 5])
                along_yi = np.array([df.iloc[idx_lower]['alongwind_mean'] + df.iloc[idx_lower]['alongwind_std_dev'],
                               df.iloc[idx_upper]['alongwind_mean'] + df.iloc[idx_upper]['alongwind_std_dev']])
                # Repeat for acrosswind:
                across_yi = np.array([df.iloc[idx_lower]['acrosswind_mean'] + df.iloc[idx_lower]['acrosswind_std_dev'],
                               df.iloc[idx_upper]['acrosswind_mean'] + df.iloc[idx_upper]['acrosswind_std_dev']])
                along_f = interp1d(xi, along_yi)
                along_traj_list.append(along_f(wind_speed))
                # Acrosswind:
                across_f = interp1d(xi, across_yi)
                across_traj_list.append(across_f(wind_speed))
    if crs == 'reference cartesian':
        # Plot the target building's footprint:
        xt, yt = bldg.hasGeometry['Footprint']['local'].exterior.xy
        ax.plot(np.array(xt)/div, np.array(yt)/div, 'r')
        # Use the reference building's footprint as origin:
        origin = bldg.hasGeometry['Footprint']['local'].centroid
        # Collect debris regions:
        debris_region = []
        for i in range(0, len(along_traj_list)):
            if along_traj_list[i] != 0:
                buffer_poly = origin.buffer(along_traj_list[i])
                debris_region.append(buffer_poly)
                xb, yb = buffer_poly.exterior.xy
            else:
                debris_region.append(None)
            idx_ltype = df_linestyle.loc[df_linestyle['debris name']==debris_name[i], 'linestyle'].index[0]
            ax.plot(np.array(xb)/div, np.array(yb)/div, df_linestyle['linestyle'][idx_ltype], label=debris_name[i], color=df_linestyle['color'][idx_ltype])
        ax.set_xlabel('x [m]')
        ax.set_ylabel('y [m]')
        plt.legend(fontsize=14)
        plt.show()
    # Add debris data to site's data model:
    site.hasDebris['roof cover']['debris region'] = debris_region
    site.hasDebris['roof cover']['alongwind_dist'] = along_traj_list
    site.hasDebris['roof cover']['acrosswind_dist'] = across_traj_list
    df_region = site.hasDebris['roof cover']
    # Find source buildings:
    fig2, ax2 = plt.subplots()
    bldg_list = []
    for b in site.hasBuilding:
        # Find the debris region based on the bldg's debris type:
        idx_region = df_region.loc[df_region['debris name']==b.hasElement['Roof'][0].hasType].index[0]
        if df_region['debris region'][idx_region] is None:
            pass
        else:
            # Find query geometry:
            if crs == 'reference cartesian':
                bldg_geometry = b.hasGeometry['Footprint'][crs]
            else:
                pass
            # Check if the bldg is within or intersects the debris type's region:
            if bldg_geometry.within(df_region['debris region'][idx_region]) or bldg_geometry.intersects(df_region['debris region'][idx_region]):
                bldg_list.append(b)
                xs, ys = bldg_geometry.exterior.xy
                ax2.plot(np.array(xs)/div, np.array(ys)/div, 'k')
                print(b.hasLocation['Address'] + '   ' + b.hasElement['Roof'][0].hasType)
            else:
                pass
    # Plot debris regions and target building footprint:
    ax2.plot(np.array(xt) / div, np.array(yt) / div, 'r')
    for region in df_region['debris region'].index.to_list():
        if df_region['debris region'][region] is None:
            pass
        else:
            idx_ltype = df_linestyle.loc[df_linestyle['debris name'] == df_region['debris name'][region], 'linestyle'].index[0]
            xregion, yregion = df_region['debris region'][region].exterior.xy
            ax2.plot(np.array(xregion)/div, np.array(yregion)/div, df_linestyle['linestyle'][idx_ltype], label=df_region['debris name'][region], color=df_linestyle['color'][idx_ltype])
    if div != 1:
        ax2.set_xlabel('x [m]')
        ax2.set_ylabel('y [m]')
    else:
        ax2.set_xlabel('x [ft]')
        ax2.set_ylabel('y [ft]')
    plt.legend(fontsize=14)
    plt.show()
    # Create site object and add source buildings based on wind intensity (and wind direction)
    site_source = Site()
    if wind_direction is None:
        site_source.hasBuilding = bldg_list
    else:
        # Filter the identified buildings by wind direction:
        fig3, ax3 = plt.subplots()
        # Step 1: Find the maximum probable alongwind distance in region (mean + std_dev):
        max_dist = max(along_traj_list) + 5
        # Step 2: Find the upwind debris region:
        new_pt1 = Point(origin.x + max_dist, origin.y)
        new_pt2 = Point(origin.x - max_dist, origin.y)
        iline = LineString([new_pt1, new_pt2])
        # Rotate line according to wind direction to separate up/downwind regions:
        iline = rotate(iline, -1 * wind_direction + 180)
        dir_region_list = []
        for j in range(0, len(df_region['debris name'])):
            if df_region['debris region'][j] is None:
                dir_region_list.append(None)
            else:
                # Split the circle using the intersecting line:
                spolys = split(df_region['debris region'][j], iline)
                # Grab the half corresponding to the upwind region:
                if 0 < wind_direction < 180:
                    if spolys[0].centroid.x > origin.x:
                        upwind_region = spolys[0]
                    else:
                        upwind_region = spolys[1]
                elif 180 < wind_direction < 360:
                    if spolys[0].centroid.x < origin.x:
                        upwind_region = spolys[0]
                    else:
                        upwind_region = spolys[1]
                elif wind_direction == 0:
                    if spolys[0].centroid.y > origin.y:
                        upwind_region = spolys[0]
                    else:
                        upwind_region = spolys[1]
                elif wind_direction == 180:
                    if spolys[0].centroid.y < origin.y:
                        upwind_region = spolys[0]
                    else:
                        upwind_region = spolys[1]
                # Step 3: Using the acrosswind distance, create a rectangle to find width of upwind region:
                new_rpt1 = Point(origin.x - df_region['acrosswind_dist'][j], origin.y)
                new_rpt2 = Point(origin.x + df_region['acrosswind_dist'][j], origin.y)
                new_rpt3 = Point(origin.x + df_region['acrosswind_dist'][j], origin.y + df_region['alongwind_dist'][j])
                new_rpt4 = Point(origin.x - df_region['acrosswind_dist'][j], origin.y + df_region['alongwind_dist'][j])
                new_rect = Polygon([new_rpt1, new_rpt2, new_rpt3, new_rpt4])
                # Rotate the rectangle:
                new_rect = rotate(new_rect, -1*wind_direction, origin=origin)
                # Now find the debris region:
                dir_debris_region = new_rect.intersection(upwind_region)
                dir_region_list.append(dir_debris_region)
        df_region['directional debris region'] = dir_region_list
        # Loop through intensity-derived source buildings to find directional source buildings:
        dir_bldg_list = []
        for k in bldg_list:
            if crs == 'reference cartesian':
                bldg_geometry = k.hasGeometry['Footprint'][crs]
            else:
                pass
            # Find the index for the debris type:
            idx_region = df_region.loc[df_region['debris name'] == k.hasElement['Roof'][0].hasType].index[0]
            if df_region['directional debris region'][idx_region] is None:
                pass
            else:
                if bldg_geometry.within(df_region['directional debris region'][idx_region]) or bldg_geometry.intersects(df_region['directional debris region'][idx_region]):
                    dir_bldg_list.append(k)
                    xk, yk = bldg_geometry.exterior.xy
                    ax3.plot(np.array(xk)/div, np.array(yk)/div, 'k')
                else:
                    pass
        # Add queried buildings to site_source:
        site_source.hasBuilding = dir_bldg_list
        # Plot directional debris regions:
        for r in df_region['directional debris region'].index.to_list():
            if df_region['directional debris region'][r] is None:
                pass
            else:
                idx_ltype = df_linestyle.loc[df_linestyle['debris name'] == df_region['debris name'][r], 'linestyle'].index[0]
                xrdir, yrdir = df_region['directional debris region'][r].exterior.xy
                ax3.plot(np.array(xrdir)/div, np.array(yrdir)/div, df_linestyle['linestyle'][idx_ltype], label=df_region['debris name'][r], color=df_linestyle['color'][idx_ltype])
        if div != 1:
            ax3.set_xlabel('x [m]')
            ax3.set_ylabel('y [m]')
        else:
            ax3.set_xlabel('x [ft]')
            ax3.set_ylabel('y [ft]')
        # Plot the target building's footprint:
        ax3.plot(np.array(xt) / div, np.array(yt) / div, 'r')
        ax3.set_xticks([-100, -50, 0, 50, 100])
        ax3.set_yticks([-100, -50, 0, 50, 100, 150])
        plt.legend(fontsize=14)
        plt.show()
    # Update site_source elements and zones:
    site_source.update_elements()
    site_source.update_zones()
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
                df_sub = df.loc[df['DEBRIS NAME'] == 'STANDING SEAM METAL 24-GAUGE STEEL PANEL WIDTH: 12 INCHES']
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