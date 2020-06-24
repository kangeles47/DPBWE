import numpy as np
import pandas as pd
from code_pressures import PressureCalc

# Goal of this code is to extract the information necessary to assign the correct pressure to building components
# General sequence:
# (1) Provide a building model:
# (2) Conduct an inventory of its components:
# (3) Given those components and the building model:
#   a) Access the correct reference pressures
#   b) Conduct the necessary similitude mappings
#   c) Assign pressures for each zone to the appropriate locations for the building model
def get_roof_uplift_pressure(edition, h_bldg, length, exposure, wind_speed, direction, pitch):
    # Step 1: Determine the use case:
    ratio = h_bldg/length
    if edition == 'ASCE 7-88' or edition == 'ASCE 7-93':
        if direction == 'parallel':
            if ratio <= 2.5:
                use_case = 3
            elif ratio > 2.5:
                use_case  = 4
        elif direction == 'normal':
            pass
    else:
        if direction == 'parallel' or (direction == 'normal' and pitch < 10):
            if ratio <= 0.5:
                use_case = 1
            elif ratio >= 1.0:
                use_case = 2
        elif direction == 'normal' and pitch >= 10:
            pass
    # Step 2: Determine which "family" of building codes will be needed (if necessary):
    if edition == 'ASCE 7-02' or edition == 'ASCE 7-05':
        edition = 'ASCE 7-98'
    elif edition == 'ASCE 7-88':
        edition = 'ASCE 7-93'
    # Step 3: Extract the respective reference pressure for the use case:
    file_path = 'D:/Users/Karen/Documents/Github/DPBWE/Similitude Parameters/Roof_MWFRS/Roof_MWFRS_'
    if use_case == 1:
        pref = pd.read_csv(file_path + 'ref1.csv', index_col='Edition').loc[[edition], :]
    elif use_case == 2:
        pref = pd.read_csv(file_path + 'ref2.csv', index_col='Edition').loc[[edition], :]
    elif use_case == 3:
        pref = pd.read_csv(file_path + 'ref3.csv', index_col='Edition').loc[[edition], :]
    elif use_case == 4:
        pref = pd.read_csv(file_path + 'ref4.csv', index_col='Edition').loc[[edition], :]
    # Step 4: Filter out any zones that are not needed for use cases 1 and 2:
    if use_case == 1 and ratio == 0.5:
        pref = pref[pref.columns[0:3]]  # Case with only 3 zones
    elif use_case == 2 and ratio == 2.0:
        pref = pref[pref.columns[0:1]] # Case with only 1 zone
    # Similitude parameters require comparison to a reference building: Note: not technically needed as long as we know what the correct reference building is
    pressures = PressureCalc()
    ref_exposure, ref_hstory, ref_hbldg, ref_pitch, ref_speed, ref_cat, hpr, h_ocean, encl_class = pressures.ref_bldg()
    # Step 5: Extract similitude parameters for wind speed, height, and exposure
    # Similitude in wind speed:
    if wind_speed == ref_speed:
        vfactor = 0.0
    else:
        if edition == 'ASCE 7-93':
            vfactor = pd.read_csv(file_path + 'v3.csv', index_col='Edition')[str(wind_speed)][edition]
        else:
            vfactor = pd.read_csv(file_path + 'v1.csv', index_col='Edition')[str(wind_speed)][edition] # Leave here for now, for regional simulation will probably want to load everything somewhere outside
    # Similitude in height:
    if h_bldg == ref_hbldg:
        hfactor = 0.0
    else:
        if edition == 'ASCE 7-93':
            hfactor = pd.read_csv(file_path + 'h_93.csv')[str(h_bldg) + ' ft'][0]
        else:
            hfactor = pd.read_csv(file_path + 'h.csv')[str(h_bldg) + ' ft'][0]
    # Similitude in exposure categories:
    if exposure == ref_exposure:
        efactor = 0.0
    else:
        efactor = pd.read_csv(file_path + 'exp_' + edition[-2:] + '.csv', index_col='Height in ft')[exposure][h_bldg]
    # Step 6: Apply the similitude parameters to get the final pressures for each zone:
    factor_lst = [vfactor, hfactor, efactor]
    psim = pref.loc[edition]
    for factor in factor_lst:
        psim = factor*psim + psim
    return psim

def get_wcc_pressure(edition, h_bldg, h_story, ctype, exposure, wind_speed, pitch):
    # Step 1: Determine which "family" of building codes will be needed (if necessary):
    if edition == 'ASCE 7-02' or edition == 'ASCE 7-05':
        edition = 'ASCE 7-98'
    elif edition == 'ASCE 7-88':
        edition = 'ASCE 7-93'
    # Step 2: Access the appropriate reference building and determine the file path:
    pressures = PressureCalc()
    if h_story == 9 and pitch <= 10:  #[ft]
        ref_exposure, ref_hstory, ref_hbldg, ref_pitch, ref_speed, ref_cat, hpr, h_ocean, encl_class = pressures.ref_bldg()
        file_path = 'D:/Users/Karen/Documents/Github/DPBWE/Similitude Parameters/Wall_CC/RBLDG1/'
    else:
        pass
    # Step 4: Extract the reference pressures for the component type
    pref = pd.read_csv(file_path + ctype + '/ref.csv', index_col='Edition').loc[[edition], :]
    # Step 5: Extract similitude parameters for wind speed, height, and exposure
    # Similitude in wind speed:
    if wind_speed == ref_speed:
        vfactor = 0.0
    else:
        if edition == 'ASCE 7-93':
            vfactor = pd.read_csv(file_path + ctype + '/v93.csv', index_col='Edition')[str(wind_speed)][edition]
        else:
            vfactor = pd.read_csv(file_path + ctype + '/v.csv', index_col='Edition')[str(wind_speed)][edition]
    # Similitude in height:
    if h_bldg == ref_hbldg:
        hfactor = 0.0
    else:
        if edition == 'ASCE 7-93':
            hfactor = pd.read_csv(file_path + ctype + '/h93.csv')[str(h_bldg) + ' ft'][0]
        else:
            hfactor = pd.read_csv(file_path + ctype + '/h.csv')[str(h_bldg) + ' ft'][0]
    # Similitude in exposure categories:
    if exposure == ref_exposure:
        efactor = 0.0
    else:
        efactor = pd.read_csv(file_path + ctype + '/e' + edition[-2:] + '.csv', index_col='Height in ft')[exposure][h_bldg]
    # Step 6: Apply the similitude parameters to get the final pressures for each zone:
    factor_lst = [vfactor, hfactor, efactor]
    psim = pref.loc[edition]
    for factor in factor_lst:
        psim = factor*psim + psim
    return psim


# Test it out:
edition = 'ASCE 7-02'
h_bldg = 9
length = 27
ratio = h_bldg/length
exposure = 'B'
wind_speed = 120
direction = 'parallel'
ref_pitch = 9
ref_cat =2
hpr = True
h_ocean = True
encl_class = 'Enclosed'
# Difference in wind speed:
psim = get_roof_uplift_pressure(edition, h_bldg, length, exposure, wind_speed, direction, ref_pitch)
pressures = PressureCalc()
rmps = pressures.rmwfrs_pressure(wind_speed, exposure, edition, h_bldg, length, ratio, ref_pitch, ref_cat, hpr, h_ocean, encl_class)
print('real pressure:', rmps, 'change in wind speed:', rmps)
# Difference in height:
h_bldg = 27
length = 27
ratio = h_bldg/length
hpsim = get_roof_uplift_pressure(edition, h_bldg, length, exposure, wind_speed, direction, ref_pitch)
hrmps = pressures.rmwfrs_pressure(wind_speed, exposure, edition, h_bldg, length, ratio, ref_pitch, ref_cat, hpr, h_ocean, encl_class)
print('real pressure:', hrmps, 'change in height:', hrmps)
# Difference in exposure categories:
exposure = 'C'
epsim = get_roof_uplift_pressure(edition, h_bldg, length, exposure, wind_speed, direction, ref_pitch)
ermps = pressures.rmwfrs_pressure(wind_speed, exposure, edition, h_bldg, length, ratio, ref_pitch, ref_cat, hpr, h_ocean, encl_class)
print('real pressure:', ermps, 'change in exposure:', ermps)