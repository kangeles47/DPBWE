from asset import Parcel
from code_capacities import get_cc_zone_width, find_cc_zone_points, assign_wcc_pressures, assign_rmwfrs_pressures

# Initialization script for data-driven workflow:

# Asset Description
# Parcel Models
lon = -85.676188
lat = 30.190142
test = Parcel('12345', 4, 'Financial', 1989, '1002 23RD ST W PANAMA CITY 32405', 41134, lon, lat)

# Hazard Characterization
# Here is where we provide wind speed, location, etc. for data-driven roughness length
# Will also need to add WDR (rain rate) characterizations
# Will also need to add subroutine for WBD

# Asset Representation
# Populate component capacities:
edition = 'ASCE 7-10'
exposure = 'B'
wind_speed = 120
p = assign_rmwfrs_pressures(test, edition, exposure, wind_speed)
a = get_cc_zone_width(test)
print('zone width in ft:', a)
roof_flag = True
zone_pts, int_poly = find_cc_zone_points(test, a, roof_flag, edition)
assign_wcc_pressures(test, zone_pts, edition, exposure, wind_speed)
print(exposure)

# Response Simulation

# Damage Estimation

# Loss Estimation