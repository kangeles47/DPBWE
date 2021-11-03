import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from shapely.geometry import Polygon, Point
from shapely.ops import nearest_points
from scipy.spatial import Voronoi, voronoi_plot_2d
from tpu_pressures import calc_tpu_pressures, convert_to_tpu_wdir
from create_fragility import get_wind_speed
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


def generate_pressure_loading(bldg, wind_speed, wind_direction, tpu_flag):
    # Populate envelope pressures:
    if tpu_flag:
        # Convert wind direction to TPU wind direction:
        tpu_wdir = convert_to_tpu_wdir(wind_direction, bldg)
        key = 'local'
        # Find TPU wind pressures:
        df_tpu_pressures = calc_tpu_pressures(bldg, key, tpu_wdir, wind_speed)
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
        r_indices = []
        for row in df_facade.index:
            ptap_z = df_facade.iloc[row]['Real Life Location'].z
            if round(ptap_z, 4) == round(bldg.hasGeometry['Height'], 4):
                r_indices.append(row)
            else:
                pass
        for r in roof_indices:
            r_indices.append(r)
        df_roof = df_tpu_pressures.iloc[r_indices]
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
                    # Try buffering the point:
                    bpt = Point(rptap_loc.x, rptap_loc.y).buffer(distance=3)
                    for subelem in bldg.adjacentElement['Roof'][0].hasSubElement['cover']:
                        if bpt.intersects(subelem.hasGeometry['2D Geometry']['local']):
                            subelem.hasDemand['wind pressure']['external'] = subelem.hasDemand['wind pressure'][
                                'external'].append(df_roof.loc[idx], ignore_index=True)
                            map_flag = True
                        else:
                            pass
                if not map_flag:
                    no_map_roof.append(df_roof.loc[idx])
            #print(len(no_map_roof))


def ftree(bldg, zone_flag):
    # Loop through building envelope components and check for breach:
    fail_elements = []
    for key in bldg.adjacentElement:
        if key == 'Floor':
            pass
        elif key == 'Roof':
            if len(bldg.adjacentElement[key][0].hasSubElement['cover']) > 0:
                roof_fail = {'time': [], 'region': [], 'area': []}
                for elem in bldg.adjacentElement[key][0].hasSubElement['cover']:
                    elem_fail = {'time': [], 'fail': [], 'region': []}
                    try:
                        for row in elem.hasDemand['wind pressure']['external'].index:
                            ptap_poly = elem.hasDemand['wind pressure']['external'].iloc[row]['Tap Polygon']
                            # Failure checks for each time step:
                            for col in elem.hasDemand['wind pressure']['external'].columns[2:]:
                                elem_fail['time'].append(int(col[2:]))
                                pressure_demand = elem.hasDemand['wind pressure']['external'].iloc[row][col]
                                # First check if failure occurred, then pull the corresponding failure region:
                                if pressure_demand < 0 and pressure_demand < elem.hasCapacity['wind pressure']['total']['negative']:
                                    elem_fail['fail'].append(True)
                                    #fail_pairs.append((pressure_demand, elem.hasCapacity['wind pressure']['total']['negative']))
                                elif pressure_demand > 0 and pressure_demand > elem.hasCapacity['wind pressure']['total']['positive']:
                                    elem_fail['fail'].append(True)
                                    #fail_pairs.append((pressure_demand, elem.hasCapacity['wind pressure']['total']['positive']))
                                # If failure occurred, pull the corresponding failure region:
                                if zone_flag:
                                    if ptap_poly.intersects(elem.hasGeometry['2D Geometry']['local']):
                                        elem_fail['region'].append(
                                            ptap_poly.intersection(elem.hasGeometry['2D Geometry']['local']))
                                    else:
                                        elem_fail['region'].append(ptap_poly)  # Pressure tap is within the element's 2D geometry
                                else:
                                    # Grab the element's entire 2D polygon:
                                    elem_fail['region'].append(elem.hasGeometry['2D Geometry']['local'])
                        elem.hasFailure['wind pressure'] = elem_fail
                    except TypeError:
                        # Demand is a single value:
                        if elem.hasDemand['wind pressure']['external'] >= elem.hasCapacity['wind pressure']['external']:
                            pass
                    if elem.hasFailure['wind pressure']:
                        fail_elements.append(elem)
                    else:
                        pass
                # Figure out when maximum response occurred:
                for t in range(0, len(elem_fail['time'])):
                    if elem_fail['fail']:
                        pass
            else:
                pass
        elif key == 'Walls':
            pass
            for elem in bldg.adjacentElement[key]:
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
    # Plotting:
    # Roof damage:
    # for fail_elem in fail_elements:
    #     xf, yf = fail_elem.hasGeometry['2D Geometry']['local'].exterior.xy
    #     plt.plot(xf, yf, 'k')
    # for tap in range(0, len(fail_ptaps)):
    #     tloc = fail_ptaps[tap]['Real Life Location']
    #     try:
    #         plt.scatter(tloc.x, tloc.y, color='red')
    #     except AttributeError:
    #         pass
    # plt.title('Roof pressure taps - damaged')
    # plt.show()
    # d = 0


def ftree_initial(bldg):
    # Loop through building envelope components and check for breach:
    fail_elements = []
    fail_ptaps = []
    fail_pairs = []
    for key in bldg.adjacentElement:
        if key == 'Floor':
            pass
        elif key == 'Roof':
            if len(bldg.adjacentElement[key][0].hasSubElement['cover']) > 0:
                for elem in bldg.adjacentElement[key][0].hasSubElement['cover']:
                    try:
                        for row in elem.hasDemand['wind pressure']['external'].index:
                            pressure_demand = elem.hasDemand['wind pressure']['external'].iloc[row]['Pressure']
                            if pressure_demand < 0 and pressure_demand < elem.hasCapacity['wind pressure']['total']['negative']:
                                elem.hasFailure['wind pressure'] = True
                                fail_ptaps.append(elem.hasDemand['wind pressure']['external'].iloc[row])
                                fail_pairs.append((pressure_demand, elem.hasCapacity['wind pressure']['total']['negative']))
                            elif pressure_demand > 0 and pressure_demand > elem.hasCapacity['wind pressure']['total']['positive']:
                                elem.hasFailure['wind pressure'] = True
                                fail_ptaps.append(elem.hasDemand['wind pressure']['external'].iloc[row])
                                fail_pairs.append(
                                    (pressure_demand, elem.hasCapacity['wind pressure']['total']['positive']))
                    except TypeError:
                        # Demand is a single value:
                        if elem.hasDemand['wind pressure']['external'] >= elem.hasCapacity['wind pressure']['external']:
                            pass
                    if elem.hasFailure['wind pressure']:
                        fail_elements.append(elem)
                    else:
                        pass
            else:
                pass
        elif key == 'Walls':
            for elem in bldg.adjacentElement[key]:
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
    # Plotting:
    # Roof damage:
    for fail_elem in fail_elements:
        xf, yf = fail_elem.hasGeometry['2D Geometry']['local'].exterior.xy
        plt.plot(xf, yf, 'k')
    for tap in range(0, len(fail_ptaps)):
        tloc = fail_ptaps[tap]['Real Life Location']
        try:
            plt.scatter(tloc.x, tloc.y, color='red')
        except AttributeError:
            pass
    plt.title('Roof pressure taps - damaged')
    plt.show()
    d = 0


def get_voronoi(bldg):
    # Get the voronoi discretization of pressure tap areas - element specific:
    # Start with roof elements and their pressure taps:
    coord_list = []
    if len(bldg.adjacentElement['Roof'][0].hasSubElement['cover']) == 0:
        # Find polygons for the entire roof surface:
        for idx in bldg.adjacentElement['Roof'][0].hasDemand['wind pressure']['external'].index:
            ptap_loc = bldg.adjacentElement['Roof'][0].hasDemand['wind pressure']['external'].iloc[idx]['Real Life Location']
            coord_list.append((ptap_loc.x, ptap_loc.y))
    else:
        for elem in bldg.adjacentElement['Roof'][0].hasSubElement['cover']:
            # Use pressure tap locations as input coordinate list:
            for idx in elem.hasDemand['wind pressure']['external'].index:
                ptap_loc = elem.hasDemand['wind pressure']['external'].iloc[idx]['Real Life Location']
                coord_list.append((ptap_loc.x, ptap_loc.y))
    # Buffer out the roof geometry to ensure perimeter points get a closed geometry:
    bpoly = bldg.adjacentElement['Roof'][0].hasGeometry['2D Geometry']['local'].buffer(distance=20)
    for c in bpoly.exterior.coords:
        coord_list.append(c)
    vor = Voronoi(list(set(coord_list)))
    # Use vertices and regions to create geometry for each pressure tap:  # list of lists - each list is a single region
    vertices = vor.vertices
    regions = vor.regions
    poly_list = []
    for r in regions:
        if len(r) > 0:
            # Elements in list r are indices to the vertices array describing region:
            point_list = []
            if -1 in r:
                new_poly = 0
            else:
                for i in range(0, len(r)):
                    point_list.append((vertices[r[i]][0], vertices[r[i]][1]))
                # Check if the geometry intersects the roof perimeter:
                new_poly = Polygon(point_list)
                if new_poly.intersects(bldg.adjacentElement['Roof'][0].hasGeometry['2D Geometry']['local']):
                    # Find the intersection region:
                    new_poly = new_poly.intersection(bldg.adjacentElement['Roof'][0].hasGeometry['2D Geometry']['local'])
                else:
                    pass
        else:
            new_poly = 0
        poly_list.append(new_poly)
    for poly in poly_list:
        if isinstance(poly, Polygon):
            xpoly, ypoly = poly.exterior.xy
            plt.plot(xpoly, ypoly, 'r')
    x, y = bldg.adjacentElement['Roof'][0].hasGeometry['2D Geometry']['local'].exterior.xy
    plt.plot(x,y)
    plt.show()
    if len(bldg.adjacentElement['Roof'][0].hasSubElement['cover']) == 0:
        pass
    else:
        # Loop through pressure taps for each element and add their corresponding polygons:
        for elem in bldg.adjacentElement['Roof'][0].hasSubElement['cover']:
            # Use pressure tap locations as input coordinate list:
            tap_poly_list = []
            for idx in elem.hasDemand['wind pressure']['external'].index:
                ptap_loc = elem.hasDemand['wind pressure']['external'].iloc[idx]['Real Life Location']
                new_arr = np.array([ptap_loc.x, ptap_loc.y])
                vpoint_idx = np.where(vor.points==new_arr)[0][0]
                vregion_idx = vor.point_region[vpoint_idx]
                tap_poly_list.append(poly_list[vregion_idx])
            elem.hasDemand['wind pressure']['external']['Tap Polygon'] = tap_poly_list

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
wind_speed = get_wind_speed(test, wind_speed_file_path, exposure, unit)
wind_direction = 90
cc_flag, mwfrs_flag = True, True
#test.hasGeometry['Height'] = 9*4
#test.hasGeometry['Height'] = 9
populate_code_capacities(test, cc_flag, mwfrs_flag, exposure)
generate_pressure_loading(test, wind_speed, wind_direction, tpu_flag=True)
get_voronoi(test)
ftree(test, zone_flag=True)
