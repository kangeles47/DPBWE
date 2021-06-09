from pandas import read_csv
# Create decision trees to characterize missile environment and consequent debris trajectories
    # Might want to include here consideration of roof assembly condition (age)
    # Typical debris types: roof covers, roof sheathing, frame/joist elements (e.g., timber)
# Develop rulesets for site-specific debris classification for range of common typologies
# Map debris classes to appropriate trajectory models
# Develop decision trees to extract relevant component data from manufacturer's specifications to refine site-specific debris models
# Implement similitude parameters to project source building damage
def get_source_bldgs(bldg, site):
    """

    :param bldg: A Building object with roof information and local wind speed values
    :param site: A Site object with Building objects as described above (Site.hasBuilding)
    :return:
    """
    debris_type = {'roof cover': [], 'roof sheathing': [], 'roof member': []}  # 3 most common debris types
    struct_type = ['WOOD', 'JOIST', 'OWSJ', 'TRUSS']  # global list of structural types with frame members
    for i in site.hasBuilding:
        # Extract roof information for each building in the Site description:
        # Roof Cover
        if i.adjacentElement['Roof'][0].hasCover not in debris_type['roof cover'] and (i.adjacentElement['Roof'][0].hasCover is not None):
            debris_type['roof cover'].append(i.adjacentElement['Roof'][0].hasCover)
        # Roof Sheathing
        if i.adjacentElement['Roof'][0].hasSheathing not in debris_type['roof sheathing'] and (i.adjacentElement['Roof'][0].hasSheathing is not None):
            debris_type['roof sheathing'].append(i.adjacentElement['Roof'][0].hasSheathing)
        # Roof Structure
        if any([stype in i.adjacentElement['Roof'][0].hasStructureType.upper() for stype in struct_type]) and (i.adjacentElement['Roof'][0].hasStructureType is not None):
            debris_type['roof member'].append(i.adjacentElement['Roof'][0].hasStructureType)
        else:
            pass
    # Get the trajectory for each debris type:
    for key in debris_type:
        bldg.adjacentElement['Roof'][0].hasDebrisTrajectory = get_trajectory(bldg)


def get_trajectory(bldg):
    traj_dict = {'roof cover': [], 'roof sheathing': [], 'roof member': []}  # Dict w/ 3 most common debris types
    # Set up global parameter values:
    if bldg.hasGeometry['Length Unit'] == 'm':
        air_density = 1.225  # kg/m^3
        gravity = 9.81  # m/s^2
    elif bldg.hasGeometry['Length Unit'] == 'ft':
        air_density = 0.0765  # lb/ft^3
        gravity = 32.2  # ft/s^2
    # Calculate the trajectory for this building's available debris types:
    if bldg.adjacentElement['Roof'][0].hasCover is None:
        traj_dict['roof cover'].append(None)
    if bldg.adjacentElement['Roof'][0].hasSheathing is None:
        traj_dict['roof sheathing'].append(None)
    if bldg.adjacentElement['Roof'][0].hasStructureType is None:
        traj_dict['roof member'].append(None)
    for key in traj_dict:
        if len(traj_dict[key]) > 0:
            pass
        else:
            # Find the debris class each debris type belongs to:
            debris_class = get_debris_class(key, bldg)
            if debris_class is None:
                traj_dict[key].append(None)  # Exception case for structural typ. flat roofs
            else:
                # Find the debris mass:
                debris_mass = get_debris_mass(bldg, debris_class)
                # Get additional trajectory parameters:
                param_dict = get_traj_params(debris_class)
                # Calculate Tachikawa number:
                tachikawa_num = air_density*(bldg.adjacentElement['Roof'][0].hasDemand['wind speed']**2)/(2*debris_mass*gravity)
                # Calculate mean of alongwind distance:
                alongwind_dist = (2*debris_mass/air_density)*((0.5*c*(tachikawa_num*flight_time)**2) + (c1*(tachikawa_num*flight_time)**3) + (c2*(tachikawa_num*flight_time)**4) + (c3*(tachikawa_num*flight_time)**5))
                # Initialize remaining distribution parameters:
                acrosswind_dist = 0
                sigma_along = 0.35*alongwind_dist
                sigma_across = 0.35*alongwind_dist
    return alongwind_dist, acrosswind_dist, sigma_along, sigma_across, tachikawa_num, c, gravity


def get_debris_class(debris_type, bldg):
    # Three debris classes to choose from: sheet/plate, compact, and rod-like:
    # Define global types:
    sheet_type = ['TILE', 'SHINGLE', 'SLATE', 'BUR', 'BUILT-UP', 'SHAKE', 'PLY', 'SPM', 'POLY', 'METAL']
    rod_type = ['WOOD', 'JOIST', 'OWSJ', 'TRUSS']  # global list of structural types with frame members
    if debris_type == 'roof cover':
        if 'GRAVEL' in bldg.adjacentElement['Roof'][0].hasCover.upper():
            debris_class = 'compact'
        elif any([stype in bldg.adjacentElement['Roof'][0].hasStructureType.upper() for stype in sheet_type]):
            debris_class = 'sheet'
    elif debris_type == 'roof sheathing':
        debris_class = 'sheet'
    elif debris_type == 'roof member':
        if any([rtype in bldg.adjacentElement['Roof'][0].hasStructureType.upper() for rtype in rod_type]):
            debris_class = 'rod'
        else:
            debris_class = None
    return debris_class


def get_debris_mass(bldg, debris_class):
    # Load debris mass data (in the future, extend to regional manufacturers):
    df = read_csv('D:/Users/Karen/Documents/Github/DPWBE/Datasets/Debris/Typical_Debris_Masses.csv')
    if debris_class == 'roof cover':
        if 'ASPHALT' in bldg.adjacentElement['Roof'][0].hasCover.upper():
            df_sub = df['DEBRIS NAME'].str.contains('ASPHALT')
            # Search for any special cases:
            scase = ['ARCH', 'LAM', 'DIM']
            if any([case in bldg.adjacentElement['Roof'][0].hasCover.upper() for case in scase]):
                if bldg.hasGeometry['Length Unit'] == 'ft':
                    debris_area = df_sub['DEBRIS NAME'].str.contains('ARCH')['TYPICAL AREA FT2']
                    debris_mass = df_sub['DEBRIS NAME'].str.contains('ARCH')['MASS PER AREA LB/FT2']
                else:
                    debris_area = df_sub['DEBRIS NAME'].str.contains('ARCH')['TYPICAL AREA M2']
                    debris_mass = df_sub['DEBRIS NAME'].str.contains('ARCH')['MASS PER AREA KG/M2']
            else:
                if bldg.hasGeometry['Length Unit'] == 'ft':
                    debris_area = df_sub['DEBRIS NAME'].str.contains('TAB')['TYPICAL AREA FT2']
                    debris_mass = df_sub['DEBRIS NAME'].str.contains('TAB')['MASS PER AREA LB/FT2']
                else:
                    debris_area = df_sub['DEBRIS NAME'].str.contains('TAB')['TYPICAL AREA M2']
                    debris_mass = df_sub['DEBRIS NAME'].str.contains('TAB')['MASS PER AREA KG/M2']
    else:
        pass
    return debris_area, debris_mass


def get_traj_params(debris_class):
    param_dict = {'C': None, 'c1': None, 'c2': None, 'c3': None}
    # Find flight time and coefficients for the debris class:
    if debris_class == 'sheet':
        from scipy.stats import uniform
        flight_time = uniform(1, 2.5)  # This will be a uniform distribution
        param_dict['C'] = 0.91
        param_dict['c1'] = -0.148
        param_dict['c2'] = 0.024
        param_dict['c3'] = -0.0014
    elif debris_class == 'rod':
        c = 0.801
    elif debris_class == 'compact':
        pass
    return param_dict

def calc_impact_momentum(debris_mass, debris_area, horiz_impact_vel):
    return debris_mass* debris_area* horiz_impact_vel


def get_horiz_impact_vel(wind_speed, c, tachikawa_num, gravity, horiz_fdist):
    from math import exp, sqrt
    x = gravity*horiz_fdist/(wind_speed**2)
    horiz_impact_vel = wind_speed*(1-exp(-1*sqrt(2*c*tachikawa_num*x)))
    return horiz_impact_vel
