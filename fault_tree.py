import numpy as np
import matplotlib.pyplot as plt
from tpu_pressures import calc_tpu_pressures, convert_to_tpu_wdir
from parcel import Parcel


# Start with building-level fault tree:
def sim_bldg_pressure_response(bldg, wind_speed, wind_direction, tpu_flag, cc_flag, mwfrs_flag):
    # Populate envelope pressures:
    if tpu_flag:
        # Convert wind direction to TPU wind direction:
        convert_to_tpu_wdir(wind_direction, bldg)
        tpu_wdir = 0
        key = 'local'
        edition = 'ASCE 7-16'
        exposure = 'B'
        cat = 2
        hpr = True
        df_tpu_pressures = calc_tpu_pressures(bldg, key, tpu_wdir, wind_speed, exposure, edition, cat, hpr)

# Asset Description
# Parcel Models
lon = -85.676188
lat = 30.190142
test = Parcel('12345', 4, 'financial', 1989, '1002 23RD ST W PANAMA CITY 32405', 41134, lon, lat, length_unit='ft')
test.hasElement['Roof'][0].hasShape['flat'] = True
test.hasElement['Roof'][0].hasPitch = 0
wind_speed = 120
wind_direction = 0
sim_bldg_pressure_response(test, wind_speed, wind_direction, tpu_flag=True, cc_flag=False, mwfrs_flag=False)