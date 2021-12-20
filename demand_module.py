import pandas as pd
from parcel import Parcel
from OBDM.zone import Site, Building
from bldg_code import ASCE7
from OBDM.element import Roof
from fault_tree import populate_code_capacities, generate_pressure_loading, find_peak_pressure_response
from get_debris import run_debris


# Asset Description
# Parcel Models
lon = -85.676188
lat = 30.190142
test = Parcel('12345', 4, 'financial', 2000, '1002 23RD ST W PANAMA CITY 32405', 41134, lon, lat, length_unit='ft', plot_flag=False)
test.hasElement['Roof'][0].hasShape['flat'] = True
test.hasElement['Roof'][0].hasPitch = 0
wind_speed_file_path = 'D:/Users/Karen/Documents/Github/DPBWE/Datasets/WindFields/2018-Michael_windgrid_ver36.csv'
exposure = 'B'
unit = 'english'
basic_wind_speed = 123.342  # 126?
wind_direction = 0
cc_flag, mwfrs_flag = True, True
# populate_code_capacities(test, cc_flag, mwfrs_flag, exposure)
# generate_pressure_loading(test, basic_wind_speed, wind_direction, tpu_flag=True, csv_flag=True)
# find_peak_pressure_response(test, zone_flag=True, time_flag=True)
#test.hasGeometry['Height'] = 9*4
#test.hasGeometry['Height'] = 52.5
# Read in parcel data from surrounding buildings:
df_parcels = pd.read_csv('C:/Users/Karen/Desktop/Parcel_data.csv')
# Create data models for each building:
site = Site()
plot_flag=False
length_unit='ft'
for p in df_parcels.index:
    pid = df_parcels['Parcel Id'][p]
    num_stories = df_parcels['Stories'][p]
    occupancy = df_parcels['OccType'][p]
    yr_built = df_parcels['Year Built'][p]
    address = df_parcels['Address'][p]
    area = df_parcels['Square Footage'][p]
    lon = df_parcels['Longitude'][p]
    lat = df_parcels['Latitude'][p]
    new_bldg = Parcel(pid, num_stories, occupancy, yr_built, address, area, lon, lat, length_unit, plot_flag)
    # Add parcel-specific roof cover information:
    new_bldg.adjacentElement['Roof'][0].hasCover = df_parcels['Roof Cover'][p]
    new_bldg.adjacentElement['Roof'][0].hasType = df_parcels['Roof Cover'][p]
    new_bldg.update_zones()
    new_bldg.update_elements()
    site.hasBuilding.append(new_bldg)
site.update_zones()
site.update_interfaces()
site.update_elements()
# Find building-specific debris vulnerability:
wind_direction = 360-45
wind_speed = None  # Need to figure out what wind speed this is
run_debris(test, site, length_unit, wind_direction, wind_speed)
