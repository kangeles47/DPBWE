from asset import Parcel
from matplotlib import pyplot as plt
from shapely.geometry import Polygon
from bldg_code import ASCE7

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
# Generate and determine the building's TPU surfaces:
tpu_wdir = 315
test.create_TPU_surfaces('local', tpu_wdir)
# Populate component capacities:
asce7 = ASCE7(test, loading_flag=True)
edition = 'ASCE 7-10'
exposure = 'B'
wind_speed = 120
wind_direction = 0
asce7.assign_rmwfrs_pressures(test, edition, exposure, wind_speed)
# Assign pressures to roof assembly:
a = asce7.get_cc_zone_width(test)
print('zone width in ft:', a)
roof_flag = True
zone_pts, int_poly, zone2_polys = asce7.find_cc_zone_points(test, a, roof_flag, edition)
asce7.assign_wcc_pressures(test, zone_pts, edition, exposure, wind_speed)
#assign_rcc_pressures(test, zone_pts, int_poly, edition, exposure, wind_speed)
# Create a polygon with full surf points:
poly_xs = []
poly_ys = []
new_points = []
for row in zone_pts.index:
    for col in range(0, len(zone_pts.loc[row])):
        if row == 0:
            poly_xs.append(zone_pts.iloc[row, col].x)
            poly_ys.append(zone_pts.iloc[row, col].y)
            new_points.append(zone_pts.iloc[row, col])
        elif row> 0 and (col > 0):
            poly_xs.append(zone_pts.iloc[row, col].x)
            poly_ys.append(zone_pts.iloc[row, col].y)
            new_points.append(zone_pts.iloc[row, col])
        else:
            pass
# Create a polygon:
new_poly = Polygon(new_points)
# Plot the wall pressures:
surf_list = []
surf_list.append(test.create_zcoords(new_poly, 0))
surf_list.append(test.create_zcoords(new_poly, test.hasGeometry['Height']))
# Create the surface polygons:
poly_list = []
for plane in range(0, len(surf_list)-1):
    for pt in range(0, len(surf_list[0])-1):
        wcc_surf = Polygon([surf_list[plane][pt], surf_list[plane + 1][pt], surf_list[plane + 1][pt + 1], surf_list[plane][pt + 1]])
        poly_list.append(wcc_surf)
# Set up plotting:
fig = plt.figure(dpi=200)
ax = plt.axes(projection='3d')
for poly in poly_list:
    xs = []
    ys = []
    zs = []
    for pts in list(poly.exterior.coords):
        xs.append(pts[0])
        ys.append(pts[1])
        zs.append(pts[2])
        # Plot the surface geometry:
        ax.plot(xs, ys, zs, color='k')
# Make the panes transparent:
ax.w_xaxis.set_pane_color((1.0, 1.0, 1.0, 1.0))
ax.w_yaxis.set_pane_color((1.0, 1.0, 1.0, 1.0))
ax.w_zaxis.set_pane_color((1.0, 1.0, 1.0, 1.0))
# Make the grids transparent:
ax.xaxis._axinfo["grid"]['color'] = (1, 1, 1, 0)
ax.yaxis._axinfo["grid"]['color'] = (1, 1, 1, 0)
ax.zaxis._axinfo["grid"]['color'] = (1, 1, 1, 0)
# Plot labels
ax.set_xlabel('x [m]')
ax.set_ylabel('y [m]')
ax.set_zlabel('z [m]')
plt.axis('off')
plt.show()
print(exposure)


# Response Simulation

# Damage Estimation

# Loss Estimation