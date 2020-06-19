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
        pref = pd.read_csv(file_path + 'ref1.csv')
    elif use_case == 2:
        pref = pd.read_csv(file_path + 'ref2.csv')
    elif use_case == 3:
        pref = pd.read_csv(file_path + 'ref3.csv')
    elif use_case == 4:
        pref = pd.read_csv(file_path + 'ref4.csv')
    # Step 3: Filter out any zones that are not needed for use cases 1 and 2:
    if use_case == 1 and ratio == 0.5:
        pref = pref[pref.columns[0:2]] # Case with only 3 zones
    elif use_case == 2 and ratio == 1.0:
        pref = pref[pref.columns[0:1]] # Case with only 1 zone

# Test it out:
edition = 'ASCE 7-02'
h_bldg = 9
length = 18
exposure = 'B'
wind_speed = 120
direction = 'normal'
pitch = 8
get_roof_uplift_pressure(edition, h_bldg, length, exposure, wind_speed, direction, pitch)