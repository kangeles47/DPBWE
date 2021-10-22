import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from shapely.geometry import Polygon
from tpu_pressures import calc_tpu_pressures, convert_to_tpu_wdir
from parcel import Parcel
from bldg_code import ASCE7


def populate_code_capacities(bldg, cc_flag, mwfrs_flag, exposure):
    # Populate code-informed capacities:
    asce7 = ASCE7(bldg, loading_flag=True)
    # Get the building's code wind speed:
    wind_speed = asce7.get_code_wind_speed(bldg)
    if cc_flag:
        a = asce7.get_cc_zone_width(bldg)
        roof_flag = True
        zone_pts, roof_polys = asce7.find_cc_zone_points(bldg, a, roof_flag, asce7.hasEdition)
        asce7.assign_wcc_pressures(bldg, zone_pts, asce7.hasEdition, exposure, wind_speed)
        asce7.assign_rcc_pressures(test, roof_polys, asce7.hasEdition, exposure, wind_speed)
    if mwfrs_flag:
        pass
        #asce7.assign_rmwfrs_pressures(test, asce7.hasEdition, exposure, wind_speed)


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
        # Map pressures to specific elements on building envelope:
        # Start with facade components:
        roof_indices = df_tpu_pressures.loc[df_tpu_pressures['Surface Number'] == 5].index
        df_facade = df_tpu_pressures.drop(roof_indices)
        fig = plt.figure()
        ax = plt.axes(projection='3d')
        for wall in bldg.adjacentElement['Walls']:
            wall_pressures = pd.DataFrame(columns=df_facade.columns)
            for idx in df_facade.index:
                # Use the point geometry to buffer it out for a distance:
                # buff_pt = df_facade['Real Life Location'][idx].buffer(distance=2)
                # xb, yb = buff_pt.exterior.xy
                # pts_xyz = []
                # for j in range(0, len(xb)):
                #     pts_xyz.append((xb[j], yb[j], df_facade['Real Life Location'][idx].z))
                # buff_poly = Polygon(pts_xyz)
                if df_facade['Real Life Location'][idx].within(wall.hasGeometry['3D Geometry']['local']) or df_facade['Real Life Location'][idx].intersects(wall.hasGeometry['3D Geometry']['local']):
                    # Check if this pressure is going to be mapped to a window element:
                    if wall.hasSubElement is not None:
                        pass
                    else:
                        pass
                    wall_pressures = wall_pressures.append(df_facade.iloc[idx], ignore_index=True)
                else:
                    # Buffer the point:
                    # Use the point geometry to buffer it out for a distance:
                    buff_pt = df_facade['Real Life Location'][idx].buffer(distance=3)
                    xb, yb = buff_pt.exterior.xy
                    pts_xyz = []
                    for j in range(0, len(xb)):
                        pts_xyz.append((xb[j], yb[j], df_facade['Real Life Location'][idx].z))
                    buff_poly = Polygon(pts_xyz)
                    if buff_poly.intersects(wall.hasGeometry['3D Geometry']['local']):
                        wall_pressures = wall_pressures.append(df_facade.iloc[idx], ignore_index=True)
                    else:
                        pass
            wall.hasDemand['wind pressure']['external'] = wall_pressures
            wall_points = list(wall.hasGeometry['3D Geometry']['local'].exterior.coords)
            xw, yw, zw = [], [], []
            for w in wall_points:
                xw.append(w[0])
                yw.append(w[1])
                zw.append(w[2])
            if len(wall_pressures) > 0:
                ax.plot(xw, yw, zw, 'r')
            else:
                ax.plot(xw, yw, zw, 'k')
        for idx in df_facade.index:
            point = df_facade['Real Life Location'][idx]
            xyz = list(point.coords)[0]
            ax.scatter(xyz[0], xyz[1], xyz[2])
        plt.show()
        # Map pressures onto roof elements:
        df_roof = df_tpu_pressures.iloc[roof_indices]
        if len(bldg.adjacentElement['Roof'][0].hasSubElement['cover']) > 0:
            for subelem in bldg.adjacentElement['Roof'][0].hasSubElement['cover']:
                roof_pressures = pd.DataFrame(columns=df_roof.columns)
                for idx in df_roof.index:
                    if df_roof['Real Life Location'][idx].within(subelem.hasGeometry['3D Geometry']['local']) or df_roof['Real Life Location'][idx].intersects(subelem.hasGeometry['3D Geometry']['local']):
                        roof_pressures = roof_pressures.append(df_roof.iloc[idx], ignore_index=True)
                    else:
                        pass
        else:
            bldg.adjacentElement['Roof'][0].hasDemand['wind pressure']['external'] = df_roof
    else:
        # Populate code-informed pressures:
        asce7 = ASCE7(bldg, loading_flag=True)
        if cc_flag:
            a = asce7.get_cc_zone_width(bldg)
            roof_flag = True
            zone_pts, int_poly, zone2_polys = asce7.find_cc_zone_points(bldg, a, roof_flag, asce7.hasEdition)
            asce7.assign_wcc_pressures(bldg, zone_pts, asce7.hasEdition, exposure, wind_speed)
            asce7.assign_rcc_pressures(test, zone_pts, int_poly, asce7.hasEdition, exposure)
        if mwfrs_flag:
            asce7.assign_rmwfrs_pressures(test, asce7.hasEdition, exposure, wind_speed)



# Asset Description
# Parcel Models
lon = -85.676188
lat = 30.190142
test = Parcel('12345', 4, 'financial', 2000, '1002 23RD ST W PANAMA CITY 32405', 41134, lon, lat, length_unit='ft', plot_flag=False)
test.hasElement['Roof'][0].hasShape['flat'] = True
test.hasElement['Roof'][0].hasPitch = 0
wind_speed = 120
wind_direction = 45
exposure = 'B'
cc_flag, mwfrs_flag = True, True
#test.hasGeometry['Height'] = 9*4
#test.hasGeometry['Height'] = 9
#populate_code_capacities(test, cc_flag, mwfrs_flag, exposure)
generate_pressure_loading(test, wind_speed, wind_direction, exposure, tpu_flag=True, cc_flag=False, mwfrs_flag=False)