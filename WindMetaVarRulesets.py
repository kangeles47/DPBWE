from math import sqrt

def get_meta_var(BIM):
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
    BIM['WBD'] = WBD
    # Terrain
    # open (0.03) = 3
    # light suburban (0.15) = 15
    # suburban (0.35) = 35
    # light trees (0.70) = 70
    # trees (1.00) = 100
    # Mapped to Land Use Categories in NJ (see https://www.state.nj.us/dep/gis/
    # digidownload/metadata/lulc02/anderson2002.html) by T. Wu group
    # (see internal report on roughness calculations, Table 4).
    # These are mapped to Hazus defintions as follows:
    # Open Water (5400s) with zo=0.01 and barren land (7600) with zo=0.04 assume Open
    # Open Space Developed, Low Intensity Developed, Medium Intensity Developed
    # (1110-1140) assumed zo=0.35-0.4 assume Suburban
    # High Intensity Developed (1600) with zo=0.6 assume Lt. Tree
    # Forests of all classes (4100-4300) assumed zo=0.6 assume Lt. Tree
    # Shrub (4400) with zo=0.06 assume Open
    # Grasslands, pastures and agricultural areas (2000 series) with
    # zo=0.1-0.15 assume Lt. Suburban
    # Woody Wetlands (6250) with zo=0.3 assume suburban
    # Emergent Herbaceous Wetlands (6240) with zo=0.03 assume Open
    # Note: HAZUS category of trees (1.00) does not apply to any LU/LC in NJ
    terrain = 15 # Default in Reorganized Rulesets - WIND
    if (BIM['z0'] > 0):
        terrain = int(100 * BIM['z0'])
    elif (BIM['lulc'] > 0):
        if (BIM['flood_zone'].startswith('V') or BIM['flood_zone'] in ['A', 'AE', 'A1-30', 'AR', 'A99']):
            terrain = 3
        elif ((BIM['lulc'] >= 5000) and (BIM['lulc'] <= 5999)):
            terrain = 3 # Open
        elif ((BIM['lulc'] == 4400) or (BIM['lulc'] == 6240)) or (BIM['lulc'] == 7600):
            terrain = 3 # Open
        elif ((BIM['lulc'] >= 2000) and (BIM['lulc'] <= 2999)):
            terrain = 15 # Light suburban
        elif ((BIM['lulc'] >= 1110) and (BIM['lulc'] <= 1140)) or ((BIM['lulc'] >= 6250) and (BIM['lulc'] <= 6252)):
            terrain = 35 # Suburban
        elif ((BIM['lulc'] >= 4100) and (BIM['lulc'] <= 4300)) or (BIM['lulc'] == 1600):
            terrain = 70 # light trees
    elif (BIM['Terrain'] > 0):
        if (BIM['flood_zone'].startswith('V') or BIM['flood_zone'] in ['A', 'AE', 'A1-30', 'AR', 'A99']):
            terrain = 3
        elif ((BIM['Terrain'] >= 50) and (BIM['Terrain'] <= 59)):
            terrain = 3 # Open
        elif ((BIM['Terrain'] == 44) or (BIM['Terrain'] == 62)) or (BIM['Terrain'] == 76):
            terrain = 3 # Open
        elif ((BIM['Terrain'] >= 20) and (BIM['Terrain'] <= 29)):
            terrain = 15 # Light suburban
        elif (BIM['Terrain'] == 11) or (BIM['Terrain'] == 61):
            terrain = 35 # Suburban
        elif ((BIM['Terrain'] >= 41) and (BIM['Terrain'] <= 43)) or (BIM['Terrain'] in [16, 17]):
            terrain = 70 # light trees
