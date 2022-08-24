import numpy as np
from math import sqrt


def parse_BIM(BIM_in):
    """
    Parses the information provided in the BIM model.
    The parameters below list the expected inputs
    Parameters
    ----------
    stories: str
        Number of stories
    yearBuilt: str
        Year of construction.
    roofType: {'hip', 'hipped', 'gabled', 'gable', 'flat'}
        One of the listed roof shapes that best describes the building.
    occupancy: str
        Occupancy type.
    buildingDescription: str
        MODIV code that provides additional details about the building
    structType: {'Stucco', 'Frame', 'Stone', 'Brick'}
        One of the listed structure types that best describes the building.
    V_design: string
        Ultimate Design Wind Speed was introduced in the 2012 IBC. Officially
        called “Ultimate Design Wind Speed (Vult); equivalent to the design
        wind speeds taken from hazard maps in ASCE 7 or ATC's API. Unit is
        assumed to be mph.
    area: float
        Plan area in ft2.
    z0: string
        Roughness length that characterizes the surroundings.
    Returns
    -------
    BIM: dictionary
        Parsed building characteristics.
    """

    # maps roof type to the internal representation
    ap_RoofType = {
        'hip': 'hip',
        'hipped': 'hip',
        'Hip': 'hip',
        'gabled': 'gab',
        'gable': 'gab',
        'Gable': 'gab',
        'flat': 'flt',
        'Flat': 'flt'
    }
    # maps roof system to the internal representation
    ap_RoofSyste = {
        'Wood': 'trs',
        'OWSJ': 'ows',
        'N/A': 'trs'
    }
    roof_system = BIM_in.get('RoofSystem', 'Wood')
    try:
        if np.isnan(roof_system):
            roof_system = 'Wood'
    except:
        pass
    # maps number of units to the internal representation
    ap_NoUnits = {
        'Single': 'sgl',
        'Multiple': 'mlt',
        'Multi': 'mlt',
        'nav': 'nav'
    }
    # maps for split level
    ap_SplitLevel = {
        'NO': 0,
        'YES': 1
    }
    # maps for design level (Marginal Engineered is mapped to Engineered as default)
    ap_DesignLevel = {
        'E': 'E',
        'NE': 'NE',
        'PE': 'PE',
        'ME': 'E'
    }
    design_level = BIM_in.get('DesignLevel', 'E')
    try:
        if np.isnan(design_level):
            design_level = 'E'
    except:
        pass

    foundation = BIM_in.get('FoundationType', 3501)
    if np.isnan(foundation):
        foundation = 3501

    nunits = BIM_in.get('NoUnits', 1)
    if np.isnan(nunits):
        nunits = 1

    # Average January Temp.
    ap_ajt = {
        'Above': 'above',
        'Below': 'below'
    }

    # Year built
    alname_yearbuilt = ['yearBuilt', 'YearBuiltMODIV', 'YearBuilt']
    yearbuilt = 1985
    try:
        yearbuilt = BIM_in['YearBuiltNJDEP']
    except:
        for i in alname_yearbuilt:
            if i in BIM_in.keys():
                yearbuilt = BIM_in[i]
                break
    print('yearbuilt = ', yearbuilt)

    # Number of Stories
    alname_nstories = ['stories', 'NumberofStories0', 'NumberofStories', 'NumberOfStories']
    try:
        nstories = BIM_in['NumberofStories1']
    except:
        for i in alname_nstories:
            if i in BIM_in.keys():
                nstories = BIM_in[i]
                break
    print('nstories = ', nstories)

    # Plan Area
    alname_area = ['area', 'PlanArea1', 'Area']
    try:
        area = BIM_in['PlanArea0']
    except:
        for i in alname_area:
            if i in BIM_in.keys():
                area = BIM_in[i]
                break

    # Design Wind Speed
    alname_dws = ['DSWII', 'DWSII', 'DesignWindSpeed']
    try:
        dws = BIM_in['DSWII']
    except:
        for alname in alname_dws:
            if alname in BIM_in.keys():
                dws = BIM_in[alname]
                break

    # if getting RES3 then converting it to default RES3A
    alname_occupancy = ['OccupancyClass']
    try:
        oc = BIM_in['occupancy']
        if math.isnan(oc):
            for i in alname_occupancy:
                if i in BIM_in.keys():
                    oc = BIM_in[i]
                    break
    except:
        for i in alname_occupancy:
            if i in BIM_in.keys():
                oc = BIM_in[i]
                break
    if oc == 'RES3':
        oc = 'RES3A'

    # maps for flood zone
    ap_FloodZone = {
        # Coastal areas with a 1% or greater chance of flooding and an
        # additional hazard associated with storm waves.
        6101: 'VE',
        6102: 'VE',
        6103: 'AE',
        6104: 'AE',
        6105: 'AO',
        6106: 'AE',
        6107: 'AH',
        6108: 'AO',
        6109: 'A',
        6110: 'X',
        6111: 'X',
        6112: 'X',
        6113: 'OW',
        6114: 'D',
        6115: 'NA',
        6119: 'NA'
    }
    if type(BIM_in['FloodZone']) == int:
        # NJDEP code for flood zone (conversion to the FEMA designations)
        floodzone_fema = ap_FloodZone[BIM_in['FloodZone']]
    else:
        # standard input should follow the FEMA flood zone designations
        floodzone_fema = BIM_in['FloodZone']

    # maps for BuildingType
    ap_BuildingType = {
        # Coastal areas with a 1% or greater chance of flooding and an
        # additional hazard associated with storm waves.
        'Wood': 3001,
        'Steel': 3002,
        'Concrete': 3003,
        'Masonry': 3004,
        'Manufactured': 3005
    }
    if type(BIM_in['FloodZone']) == str:
        # NJDEP code for flood zone (conversion to the FEMA designations)
        buildingtype = ap_BuildingType[BIM_in['BuildingType']]
    else:
        # standard input should follow the FEMA flood zone designations
        buildingtype = BIM_in['BuildingType']

    # first, pull in the provided data
    BIM = dict(
        occupancy_class=str(oc),
        bldg_type=int(buildingtype),
        year_built=int(yearbuilt),
        # double check with Tracey for format - (NumberStories0 is 4-digit code)
        # (NumberStories1 is image-processed story number)
        stories=int(nstories),
        area=float(area),
        flood_zone=floodzone_fema,
        V_ult=float(dws),
        avg_jan_temp=ap_ajt[BIM_in.get('AvgJanTemp', 'Below')],
        roof_shape=ap_RoofType[BIM_in['RoofShape']],
        roof_slope=float(BIM_in.get('RoofSlope', 0.25)),  # default 0.25
        sheathing_t=float(BIM_in.get('SheathingThick', 1.0)),  # default 1.0
        roof_system=str(ap_RoofSyste[roof_system]),  # only valid for masonry structures
        garage_tag=float(BIM_in.get('Garage', -1.0)),
        lulc=BIM_in.get('LULC', -1),
        z0=float(BIM_in.get('z0', -1)),  # if the z0 is already in the input file
        Terrain=BIM_in.get('Terrain', -1),
        mean_roof_height=float(BIM_in.get('MeanRoofHt', 15.0)),  # default 15
        design_level=str(ap_DesignLevel[design_level]),  # default engineered
        no_units=int(nunits),
        window_area=float(BIM_in.get('WindowArea', 0.20)),
        first_floor_ht1=float(BIM_in.get('FirstFloorHt1', 10.0)),
        split_level=bool(ap_SplitLevel[BIM_in.get('SplitLevel', 'NO')]),  # dfault: no
        fdtn_type=int(foundation),  # default: pile
        city=BIM_in.get('City', 'NA'),
        wind_zone=str(BIM_in.get('WindZone', 'I'))
    )

    # add inferred, generic meta-variables
    # My stuff starts here:
    # Hurricane-Prone Region (HRP)
    # Areas vulnerable to hurricane, defined as the U.S. Atlantic Ocean and
    # Gulf of Mexico coasts where the ultimate design wind speed, V_ult is
    # greater than a pre-defined limit.
    if BIM['year_built'] > 2010:
        # The limit is 115 mph (ultimate wind speed, V_ult) in 2010-2017 FBC (see Section 1609.2)
        HPR = BIM['V_ult'] > 115.0
    else:
        # The limit is 90 mph (basic wind speed, V_asd) in 2001-2009 FBC
        # Conversion: V_asd = V_ult*sqrt(0.6)
        HPR = BIM['V_ult'] > 90.0/sqrt(0.6)
    BIM['hpr'] = HPR

    # High-velocity hurricane zone (HVHZ):
    # Chapter 2 in 2001-2017 FBC defines HVHZ zone as Broward and Dade Counties. Note that before the FBC, these counties adhered to the South Florida Building Code (SFBC)
    if 'BROWARD' in BIM['county'].upper() or 'DADE' in BIM['county'].upper():
        BIM['hvhz'] = True
    else:
        BIM['hvhz'] = False

    # Wind Borne Debris
    # (Section 202 - FBC 2017 and 2014, Section 1609.2 - FBC 2010)
    # Areas within hurricane-prone regions are affected by debris if one of
    # the following two conditions holds:
    # (1) Within 1 mile (1.61 km) of the coastal mean high water line where
    # the ultimate design wind speed is 130 mph or greater. (flood_lim)
    # (2) In areas where the ultimate design wind speed is greater than 140 mph (general_lim)
    # The flood_lim and general_lim limits depend on the year of construction
    panhandle_flag = False  # variable to enact Panhandle WBD exemption
    panhandle_counties = ['GULF', 'BAY', 'WALTON', 'OKALOOSA', 'SANTA ROSA', 'ESCAMBIA']
    if BIM['year_built'] > 2010:
        # In 2010 FBC - present:
        flood_lim = 130.0 # mph
        general_lim = 140.0 # mph
    elif BIM['year_built'] <= 2010:
        # Section 1609.2 - FBC 2007
        # Areas within hurricane-prone regions located in accordance with one of the following:
        # (1) Within 1 mile (1.61 km) of the coastal mean high water line where the basic wind speed, Vasd, is 110 mph (48m/s) or greater.
        # (2) In areas where the basic wind speed is 120 mph (53 m/s) or greater.
        # Conversion: V_asd = V_ult*sqrt(0.6)
        flood_lim = 110/sqrt(0.6) # mph
        general_lim = 120.0/sqrt(0.6) # mph
        if BIM['year_built'] <= 2007:
            # Check for Panhandle exemption: Section 1609.2 - FBC 2004, Section 1606.1.5 - FBC 2001
            # Areas within hurricane-prone regions located in accordance with one of the following:
            # (1) Within 1 mile (1.61 km) of the coastal mean high water line where the basic wind speed, Vasd, is 110 mph (48m/s) or greater.
            # (2) Areas where the basic wind speed is 120 mph (53 m/s) or greater except from the eastern border of Franklin County to the Florida-Alabama line where the region includes areas only 1 mile of the coast.
            if any(county in BIM['county'].upper() for county in panhandle_counties):
                panhandle_flag = True
            else:
                pass
        else:
            pass
    # Determine if in WBD region:
    if not HPR:
        WBD = False
    else:
        # Applicable flood zones for the Bay County include the following: A, AE, AH, AO, VE
        # Bay County, FL FEMA Flood Zones can easily be viewed at:
        # https://www.baycountyfl.gov/508/FEMA-Flood-Zones
        WBD = (((BIM['flood_zone'].startswith('A') or BIM['flood_zone'].startswith('V')) and
                BIM['V_ult'] >= flood_lim) or (BIM['V_ult'] >= general_lim and not panhandle_flag))
        # Note: here if first criteria is met, this enforces 1-mi boundary for panhandle exemption.
        # In the future, it would be better to have an actually polygon or line that creates a boundary to easily query
    BIM['WBD'] = WBD
    # Terrain
    # open (0.03) = 3
    # light suburban (0.15) = 15
    # suburban (0.35) = 35
    # light trees (0.70) = 70
    # trees (1.00) = 100
    # For purposes of case study, set default to light suburban (0.15).
    # In the future, robust rulests can be formalized by consulting LULC categories for FL
    # https://geodata.dep.state.fl.us/datasets/FDEP::statewide-land-use-land-cover/about
    # Note that, for coastal cities, it may be more appropriate to designate open terrain conditions:
    coastal_cities_fl = ['MEXICO BEACH', 'PANAMA CITY BEACH']
    if BIM['lulc'] == 1400:  # Commercial and services
        terrain = 35  # suburban
    elif BIM['lulc'] == 1330:  # High density, multiple dwelling units, low rise
        terrain = 35
    elif BIM['lulc'] == 1210 or BIM['lulc'] == 1740:  # Medium density, fixed single family units or medical/health care
        terrain = 15  # light suburban
    else:
        # Check for coastal cities:
        if any(city == BIM['city'].upper() for city in coastal_cities_fl):
            terrain = 3
        else:
            # Assume light, suburban terrain:
            terrain = 15  # Default value
    BIM['terrain'] = terrain

    return BIM
