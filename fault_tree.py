import numpy as np
import matplotlib.pyplot as plt
from tpu_pressures import calc_tpu_pressures, convert_to_tpu_wdir
from parcel import Parcel
from bldg_code import ASCE7


def populate_code_capacities(bldg, cc_flag, mwfrs_flag, exposure, wind_speed):
    # Populate code-informed capacities:
    asce7 = ASCE7(bldg, loading_flag=True)
    if cc_flag:
        a = asce7.get_cc_zone_width(bldg)
        roof_flag = True
        zone_pts, roof_polys = asce7.find_cc_zone_points(bldg, a, roof_flag, asce7.hasEdition)
        asce7.assign_wcc_pressures(bldg, zone_pts, asce7.hasEdition, exposure, wind_speed)
        asce7.assign_rcc_pressures(test, zone_pts, roof_polys, asce7.hasEdition, exposure, wind_speed)
    if mwfrs_flag:
        asce7.assign_rmwfrs_pressures(test, asce7.hasEdition, exposure, wind_speed)


def generate_pressure_loading(bldg, wind_speed, wind_direction, exposure, tpu_flag, cc_flag, mwfrs_flag):
    # Populate envelope pressures:
    if tpu_flag:
        # Convert wind direction to TPU wind direction:
        tpu_wdir = convert_to_tpu_wdir(wind_direction, bldg)
        key = 'local'
        edition = 'ASCE 7-16'
        cat = 2
        hpr = True
        # Find TPU wind pressures:
        df_tpu_pressures = calc_tpu_pressures(bldg, key, tpu_wdir, wind_speed, exposure, edition, cat, hpr)
    else:
        # Populate code-informed pressures:
        asce7 = ASCE7(bldg, loading_flag=True)
        if cc_flag:
            a = asce7.get_cc_zone_width(bldg)
            roof_flag = True
            zone_pts, int_poly, zone2_polys = asce7.find_cc_zone_points(bldg, a, roof_flag, asce7.hasEdition)
            asce7.assign_wcc_pressures(bldg, zone_pts, asce7.hasEdition, exposure, wind_speed)
            asce7.assign_rcc_pressures(test, zone_pts, int_poly, asce7.hasEdition, exposure, wind_speed)
        if mwfrs_flag:
            asce7.assign_rmwfrs_pressures(test, asce7.hasEdition, exposure, wind_speed)



# Asset Description
# Parcel Models
lon = -85.676188
lat = 30.190142
test = Parcel('12345', 4, 'financial', 1989, '1002 23RD ST W PANAMA CITY 32405', 41134, lon, lat, length_unit='ft')
test.hasElement['Roof'][0].hasShape['flat'] = True
test.hasElement['Roof'][0].hasPitch = 0
wind_speed = 120
wind_direction = 45
exposure = 'B'
cc_flag, mwfrs_flag = True, True
test.hasGeometry['Height'] = 9*4
test.hasGeometry['Height'] = 9
populate_code_capacities(test, cc_flag, mwfrs_flag, exposure, wind_speed)
#generate_pressure_loading(test, wind_speed, wind_direction, exposure, tpu_flag=True, cc_flag=False, mwfrs_flag=False)