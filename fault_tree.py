import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from shapely.geometry import Polygon, Point
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


def generate_pressure_loading(bldg, wind_speed, wind_direction, exposure, tpu_flag):
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
        # Add empty DataFrames to facade elements:
        for wall in bldg.adjacentElement['Walls']:
            wall.hasDemand['wind pressure']['external'] = pd.DataFrame(columns=df_facade.columns)
        # Set up plotting:
        # fig = plt.figure()
        # ax = plt.axes(projection='3d')
        no_map = []
        for idx in df_facade.index:
            map_flag = False
            ptap_loc = df_facade['Real Life Location'][idx]
            for story in bldg.hasStory:
                if story.hasElevation[0] <= ptap_loc.z <= story.hasElevation[1]:
                    for wall in story.adjacentElement['Walls']:
                        wall_pts = list(wall.hasGeometry['3D Geometry']['local'].exterior.coords)
                        xw, yw, zw = [], [], []
                        for w in wall_pts:
                            xw.append(w[0])
                            yw.append(w[1])
                            zw.append(w[2])
                        bound_poly = Polygon([(max(xw), max(yw)), (min(xw), max(yw)), (min(xw), min(yw)), (max(xw), min(yw))])
                        if Point(ptap_loc.x, ptap_loc.y).within(bound_poly) or Point(ptap_loc.x, ptap_loc.y).intersects(bound_poly):
                            if min(zw) <= ptap_loc.z <= max(zw):
                                wall.hasDemand['wind pressure']['external'] = wall.hasDemand['wind pressure']['external'].append(df_facade.iloc[idx], ignore_index=True)
                                map_flag = True
                                break
                            else:
                                print('Point within boundary but not wall height')
                        else:
                            pass
                else:
                    pass
            if not map_flag:
                no_map.append(df_facade.iloc[idx])
                #ax.scatter(ptap_loc.x, ptap_loc.y, ptap_loc.z, 'r')
        # for wall in bldg.adjacentElement['Walls']:
        #     wall_pts = list(wall.hasGeometry['3D Geometry']['local'].exterior.coords)
        #     xw, yw, zw = [], [], []
        #     for w in wall_pts:
        #         xw.append(w[0])
        #         yw.append(w[1])
        #         zw.append(w[2])
        #     ax.plot(xw, yw, zw, 'k')
        # plt.show()
        # Set up empty DataFrames for roof or roof_subelements:
        df_roof = df_tpu_pressures.iloc[roof_indices]
        # Map pressures onto roof elements:
        if len(bldg.adjacentElement['Roof'][0].hasSubElement['cover']) == 0:
            # Assign the entire DataFrame to the roof:
            bldg.adjacentElement['Roof'][0].hasDemand['wind pressure']['external'] = df_roof
        else:
            for subelem in bldg.adjacentElement['Roof'][0].hasSubElement['cover']:
                subelem.hasDemand['wind pressure']['external'] = pd.DataFrame(columns=df_roof.columns)
            # Map pressures to roof subelements
            no_map_roof = []
            for idx in df_roof.index:
                map_flag = False
                rptap_loc = df_roof['Real Life Location'][idx]
                for subelem in bldg.adjacentElement['Roof'][0].hasSubElement['cover']:
                    if Point(rptap_loc.x, rptap_loc.y).within(subelem.hasGeometry['2D Geometry']['local']) or Point(rptap_loc.x, rptap_loc.y).intersects(subelem.hasGeometry['2D Geometry']['local']):
                        subelem.hasDemand['wind pressure']['external'] = subelem.hasDemand['wind pressure']['external'].append(df_roof.loc[idx], ignore_index=True)
                        map_flag = True
                    else:
                        pass
                if not map_flag:
                    no_map_roof.append(df_roof.loc[idx])


def ftree(bldg):
    # Loop through building envelope components and check for breach:
    fail_elements = []
    for key in bldg.adjacentElement:
        if key == 'Floor':
            pass
        else:
            for elem in bldg.adjacentElement[key]:
                if key == 'Floor':
                    pass
                elif key == 'Roof':
                    if len(bldg.adjacentElement[key][0].hasSubElement['cover']) > 0:
                        for row in bldg.adjacentElement[key][0].hasDemand['wind pressure']:
                            pass
                    else:
                        # Check the entire roof:
                        for row in bldg.adjacentElement[key][0].hasDemand:
                            pass
                else:
                    # Check facade components:
                    try:
                        for row in elem.hasDemand['wind pressure']['external'].index:
                            pressure_demand = elem.hasDemand['wind pressure']['external'].iloc[row]['Pressure']
                            if pressure_demand < 0 and pressure_demand < elem.hasCapacity['wind pressure']['total']['negative']:
                                elem.hasFailure['wind pressure'] = True
                            elif pressure_demand > 0 and pressure_demand > elem.hasCapacity['wind pressure']['total']['positive']:
                                elem.hasFailure['wind pressure'] = True
                    except TypeError:
                        # Demand is a single value:
                        if elem.hasDemand['wind pressure']['external'] >= elem.hasCapacity['wind pressure']['external']:
                            pass
                    if elem.hasFailure['wind pressure']:
                        fail_elements.append(elem)
                    else:
                        pass

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
populate_code_capacities(test, cc_flag, mwfrs_flag, exposure)
generate_pressure_loading(test, wind_speed, wind_direction, exposure, tpu_flag=True)
ftree(test)
