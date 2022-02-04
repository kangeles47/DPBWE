import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from shapely.geometry import Polygon, Point, LineString, MultiPoint
from scipy.stats import norm, uniform
from tpu_pressures import calc_tpu_pressures, convert_to_tpu_wdir
from bldg_code import ASCE7
from OBDM.element import Roof
from code_pressures import PressureCalc
from get_debris import get_trajectory, get_num_dobjects, get_traj_line


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
        asce7.assign_rcc_pressures(bldg, roof_polys, asce7.hasEdition, exposure, wind_speed)
    if mwfrs_flag:
        pass
        #asce7.assign_rmwfrs_pressures(test, asce7.hasEdition, exposure, wind_speed)


def generate_pressure_loading(bldg, basic_wind_speed, wind_direction, tpu_flag, csv_flag):
    """
    A function to apply DAD or code-informed pressures onto the building envelope.
    Updates bldg Roof object and/or subelements with pressures and tap information.
    Updates facade elements with pressure and tap information.

    :param bldg: The building that is going to be pressurized.
    :param basic_wind_speed: Input basic wind speed (open terrain at 33 ft), in mph
    :param wind_direction: The real-life wind direction, relative to cardinal directions.
    :param tpu_flag: True if DAD pressure loading is to be applied.
    :param csv_flag: True if a .csv of the pressure time history is available.
    """
    # 1) Populate envelope pressures:
    if tpu_flag:
        if csv_flag:
            # First see if we have a .csv available with pressure output:
            df_tpu_pressures = pd.read_csv('D:/Users/Karen/Documents/GitHub/DPBWE/TPU_ZERO_DEG_CS.csv')
            pt_locs = []
            for row in range(0, len(df_tpu_pressures['Real Life Location'])):
                new_pt = df_tpu_pressures['Real Life Location'][row].split()[-3:]
                new_x = float(new_pt[0].strip('('))
                new_y = float(new_pt[1])
                new_z = float(new_pt[2].strip(')'))
                pt_locs.append(Point(new_x, new_y, new_z))
            df_tpu_pressures['Real Life Location'] = pt_locs
            df_tpu_pressures['Point Number'] = df_tpu_pressures.index
        else:
            # Convert wind direction to TPU wind direction:
            tpu_wdir = convert_to_tpu_wdir(wind_direction, bldg)
            tpu_wdir = 0
            key = 'local'
            # Find TPU wind pressures:
            df_tpu_pressures = calc_tpu_pressures(bldg, key, tpu_wdir, basic_wind_speed)
            #df_tpu_pressures.to_csv('D:/Users/Karen/Documents/Github/DPBWE/TPU_ZERO_DEG_CS.csv')
        # Save the pressure loading to the Building object:
        bldg.hasDemand['wind pressure']['external'] = df_tpu_pressures
        # 2) Map pressures to specific elements on building envelope:
        # 2a) Start with facade components: Find their indices
        roof_indices = df_tpu_pressures.loc[df_tpu_pressures['Surface Number'] == 5].index
        tcols = [col for col in df_tpu_pressures.columns if 'pt' in col]
        df_facade = df_tpu_pressures.drop(roof_indices).drop(tcols, axis=1)
        # 2b) Create tributary geometries for pressure taps:
        df_facade = get_facade_mesh(bldg, df_facade)
        # Add empty DataFrames to facade elements for placeholding, we are going to add pressure taps:
        for wall in bldg.adjacentElement['Walls']:
            wall.hasDemand['wind pressure']['external'] = []
        # Set up plotting:
        # fig = plt.figure()
        # ax = plt.axes(projection='3d')
        # 2c) Map facade pressure taps to available exterior walls:
        no_map = []  # Empty list to hold any unmapped taps (due to numerical error)
        for idx in df_facade.index:
            map_flag = False
            ptap_loc = df_facade['Real Life Location'][idx]
            # Use line geometries to map pressure tap trib areas to walls:
            xtap, ytap = df_facade['Tap Polygon'][idx].exterior.xy
            tap_line = LineString([(min(xtap), min(ytap)), (max(xtap), max(ytap))])
            #bound_tap_poly = Polygon([(max(xtap), max(ytap)), (min(xtap), max(ytap)), (min(xtap), min(ytap)), (max(xtap), min(ytap))])
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
                        if tap_line.within(bound_poly) or tap_line.intersects(bound_poly):
                            if min(zw) <= ptap_loc.z <= max(zw):
                                wall.hasDemand['wind pressure']['external'].append(idx)
                                #wall.hasDemand['wind pressure']['external'] = wall.hasDemand['wind pressure']['external'].append(df_tpu_pressures.iloc[idx], ignore_index=True)
                                map_flag = True
                                break
                            else:
                                print('Point within boundary but not wall height')
                        else:
                            pass
                else:
                    pass
            if not map_flag:
                no_map.append(idx)
                #ax.scatter(ptap_loc.x, ptap_loc.y, ptap_loc.z, 'r')
        # Plotting:
        fig = plt.figure()
        ax = plt.axes(projection='3d')
        for story in bldg.hasStory:
            for wall in story.adjacentElement['Walls']:
                wall_pts = list(wall.hasGeometry['3D Geometry']['local'].exterior.coords)
                xw, yw, zw = [], [], []
                for w in wall_pts:
                    xw.append(w[0])
                    yw.append(w[1])
                    zw.append(w[2])
                ax.plot(xw, yw, zw)
                for idx in wall.hasDemand['wind pressure']['external']:
                    ptap_loc = df_facade['Real Life Location'][idx]
                    ax.scatter(ptap_loc.x, ptap_loc.y, ptap_loc.z)
        # for wall in bldg.adjacentElement['Walls']:
        #     wall_pts = list(wall.hasGeometry['3D Geometry']['local'].exterior.coords)
        #     xw, yw, zw = [], [], []
        #     for w in wall_pts:
        #         xw.append(w[0])
        #         yw.append(w[1])
        #         zw.append(w[2])
        #     ax.plot(xw, yw, zw, 'k')
        # plt.show()
        # 2e) Now do the mapping for the roof: (set-up placeholders and indices)
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
        df_roof = df_tpu_pressures.iloc[r_indices].drop(tcols, axis=1)
        # 2f) Get pressure tap tributary areas (voronoi diagram):
        # Assign the entire roof DataFrame to main roof element:
        bldg.adjacentElement['Roof'][0].hasDemand['wind pressure']['external'] = df_roof
        get_voronoi(bldg)
        # 2g) Map pressure taps to roof or roof subelements:
        if len(bldg.adjacentElement['Roof'][0].hasSubElement['cover']) == 0:
            # Assign the entire roof DataFrame to main roof element:
            bldg.adjacentElement['Roof'][0].hasDemand['wind pressure']['external'] = df_roof
        else:
            for subelem in bldg.adjacentElement['Roof'][0].hasSubElement['cover']:
                subelem.hasDemand['wind pressure']['external'] = []
            # Here the mapping is done completely in the x-y plane (flat roofs):
            no_map_roof = []
            for idx in bldg.adjacentElement['Roof'][0].hasDemand['wind pressure']['external'].index:
                map_flag = False
                rtap_poly = df_roof['Tap Polygon'][idx]
                for subelem in bldg.adjacentElement['Roof'][0].hasSubElement['cover']:
                    if rtap_poly.within(subelem.hasGeometry['2D Geometry']['local']) or rtap_poly.intersects(subelem.hasGeometry['2D Geometry']['local']):
                        subelem.hasDemand['wind pressure']['external'].append(idx)
                        #subelem.hasDemand['wind pressure']['external'] = subelem.hasDemand['wind pressure']['external'].append(df_roof.loc[idx], ignore_index=True)
                        map_flag = True
                    else:
                        pass
                if not map_flag:
                    # Try buffering the polygon:
                    bpoly = rtap_poly.buffer(distance=3)
                    for subelem in bldg.adjacentElement['Roof'][0].hasSubElement['cover']:
                        if bpoly.intersects(subelem.hasGeometry['2D Geometry']['local']):
                            subelem.hasDemand['wind pressure']['external'].append(idx)
                            map_flag = True
                        else:
                            pass
                if not map_flag:
                    no_map_roof.append(df_roof.loc[idx])
            #print(len(no_map_roof))
        # 2h) Pull pressure tap information for each element according to stored indices:
        for wall in bldg.adjacentElement['Walls']:
            wall.hasDemand['wind pressure']['external'] = df_facade.loc[wall.hasDemand['wind pressure']['external']]
        if len(bldg.adjacentElement['Roof'][0].hasSubElement['cover']) == 0:
            pass
        else:
            for subelem in bldg.adjacentElement['Roof'][0].hasSubElement['cover']:
                subelem.hasDemand['wind pressure']['external'] = df_roof.loc[subelem.hasDemand['wind pressure']['external']]


def find_peak_pressure_response(bldg, zone_flag, time_flag):
    """
     A function to find peak pressure response for a given building.
     This is conducted using a series of demand versus capacity checks (i.e., fault tree analysis).
     Peak response corresponds to that which causes the most area on building envelope to fail.

    :param bldg: A Building object with pressure descriptions for its envelope components.
    :param zone_flag:
    :param time_flag: True if the fault tree is for a time history of pressures (find when peak response occurs).
    :return:
    """
    # Goal is to find when maximum damage occurs:
    if time_flag:
        tcols = [col for col in bldg.hasDemand['wind pressure']['external'].columns if 'pt' in col]
    else:
        pass
    # Loop through building envelope components and check for breach:
    for key in bldg.adjacentElement:
        if key == 'Floor':
            pass
        elif key == 'Roof':
            # First check if C vs. D checks are going to be on entire roof or subelements:
            if len(bldg.adjacentElement[key][0].hasSubElement['cover']) > 0:
                roof_fail = pd.DataFrame({'time': tcols, 'area': np.zeros(len(tcols))})
                for elem in bldg.adjacentElement[key][0].hasSubElement['cover']:
                    if time_flag:
                        time_hist_element_pressure_failure_check(elem, bldg, zone_flag, tcols)
                        # Pull failure data for building-level analysis:
                        if len(elem.hasFailure['wind pressure'].index) > 0:
                            for idx in elem.hasFailure['wind pressure'].index:
                                for r in elem.hasFailure['wind pressure'].loc[idx]['region']:
                                    roof_fail.iat[idx, 1] += r.area
                        else:
                            pass
                    print(elem.hasFailure)
                    # elem_fail = pd.DataFrame({'time': tcols, 'fail': [False for col in tcols], 'region': [[] for col in tcols], 'tap index': [[] for col in tcols]})
                    # fcol = np.where(elem_fail.columns == 'fail')[0][0]
                    # rcol = np.where(elem_fail.columns == 'region')[0][0]
                    # tap_col = np.where(elem_fail.columns == 'tap index')[0][0]
                    # try:
                    #     # Pull the element's positive and negative capacities:
                    #     neg_ecapacity = elem.hasCapacity['wind pressure']['total']['negative']
                    #     pos_ecapacity = elem.hasCapacity['wind pressure']['total']['positive']
                    #     # Check capacity versus demand for all pressure taps and times:
                    #     elem_idx = elem.hasDemand['wind pressure']['external'].index
                    #     pressure_demand = bldg.hasDemand['wind pressure']['external'].loc[elem_idx][tcols]
                    #     # Set up DataFrames with Booleans checking demand versus capacity:
                    #     df_neg = pressure_demand < neg_ecapacity
                    #     df_pos = pressure_demand > pos_ecapacity
                    #     # By time step, check if demand exceeded capacity in any of the pressure taps for this element:
                    #     tneg_check = df_neg[df_neg.columns].any()
                    #     tpos_check = df_pos[df_pos.columns].any()
                    #     # Find which points in time saw failure:
                    #     tneg_fcol = tneg_check.loc[tneg_check==True].index
                    #     tpos_fcol = tpos_check.loc[tpos_check==True].index
                    #     # Grab subsets of each dataframe to conduct query:
                    #     df_neg = df_neg[tneg_fcol]
                    #     df_pos = df_pos[tpos_fcol]
                    #     # print('columns in negative with true value:' + str(len(df_neg.columns)))
                    #     # print('columns in positive with true value:' + str(len(df_pos.columns)))
                    #     # Before proceeding, get rid of any bigger data items we no longer need:
                    #     del pressure_demand, tneg_check, tpos_check, tneg_fcol, tpos_fcol
                    #     # Grab failed regions and record pressure tap indices:
                    #     df_list = [df_neg, df_pos]
                    #     for d in range(0, len(df_list)):
                    #         df_query = df_list[d]
                    #         if len(df_query) > 0:
                    #             for col in df_query.columns:
                    #                 elem_fail_tidx = elem_fail.loc[elem_fail['time']==col].index[0]
                    #                 fail_rows = df_query.loc[df_query[col]==True].index
                    #                 region_list = []
                    #                 tap_index_list = []
                    #                 for row in fail_rows:
                    #                     # Save the tap's index for later reference:
                    #                     tap_index_list.append(row)
                    #                     # Find the resulting failure region:
                    #                     # Here we want the most accurate estimation of roof cover damage.
                    #                     # If pressure tap intersects element, take area within element geometry.
                    #                     # If pressure tap is inside the element geometry, record pressure tap area
                    #                     ptap_poly = elem.hasDemand['wind pressure']['external'].loc[row]['Tap Polygon']
                    #                     if zone_flag:
                    #                         if ptap_poly.intersects(elem.hasGeometry['2D Geometry']['local']):
                    #                             region_list.append(ptap_poly.intersection(elem.hasGeometry['2D Geometry']['local']))
                    #                         else:
                    #                             region_list.append(ptap_poly)  # Pressure tap is within element's 2D geometry
                    #                     else:
                    #                         # Grab the element's entire 2D polygon:
                    #                         region_list.append(elem.hasGeometry['2D Geometry']['local'])
                    #                 # Add failure information to element's dataframe:
                    #                 elem_fail.iat[elem_fail_tidx, rcol] = elem_fail.iat[elem_fail_tidx, rcol] + region_list
                    #                 elem_fail.iat[elem_fail_tidx, fcol] = True
                    #                 elem_fail.iat[elem_fail_tidx, tap_col] = elem_fail.iat[elem_fail_tidx, tap_col] + tap_index_list
                    #                 # Add failure area to overall roof failure information:
                    #                 for r in region_list:
                    #                     roof_fail.iat[elem_fail_tidx, 1] += r.area
                    #         else:
                    #             pass
                    #     # Add the data to the element's data model:
                    #     elem.hasFailure['wind pressure'] = elem_fail.loc[elem_fail['fail']==True]
                    # except TypeError:
                    #     # Demand is a single value:
                    #     if elem.hasDemand['wind pressure']['external'] >= elem.hasCapacity['wind pressure']['external']:
                    #         pass
                # Figure out when maximum response occurred:
                max_idx = roof_fail.loc[roof_fail['area'] == max(roof_fail['area'])].index[0]
                max_time = roof_fail['time'][max_idx]
                print('Max time of roof failure: ' + str(max_time))
                # Loop through elements and retain only data for max response:
                # for elem in bldg.adjacentElement[key][0].hasSubElement['cover']:
                #     max_idx_elem = elem.hasFailure['wind pressure'].loc[elem.hasFailure['wind pressure']['time']==max_time].index
                #     if len(max_idx_elem) > 0:
                #         elem.hasFailure['wind pressure'] = elem.hasFailure['wind pressure'].loc[max_idx_elem[0]]
                #         for r in elem.hasFailure['wind pressure']['region']:
                #             xr, yr = r.exterior.xy
                #             plt.plot(xr, yr, 'r')
                #     else:
                #         elem.hasFailure['wind pressure'] = False
                #     # Plot element geometries:
                #     xe, ye = elem.hasGeometry['2D Geometry']['local'].exterior.xy
                #     plt.plot(xe, ye, 'g')
                # x, y = bldg.adjacentElement['Roof'][0].hasGeometry['2D Geometry']['local'].exterior.xy
                # plt.plot(x, y, 'k', linestyle='dashed')
                # plt.show()
            else:
                pass
        elif key == 'Walls':
            wall_fail = pd.DataFrame({'time': tcols, 'area': np.zeros(len(tcols))})
            for elem in bldg.adjacentElement[key]:
                if time_flag:
                    time_hist_element_pressure_failure_check(elem, bldg, zone_flag, tcols)
                # Pull failure data for building-level analysis:
                if len(elem.hasFailure['wind pressure'].index) > 0:
                    for idx in elem.hasFailure['wind pressure'].index:
                        for r in elem.hasFailure['wind pressure'].loc[idx]['region']:
                            poly_coord_list = list(r.exterior.coords)
                            poly = []
                            for p in poly_coord_list:
                                poly.append([p[0], p[1], p[2]])
                            wall_fail.iat[idx, 1] += polygon_area(poly)
                else:
                    pass
            # Figure out when maximum response occurred:
            # max_idx = wall_fail.loc[wall_fail['area'] == max(wall_fail['area'])].index[0]
            # max_time = wall_fail['time'][max_idx]
            # print('Max time of envelope failure: ' + str(max_time))
            # Loop through elements and retain only data for max response:
            # for elem in bldg.adjacentElement[key]:
            #     max_idx_elem = elem.hasFailure['wind pressure'].loc[elem.hasFailure['wind pressure']['time'] == max_time].index
            #     if len(max_idx_elem) > 0:
            #         elem.hasFailure['wind pressure'] = elem.hasFailure['wind pressure'].loc[max_idx_elem[0]]
            #         for r in elem.hasFailure['wind pressure']['region']:
            #             xr, yr, zr = [], [], []
            #             for i in list(r.exterior.coords):
            #                 xr.append(i[0])
            #                 yr.append(i[1])
            #                 zr.append(i[2])
            #             ax.plot(xr, yr, zr, 'r')
            #     else:
            #         elem.hasFailure['wind pressure'] = False
            #     # Plot element geometries:
            #     xw, yw, zw = [], [], []
            #     wall_coords = list(elem.hasGeometry['3D Geometry']['local'].exterior.coords)
            #     for w in wall_coords:
            #         xw.append(w[0])
            #         yw.append(w[1])
            #         zw.append(w[2])
            #     ax.plot(xw, yw, zw, color='k')
            #plt.show()
    # Find when maximum response occurred (overall):
    dfw = wall_fail.loc[wall_fail['area'] != 0]
    dfr = roof_fail.loc[roof_fail['area'] != 0]
    df_full = dfw.merge(dfr, how='outer', on='time', left_index=True, right_index=True)
    df_full = df_full.fillna(0)
    sum_column = df_full['area_x'] + df_full['area_y']
    df_full['area_sum'] = sum_column
    max_idx = df_full.loc[df_full['area_sum']==max(df_full['area_sum'])].index[0]
    max_time = df_full['time'][max_idx]
    # Now that we know when the maximum response occurred, go back and retain pressure response for that time:
    fig = plt.figure()
    ax = plt.axes(projection='3d')
    # Loop through elements and retain only data for max response:
    for key in bldg.adjacentElement:
        if key == 'Floor':
            pass
        else:
            for elem in bldg.adjacentElement[key]:
                if isinstance(elem.hasFailure['wind pressure'], bool):
                    pass
                else:
                    max_idx_elem = elem.hasFailure['wind pressure'].loc[elem.hasFailure['wind pressure']['time'] == max_time].index
                    if len(max_idx_elem) > 0:
                        elem.hasFailure['wind pressure'] = elem.hasFailure['wind pressure'].loc[max_idx_elem[0]]
                        if key == 'Roof':
                            for r in elem.hasFailure['wind pressure']['region']:
                                xr, yr = r.exterior.xy
                                zr = np.ones(len(xr))*bldg.hasGeometry['Height']
                                ax.plot(xr, yr, zr, 'r')
                        else:
                            for r in elem.hasFailure['wind pressure']['region']:
                                xr, yr, zr = [], [], []
                                for i in list(r.exterior.coords):
                                    xr.append(i[0])
                                    yr.append(i[1])
                                    zr.append(i[2])
                                ax.plot(xr, yr, zr, 'r')
                    else:
                        elem.hasFailure['wind pressure'] = False
                # Plot the element:
                xe, ye, ze = [], [], []
                elem_coords = list(elem.hasGeometry['3D Geometry']['local'].exterior.coords)
                for e in elem_coords:
                    xe.append(e[0])
                    ye.append(e[1])
                    ze.append(e[2])
                ax.plot(xe, ye, ze, color='k')
    plt.show()
    a=0

def polygon_area(poly):
    # Reference: https://stackoverflow.com/questions/12642256/find-area-of-polygon-from-xyz-coordinates
    #shape (N, 3)
    if isinstance(poly, list):
        poly = np.array(poly)
    #all edges
    edges = poly[1:] - poly[0:1]
    # row wise cross product
    cross_product = np.cross(edges[:-1],edges[1:], axis=1)
    #area of all triangles
    area = np.linalg.norm(cross_product, axis=1)/2
    return sum(area)


def time_hist_element_pressure_failure_check(elem, bldg, zone_flag, tcols):
    """
    A function to find failure regions due to pressure on building envelope per time step.

    :param elem:
    :param bldg:
    :param zone_flag:
    :param tcols:
    :return:
    """
    elem_fail = pd.DataFrame({'time': tcols, 'fail': [False for col in tcols], 'region': [[] for col in tcols],
                              'tap index': [[] for col in tcols]})
    fcol = np.where(elem_fail.columns == 'fail')[0][0]
    rcol = np.where(elem_fail.columns == 'region')[0][0]
    tap_col = np.where(elem_fail.columns == 'tap index')[0][0]
    # Pull the element's positive and negative capacities:
    neg_ecapacity = elem.hasCapacity['wind pressure']['total']['negative']
    pos_ecapacity = elem.hasCapacity['wind pressure']['total']['positive']
    # Check capacity versus demand for all pressure taps and times:
    elem_idx = elem.hasDemand['wind pressure']['external'].index
    pressure_demand = bldg.hasDemand['wind pressure']['external'].loc[elem_idx][tcols]
    df_neg = pressure_demand < neg_ecapacity
    df_pos = pressure_demand > pos_ecapacity
    # By time step, check if demand exceeded capacity in any of the pressure taps for this element:
    tneg_check = df_neg[df_neg.columns].any()
    tpos_check = df_pos[df_pos.columns].any()
    # Find which points in time saw failure:
    tneg_fcol = tneg_check.loc[tneg_check == True].index
    tpos_fcol = tpos_check.loc[tpos_check == True].index
    # Grab subsets of each dataframe to conduct query:
    df_neg = df_neg[tneg_fcol]
    df_pos = df_pos[tpos_fcol]
    # Before proceeding, get rid of any bigger data items we no longer need:
    del pressure_demand, tneg_check, tpos_check, tneg_fcol, tpos_fcol
    # Grab failed regions and record pressure tap indices:
    df_list = [df_neg, df_pos]
    for d in range(0, len(df_list)):
        df_query = df_list[d]
        if len(df_query) > 0:
            for col in df_query.columns:
                elem_fail_tidx = elem_fail.loc[elem_fail['time'] == col].index[0]
                fail_rows = df_query.loc[df_query[col] == True].index
                region_list = []
                tap_index_list = []
                for row in fail_rows:
                    # Save the tap's index for later reference:
                    tap_index_list.append(row)
                    # Find the resulting failure region:
                    ptap_poly = elem.hasDemand['wind pressure']['external'].loc[row]['Tap Polygon']
                    if zone_flag:
                        if isinstance(elem, Roof):
                            if ptap_poly.intersects(elem.hasGeometry['2D Geometry']['local']):
                                region_list.append(ptap_poly.intersection(elem.hasGeometry['2D Geometry']['local']))
                            else:
                                region_list.append(ptap_poly)  # Pressure tap is within the element's 2D geometry
                        else:
                            # Use line geometries to find each element's corresponding failure region:
                            xp, yp, zp = [], [], []
                            for i in list(ptap_poly.exterior.coords):
                                xp.append(i[0])
                                yp.append(i[1])
                                zp.append(i[2])
                            # Keep only unique (x, y) pairs:
                            tap_coords_list = []
                            for j in range(0, len(xp)):
                                if (xp[j], yp[j]) not in tap_coords_list:
                                    tap_coords_list.append((xp[j], yp[j]))
                            pline = LineString(tap_coords_list)
                            if pline.intersects(elem.hasGeometry['1D Geometry']['local']):
                                # Find the intersection:
                                iline = pline.intersection(elem.hasGeometry['1D Geometry']['local'])
                                if isinstance(iline, Point):
                                    xl, yl = elem.hasGeometry['1D Geometry']['local'].xy
                                    dist1 = Point(xl[0], yl[0]).distance(iline)
                                    dist2 = Point(xl[1], yl[1]).distance(iline)
                                    if dist1 < dist2:
                                        # Create failure region using iline point and closest element point:
                                        new_poly = Polygon([(iline.x, iline.y, min(zp)), (xl[0], yl[0], min(zp)), (xl[0], yl[0], max(zp)), (iline.x, iline.y, max(zp)), (iline.x, iline.y, min(zp))])
                                    else:
                                        new_poly = Polygon([(iline.x, iline.y, min(zp)), (xl[1], yl[1], min(zp)), (xl[1], yl[1], max(zp)), (iline.x, iline.y, max(zp)), (iline.x, iline.y, min(zp))])
                                    region_list.append(new_poly)
                                elif isinstance(iline, MultiPoint):
                                    new_poly = Polygon(
                                        [(iline[0].x, iline[0].y, min(zp)), (iline[1].x, iline[1].y, min(zp)), (iline[1].x, iline[1].y, max(zp)),
                                         (iline[0].x, iline[0].y, max(zp)), (iline[0].x, iline[0].y, min(zp))])
                                    region_list.append(new_poly)
                                else:
                                    try:
                                        x_iline = iline.xy[0]
                                        y_iline = iline.xy[1]
                                    except NotImplementedError:
                                        # The output geometry is a multistring:
                                        x_iline, y_iline = [], []
                                        lines = list(iline.geoms)
                                        for l in lines:
                                            x_iline += l.xy[0]
                                            y_iline += l.xy[1]
                                    # Now figure out z-range:
                                    zw = []
                                    for w in list(elem.hasGeometry['3D Geometry']['local'].exterior.coords):
                                        zw.append(w[2])
                                    if max(zw) > max(zp):
                                        zmax = max(zp)
                                    else:
                                        zmax = max(zw)
                                    if min(zp) > min(zw):
                                        zmin = min(zp)
                                    else:
                                        zmin = min(zw)
                                    # Create intersection's geometry:
                                    pcoords_list = []
                                    # Add zmin points first:
                                    for k in range(0, len(x_iline)):
                                        pcoords_list.append((x_iline[k], y_iline[k], zmin))
                                    # Now add zmax points:
                                    for k in range(0, len(x_iline)):
                                        pcoords_list.append((x_iline[-1 - k], y_iline[-1 - k], zmax))
                                    new_poly = Polygon(pcoords_list)
                                    region_list.append(new_poly)
                            elif ptap_poly.within(elem.hasGeometry['3D Geometry']['local']):
                                region_list.append(ptap_poly)
                            else:
                                pass
                    else:
                        # Grab the element's entire 2D polygon:
                        region_list.append(elem.hasGeometry['2D Geometry']['local'])
                # Add failure information to element's dataframe:
                elem_fail.iat[elem_fail_tidx, rcol] = elem_fail.iat[elem_fail_tidx, rcol] + region_list
                elem_fail.iat[elem_fail_tidx, fcol] = True
                elem_fail.iat[elem_fail_tidx, tap_col] = elem_fail.iat[elem_fail_tidx, tap_col] + tap_index_list
    # Add the data to the element's data model:
    elem.hasFailure['wind pressure'] = elem_fail.loc[elem_fail['fail'] == True]


def wbd_ftree(target_bldg, source_bldg, df_fail_source, df_site_debris, wind_speed, wind_direction, length_unit, plot_flag):
    # Plot the failure regions on roof if necessary:
    if plot_flag:
        fig, ax = plt.subplots()
        for idx in df_fail_source['fail regions'].index.to_list():
            xp, yp = df_fail_source['fail regions'][idx].exterior.xy
            ax.plot(xp, yp, 'r')
    else:
        pass
    # 1) Debris generation: Depends on distance to source building and element impact resistance
    # Get element impact resistance from target building:
    elem_impact_resistance = target_bldg.adjacentElement['Walls'][0].hasCapacity['debris impact']
    source_roof_geometry = source_bldg.hasGeometry['Footprint']['reference cartesian'].minimum_rotated_rectangle
    if len(df_fail_source.index.to_list()) > 0:  # Make sure there is damage to begin:
        target_bldg_footprint = target_bldg.hasGeometry['Footprint']['local']
        # Query damage to roof elements in source bldg:
        potential_wbd = df_fail_source[df_fail_source['roof element'] == True]
        for idx in potential_wbd.index.to_list():
            fail_region = potential_wbd['fail regions'][idx]
            debris_name = potential_wbd['fail elements'][idx].hasType
            df_debris_char = df_site_debris.loc[df_site_debris['debris name'] == debris_name]
            # Get number of debris object and shift fail_region to global CRS for trajectory/hit calculations:
            num_dobjects, gcrs_fail_region = get_num_dobjects(fail_region, target_bldg_footprint, source_roof_geometry,
                                                              wind_speed, elem_impact_resistance,
                                                              c=df_debris_char['c'].values[0],
                                                              debris_mass=df_debris_char['debris mass'].values[0],
                                                              momentum_flag=True, length_unit='ft')
            if plot_flag:
                xfail, yfail = gcrs_fail_region.exterior.xy
                ax.plot(xfail, yfail, 'b')
            else:
                pass
            # 2) Calculate the debris trajectory (in gcrs):
            model_input = df_debris_char.loc[df_debris_char.index[0]].to_dict()
            if num_dobjects > 0:
                # Keep track of trajectories that hit the building:
                hit_traj_list = []
                for n in range(0, num_dobjects):
                    alongwind_dist, acrosswind_dist = get_trajectory(model_input, wind_speed, length_unit,
                                                                     mcs_flag=False)
                    traj_line = get_traj_line(alongwind_dist[0], acrosswind_dist[0], wind_direction,
                                              origin_pt=gcrs_fail_region.centroid)
                    # Check if this debris object will hit the building:
                    if traj_line.intersects(target_bldg_footprint):
                        hit_traj_list.append(traj_line)
                    else:
                        pass
                    # Add plotting if needed:
                    if plot_flag:
                        xt, yt = traj_line.xy
                        ax.plot(xt, yt, 'b', linestyle='dashed')
                        ax.scatter(gcrs_fail_region.centroid.x, gcrs_fail_region.centroid.y)
                if plot_flag:
                    # Add source and target building geometries:
                    xsource_rect, ysource_rect = source_roof_geometry.exterior.xy
                    ax.plot(xsource_rect, ysource_rect, 'k')
                    xtarget, ytarget = target_bldg_footprint.exterior.xy
                    ax.plot(xtarget, ytarget, 'r')
                    # Plot the directional debris region:
                    dir_debris_region = df_site_debris.loc[df_site_debris['debris name']==source_bldg.adjacentElement['Roof'][0].hasCover, 'directional debris region'].values[0]
                    xdir, ydir = dir_debris_region.exterior.xy
                    ax.plot(xdir, ydir, linestyle='dotted', color='orange')
                # 3) Now find what elements in target building are affected by impact:
                for hit_traj in hit_traj_list:
                    wall_list = []
                    for wall in target_bldg.adjacentElements['Walls']:
                        # Pull the wall's line geometry:
                        wall_line = wall.hasGeometry['1D Geometry']['local']
                        if hit_traj.intersects(wall_line):
                            wall_list.append(wall)
                        else:
                            pass
                # Find out which element got damaged:
                prob_hit = uniform.rvs(size=len(wall_list))
                max_idx = np.where(prob_hit == max(prob_hit))
                # Update the wall's hasFailure attribute:
                wall_list[max_idx].hasFailure['debris impact'] = True
            else:
                pass
    else:
        pass
    return target_bldg, wall_list

def wind_pressure_ftree(bldg, wind_speed, facade_flag):
    # For each building:
    # 1) Sample pressure coefficients and calculate wind pressure:
    df_bldg_cps = bldg.hasDemand['wind pressure']['external']
    # Sample from gaussian distribution with mean = mean cp and std dev = 0.3
    df_bldg_cps['Sample Cp'] = df_bldg_cps['Mean Cp'].apply(lambda x: norm.rvs(x, 0.3))
    # Quantify pressures:
    pressure_calc = PressureCalc()
    df_bldg_cps['Pressure'] = df_bldg_cps['Sample Cp'].apply(lambda j: pressure_calc.get_tpu_pressure(wind_speed, j, 'B', bldg.hasGeometry['Height'], 'mph'))
    # 2) Loop through building envelope components, sample capacities, and check for breach:
    fail_elements = []
    fail_regions = []
    for key in bldg.adjacentElement:
        if key == 'Floor':
            pass
        elif key == 'Roof':
            if len(bldg.adjacentElement[key][0].hasSubElement['cover']) > 0:
                for elem in bldg.adjacentElement[key][0].hasSubElement['cover']:
                    # Query tap numbers, pressures, and intersecting areas:
                    tap_nums = elem.hasDemand['wind pressure']['external']['tap number']
                    tap_pressures = df_bldg_cps['Pressure'][tap_nums]
                    tap_areas = elem.hasDemand['wind pressure']['external']['intersecting area']
                    if type(tap_areas) == list:
                        tap_areas = np.array(tap_areas)
                    else:
                        pass
                    # Sample component capacity:
                    idx = 0
                    for p in tap_pressures.index.to_list():
                        fail_flag = False
                        if tap_pressures.loc[p] < 0:
                            elem_capacity = elem.hasCapacity['wind pressure']['external']['negative']
                            if elem_capacity > tap_pressures.loc[p]:
                                fail_flag = True
                            else:
                                pass
                        else:
                            elem_capacity = elem.hasCapacity['wind pressure']['external']['positive']
                            if elem_capacity < tap_pressures.loc[p]:
                                fail_flag = True
                            else:
                                pass
                        # Add failure data:
                        if fail_flag:
                            fail_regions.append(tap_areas[idx])
                            elem.hasFailure['wind pressure'] = True
                            fail_elements.append(elem)
                        else:
                            pass
                        idx += 1
            else:
                pass
        elif key == 'Walls':
            if facade_flag:
                for elem in bldg.adjacentElement[key]:
                    # Query tap numbers, pressures, and intersecting areas:
                    tap_nums = elem.hasDemand['wind pressure']['external']['tap number']
                    tap_pressures = df_bldg_cps['Pressure'][tap_nums]
                    tap_areas = elem.hasDemand['wind pressure']['external']['intersecting area']
                    if type(tap_areas) == list:
                        tap_areas = np.array(tap_areas)
                    else:
                        pass
                    #elem_loading = sum(tap_pressures*tap_areas)/elem.hasGeometry['2D Geometry']['local'].area
                    # Sample component capacity:
                    elem_capacity = elem.hasCapacity['wind pressure']['external']['positive']
                    idx = 0
                    if tap_pressures.loc[p] < 0:
                        elem_capacity = elem.hasCapacity['wind pressure']['external']['negative']
                        if elem_capacity > tap_pressures.loc[p]:
                            fail_flag = True
                        else:
                            pass
                    else:
                        elem_capacity = elem.hasCapacity['wind pressure']['external']['positive']
                        if elem_capacity < tap_pressures.loc[p]:
                            fail_flag = True
                        else:
                            pass
                    # Add failure data:
                    if fail_flag:
                        fail_regions.append(tap_areas[idx])
                        elem.hasFailure['wind pressure'] = True
                        fail_elements.append(elem)
                    else:
                        pass
                    idx += 1
            else:
                pass
    # Return a DataFrame with all failed elements and regions:
    df_fail = pd.DataFrame({'fail elements': fail_elements, 'fail regions': fail_regions})
    df_fail['roof element'] = df_fail['fail elements'].apply(lambda x: isinstance(x, Roof))
    return df_fail


def facade_wind_fault_tree(bldg):
    # Loop through facade elements by story:
    fig = plt.figure()
    ax = plt.axes(projection='3d')
    for story in bldg.hasStory:
        undamaged_elem = []
        ext_pressures = []
        breached_elem = []
        for key in story.adjacentElement:
            if key == 'Walls' or key == 'Windows':
                for elem in story.adjacentElement[key]:
                    wall_pts = list(elem.hasGeometry['3D Geometry']['local'].exterior.coords)
                    xw, yw, zw = [], [], []
                    for w in wall_pts:
                        xw.append(w[0])
                        yw.append(w[1])
                        zw.append(w[2])
                    xw = np.array(xw)/3.281
                    yw = np.array(yw) / 3.281
                    zw = np.array(zw)/3.281
                    # Demand vs. capacity checks:
                    for p in elem.hasDemand['wind pressure']['external']:
                        if p > elem.hasCapacity['wind pressure']['external']['positive']:
                            elem.hasFailure['wind pressure'] = True
                            break
                        elif p < elem.hasCapacity['wind pressure']['external']['negative']:
                            elem.hasFailure['wind pressure'] = True
                            break
                        else:
                            pass
                    if elem.hasFailure['wind pressure']:
                        for p in elem.hasDemand['wind pressure']['external']:
                            ext_pressures.append(p)
                            breached_elem.append(elem)
                    else:
                        undamaged_elem.append(elem)
                        ax.plot(xw, yw, zw, 'k', zorder=2)
            else:
                pass
        for b in breached_elem:
            wall_pts = list(b.hasGeometry['3D Geometry']['local'].exterior.coords)
            xw, yw, zw = [], [], []
            for w in wall_pts:
                xw.append(w[0])
                yw.append(w[1])
                zw.append(w[2])
            xw = np.array(xw) / 3.281
            yw = np.array(yw) / 3.281
            zw = np.array(zw) / 3.281
            ax.plot(xw, yw, zw, 'r', zorder=1)
        if len(ext_pressures) > 0:
            # Calculate the new internal pressure:
            int_pressure = np.array(ext_pressures).mean()
            print('New story internal pressure:')
            print(int_pressure/0.020885)
            # Recalculate wind pressures for each undamaged component:
            for u in undamaged_elem:
                u.hasDemand['wind pressure']['internal'] = int_pressure
                u.hasDemand['wind pressure']['total'] = u.hasDemand['wind pressure']['external'] + int_pressure
        # Plot the roof:
        xr, yr = bldg.adjacentElement['Roof'][0].hasGeometry['2D Geometry']['local'].exterior.xy
        ax.plot(np.array(xr)/ 3.281, np.array(yr)/ 3.281, np.ones(len(xr))*bldg.hasGeometry['Height']/ 3.281, 'k')
        # Make the panes transparent:
        ax.w_xaxis.set_pane_color((1.0, 1.0, 1.0, 1.0))
        ax.w_yaxis.set_pane_color((1.0, 1.0, 1.0, 1.0))
        ax.w_zaxis.set_pane_color((1.0, 1.0, 1.0, 1.0))
        # Make the grids transparent:
        ax.xaxis._axinfo["grid"]['color'] = (1, 1, 1, 0)
        ax.yaxis._axinfo["grid"]['color'] = (1, 1, 1, 0)
        ax.zaxis._axinfo["grid"]['color'] = (1, 1, 1, 0)
        # Plot labels
        ax.set_xlabel('x [m]', fontsize=14, labelpad=10)
        ax.set_ylabel('y [m]', fontsize=14, labelpad=10)
        ax.set_zlabel('z [m]', fontsize=14, labelpad=10)
        # Set label styles:
        ax.set_zticks(np.arange(0, 20, 4))
        ax.set_yticks(np.arange(-20, 30, 10))
        ax.set_xticks(np.arange(-20, 30, 10))
        ax.xaxis.set_tick_params(labelsize=14)
        ax.yaxis.set_tick_params(labelsize=14)
        ax.zaxis.set_tick_params(labelsize=14)
    ax.legend(labels=['breached', 'not breached'])
    plt.show()

# # Code for data model CQ:
# # Set positive and negative capacities per wall element:
# gcpi = 0.18
# rho = 1.225
# avg_factor = (1/1.52)**2
# for wall in test.adjacentElement['Walls']:
#     wall.hasCapacity['wind pressure']['external']['positive'] = 400*0.020885
#     wall.hasCapacity['wind pressure']['external']['negative'] = -600 * 0.020885
#     wall.hasDemand['wind pressure']['internal'] = (0.5*rho*((wind_speed/2.237)**2)*gcpi)* 0.020885
#     wall.hasDemand['wind pressure']['external'] = wall.hasDemand['wind pressure']['external']['Pressure']
# print(wall.hasDemand['wind pressure']['internal'])
# facade_wind_fault_tree(test)
# ftree_initial(test)
#get_voronoi(test)
#pressure_ftree(test, zone_flag=True, time_flag=True)
