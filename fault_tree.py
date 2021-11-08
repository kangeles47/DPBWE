import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from shapely.geometry import Polygon, Point, LineString
from shapely.ops import nearest_points
from scipy.spatial import Voronoi, voronoi_plot_2d
from time_history_tpu_pressures import calc_tpu_pressures, convert_to_tpu_wdir
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


def generate_pressure_loading(bldg, wind_speed, wind_direction, tpu_flag, csv_flag):
    # Populate envelope pressures:
    if tpu_flag:
        if csv_flag:
            df_tpu_pressures = pd.read_csv('D:/Users/Karen/Documents/GitHub/DPBWE/SampleTHPressureOutput.csv')
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
            key = 'local'
            # Find TPU wind pressures:
            df_tpu_pressures = calc_tpu_pressures(bldg, key, tpu_wdir, wind_speed)
        # Save the pressure loading to the Building object:
        bldg.hasDemand['wind pressure']['external'] = df_tpu_pressures
        # Map pressures to specific elements on building envelope:
        # Start with facade components:
        roof_indices = df_tpu_pressures.loc[df_tpu_pressures['Surface Number'] == 5].index
        tcols = [col for col in df_tpu_pressures.columns if 'pt' in col]
        df_facade = df_tpu_pressures.drop(roof_indices).drop(tcols, axis=1)
        # Add tap polygon geometries:
        df_facade = get_facade_mesh(bldg, df_facade)
        # Add empty DataFrames to facade elements:
        for wall in bldg.adjacentElement['Walls']:
            wall.hasDemand['wind pressure']['external'] = []
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
                    ptap_loc = df_tpu_pressures['Real Life Location'][idx]
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
        # Map pressures onto roof elements:
        # Assign the entire roof DataFrame to main roof element:
        bldg.adjacentElement['Roof'][0].hasDemand['wind pressure']['external'] = df_roof
        # First get the voronoi diagram (pressure tap tributary areas):
        get_voronoi(bldg)
        if len(bldg.adjacentElement['Roof'][0].hasSubElement['cover']) == 0:
            # Assign the entire roof DataFrame to main roof element:
            bldg.adjacentElement['Roof'][0].hasDemand['wind pressure']['external'] = df_roof
        else:
            for subelem in bldg.adjacentElement['Roof'][0].hasSubElement['cover']:
                subelem.hasDemand['wind pressure']['external'] = []
            # Map pressures to roof subelements
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
        # Generate minimal DataFrames for each element:
        for wall in bldg.adjacentElement['Walls']:
            wall.hasDemand['wind pressure']['external'] = df_facade.loc[wall.hasDemand['wind pressure']['external']]
        if len(bldg.adjacentElement['Roof'][0].hasSubElement['cover']) == 0:
            pass
        else:
            for subelem in bldg.adjacentElement['Roof'][0].hasSubElement['cover']:
                subelem.hasDemand['wind pressure']['external'] = df_roof.loc[subelem.hasDemand['wind pressure']['external']]


def ftree(bldg, zone_flag):
    tcols = [col for col in bldg.hasDemand['wind pressure']['external'].columns if 'pt' in col]
    # Loop through building envelope components and check for breach:
    fail_elements = []
    for key in bldg.adjacentElement:
        if key == 'Floor':
            pass
        elif key == 'Roof':
            if len(bldg.adjacentElement[key][0].hasSubElement['cover']) > 0:
                roof_fail = pd.DataFrame({'time': tcols, 'area': np.zeros(len(tcols))})
                for elem in bldg.adjacentElement[key][0].hasSubElement['cover']:
                    elem_fail = pd.DataFrame({'time': tcols, 'fail': [False for col in tcols], 'region': [[] for col in tcols], 'tap index': [[] for col in tcols]})
                    fcol = np.where(elem_fail.columns == 'fail')[0][0]
                    rcol = np.where(elem_fail.columns == 'region')[0][0]
                    tap_col = np.where(elem_fail.columns == 'tap index')[0][0]
                    try:
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
                        tneg_fcol = tneg_check.loc[tneg_check==True].index
                        tpos_fcol = tpos_check.loc[tpos_check==True].index
                        # Grab subsets of each dataframe to conduct query:
                        df_neg = df_neg[tneg_fcol]
                        df_pos = df_pos[tpos_fcol]
                        # print('columns in negative with true value:' + str(len(df_neg.columns)))
                        # print('columns in positive with true value:' + str(len(df_pos.columns)))
                        # Before proceeding, get rid of any bigger data items we no longer need:
                        del pressure_demand, tneg_check, tpos_check, tneg_fcol, tpos_fcol
                        # Grab failed regions and record pressure tap indices:
                        df_list = [df_neg, df_pos]
                        for d in range(0, len(df_list)):
                            df_query = df_list[d]
                            if len(df_query) > 0:
                                for col in df_query.columns:
                                    elem_fail_tidx = elem_fail.loc[elem_fail['time']==col].index[0]
                                    fail_rows = df_query.loc[df_query[col]==True].index
                                    region_list = []
                                    tap_index_list = []
                                    for row in fail_rows:
                                        # Save the tap's index for later reference:
                                        tap_index_list.append(row)
                                        # Find the resulting failure region:
                                        ptap_poly = elem.hasDemand['wind pressure']['external'].loc[row]['Tap Polygon']
                                        if zone_flag:
                                            if ptap_poly.intersects(elem.hasGeometry['2D Geometry']['local']):
                                                region_list.append(ptap_poly.intersection(elem.hasGeometry['2D Geometry']['local']))
                                            else:
                                                region_list.append(ptap_poly)  # Pressure tap is within the element's 2D geometry
                                        else:
                                            # Grab the element's entire 2D polygon:
                                            region_list.append(elem.hasGeometry['2D Geometry']['local'])
                                    # Add failure information to element's dataframe:
                                    elem_fail.iat[elem_fail_tidx, rcol] = elem_fail.iat[elem_fail_tidx, rcol] + region_list
                                    elem_fail.iat[elem_fail_tidx, fcol] = True
                                    elem_fail.iat[elem_fail_tidx, tap_col] = elem_fail.iat[elem_fail_tidx, tap_col] + tap_index_list
                                    # Add failure area to overall roof failure information:
                                    for r in region_list:
                                        roof_fail.iat[elem_fail_tidx, 1] += r.area
                            else:
                                pass
                        # Add the data to the element's data model:
                        elem.hasFailure['wind pressure'] = elem_fail.loc[elem_fail['fail']==True]
                    except TypeError:
                        # Demand is a single value:
                        if elem.hasDemand['wind pressure']['external'] >= elem.hasCapacity['wind pressure']['external']:
                            pass
                # Figure out when maximum response occurred:
                max_idx = roof_fail.loc[roof_fail['area'] == max(roof_fail['area'])].index[0]
                max_time = roof_fail['time'][max_idx]
                # Loop through elements and retain only data for max response:
                for elem in bldg.adjacentElement[key][0].hasSubElement['cover']:
                    max_idx_elem = elem.hasFailure['wind pressure'].loc[elem.hasFailure['wind pressure']['time']==max_time].index
                    if len(max_idx_elem) > 0:
                        elem.hasFailure['wind pressure'] = elem.hasFailure['wind pressure'].loc[max_idx_elem[0]]
                        for r in elem.hasFailure['wind pressure']['region']:
                            xr, yr = r.exterior.xy
                            plt.plot(xr, yr, 'r')
                    else:
                        elem.hasFailure['wind pressure'] = False
                    # Plot element geometries:
                    xe, ye = elem.hasGeometry['2D Geometry']['local'].exterior.xy
                    plt.plot(xe, ye, 'g')
                x, y = bldg.adjacentElement['Roof'][0].hasGeometry['2D Geometry']['local'].exterior.xy
                plt.plot(x, y, 'k', linestyle='dashed')
                plt.show()
            else:
                pass
        elif key == 'Walls':
            pass
            # for elem in bldg.adjacentElement[key]:
            #     try:
            #         for row in elem.hasDemand['wind pressure']['external'].index:
            #             pressure_demand = elem.hasDemand['wind pressure']['external'].iloc[row]['Pressure']
            #             if pressure_demand < 0 and pressure_demand < elem.hasCapacity['wind pressure']['total']['negative']:
            #                 elem.hasFailure['wind pressure'] = True
            #             elif pressure_demand > 0 and pressure_demand > elem.hasCapacity['wind pressure']['total']['positive']:
            #                 elem.hasFailure['wind pressure'] = True
            #     except TypeError:
            #         # Demand is a single value:
            #         if elem.hasDemand['wind pressure']['external'] >= elem.hasCapacity['wind pressure']['external']:
            #             pass
            #     if elem.hasFailure['wind pressure']:
            #         fail_elements.append(elem)
            #     else:
            #         pass
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
    for idx in bldg.adjacentElement['Roof'][0].hasDemand['wind pressure']['external'].index:
        ptap_loc = bldg.adjacentElement['Roof'][0].hasDemand['wind pressure']['external'].loc[idx]['Real Life Location']
        coord_list.append((ptap_loc.x, ptap_loc.y))
    # if len(bldg.adjacentElement['Roof'][0].hasSubElement['cover']) == 0:
    #     # Find polygons for the entire roof surface:
    #     for idx in bldg.adjacentElement['Roof'][0].hasDemand['wind pressure']['external'].index:
    #         ptap_loc = bldg.adjacentElement['Roof'][0].hasDemand['wind pressure']['external'].loc[idx]['Real Life Location']
    #         coord_list.append((ptap_loc.x, ptap_loc.y))
    # else:
    #     for elem in bldg.adjacentElement['Roof'][0].hasSubElement['cover']:
    #         # Use pressure tap locations as input coordinate list:
    #         for idx in elem.hasDemand['wind pressure']['external'].index:
    #             ptap_loc = elem.hasDemand['wind pressure']['external'].loc[idx]['Real Life Location']
    #             coord_list.append((ptap_loc.x, ptap_loc.y))
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
    # for poly in poly_list:
    #     if isinstance(poly, Polygon):
    #         xpoly, ypoly = poly.exterior.xy
    #         plt.plot(xpoly, ypoly, 'r')
    # x, y = bldg.adjacentElement['Roof'][0].hasGeometry['2D Geometry']['local'].exterior.xy
    # plt.plot(x,y)
    # plt.show()
    # Loop through each pressure tap and add its corresponding polygon:
    tap_poly_list = []
    no_poly_idx = []
    for idx in bldg.adjacentElement['Roof'][0].hasDemand['wind pressure']['external'].index:
        ptap_loc = bldg.adjacentElement['Roof'][0].hasDemand['wind pressure']['external'].loc[idx]['Real Life Location']
        poly_flag = False
        for poly in poly_list:
            if isinstance(poly, Polygon):
                if Point(ptap_loc.x, ptap_loc.y).intersects(poly) or Point(ptap_loc.x, ptap_loc.y).within(poly):
                    tap_poly_list.append(poly)
                    poly_flag = True
                    break
        if not poly_flag:
            # Save the polygon:
            tap_poly_list.append(None)
            no_poly_idx.append(idx)
    bldg.adjacentElement['Roof'][0].hasDemand['wind pressure']['external']['Tap Polygon'] = tap_poly_list
    # Find which polygons were not mapped:
    no_map_poly = []
    for poly in poly_list:
        if isinstance(poly, Polygon):
            if poly in tap_poly_list:
                pass
            else:
                no_map_poly.append(poly)
    # Buffer points without polygons to find corresponding geometry:
    df_sub = bldg.adjacentElement['Roof'][0].hasDemand['wind pressure']['external'].loc[no_poly_idx]
    for idx in df_sub.index:
        ptap_loc = df_sub.loc[idx]['Real Life Location']
        bpt = Point(ptap_loc.x, ptap_loc.y).buffer(distance=3)
        for no_map in no_map_poly:
            if bpt.intersects(no_map):
                bldg.adjacentElement['Roof'][0].hasDemand['wind pressure']['external'].at[idx, 'Tap Polygon'] = no_map
                break
        else:
            pass
    for idx in bldg.adjacentElement['Roof'][0].hasDemand['wind pressure']['external'].index:
        try:
            xpoly, ypoly = bldg.adjacentElement['Roof'][0].hasDemand['wind pressure']['external'].loc[idx]['Tap Polygon'].exterior.xy
            plt.plot(xpoly, ypoly, 'r')
        except AttributeError:
            bldg.adjacentElement['Roof'][0].hasDemand['wind pressure']['external'] = bldg.adjacentElement['Roof'][0].hasDemand['wind pressure']['external'].drop(idx)
    plt.show()
    # for idx in bldg.adjacentElement['Roof'][0].hasDemand['wind pressure']['external'].index:
    #     ptap_loc = bldg.adjacentElement['Roof'][0].hasDemand['wind pressure']['external'].loc[idx]['Real Life Location']
    #     new_arr = np.array([ptap_loc.x, ptap_loc.y])
    #     vpoint_idx = np.where(vor.points == new_arr)[0][0]
    #     vregion_idx = vor.point_region[vpoint_idx]
    #     tap_poly_list.append(poly_list[vregion_idx])
    #bldg.adjacentElement['Roof'][0].hasDemand['wind pressure']['external']['Tap Polygon'] = tap_poly_list
    # if len(bldg.adjacentElement['Roof'][0].hasSubElement['cover']) == 0:
    #     pass
    # else:
    #     # Loop through pressure taps for each element and add their corresponding polygons:
    #     for elem in bldg.adjacentElement['Roof'][0].hasSubElement['cover']:
    #         # Use pressure tap locations as input coordinate list:
    #         tap_poly_list = []
    #         for idx in elem.hasDemand['wind pressure']['external'].index:
    #             ptap_loc = elem.hasDemand['wind pressure']['external'].loc[idx]['Real Life Location']
    #             new_arr = np.array([ptap_loc.x, ptap_loc.y])
    #             vpoint_idx = np.where(vor.points==new_arr)[0][0]
    #             vregion_idx = vor.point_region[vpoint_idx]
    #             tap_poly_list.append(poly_list[vregion_idx])
    #         elem.hasDemand['wind pressure']['external']['Tap Polygon'] = tap_poly_list
    #a = 0


def get_facade_mesh(bldg, df_facade):
    # Collect (x, y) tap locations around bldg perimeter:
    perim_points = []
    xp, yp = [], []
    zlist = []
    for idx in df_facade.index:
        ptap_loc = df_facade['Real Life Location'][idx]
        zlist.append(ptap_loc.z)
        #zlist.append(round(ptap_loc.z, 6))
        if ptap_loc.z == 0:
            perim_points.append(ptap_loc)
            xp.append(ptap_loc.x)
            yp.append(ptap_loc.y)
    # Order z locations:
    zlist_order = np.sort(np.array(list(set(zlist))))
    # Order points according to building footprint geometry:
    plist = []
    x, y = bldg.hasGeometry['Footprint']['local'].exterior.xy
    for i in range(0, len(x)-1):
        max_x = max(x[i], x[i+1])
        min_x = min(x[i], x[i+1])
        max_y = max(y[i], y[i+1])
        min_y = min(y[i], y[i+1])
        point_info = {'points': [], 'distance': []}
        for p in perim_points:
            if min_x <= p.x <= max_x and min_y <= p.y <= max_y:
                point_info['points'].append(p)
                # Calculate the distance from this point to origin point:
                origin_dist = Point(x[i], y[i]).distance(p)
                point_info['distance'].append(origin_dist)
        dist_sort = np.sort(np.array(point_info['distance']))
        for d in dist_sort:
            pidx = np.where(point_info['distance']==d)[0][0]
            plist.append(point_info['points'][pidx])
    # Create tap geometries:
    tap_poly_list = []
    for idx in df_facade.index:
        ptap_loc = df_facade['Real Life Location'][idx]
        zidx = np.where(zlist_order==ptap_loc.z)[0][0]
        if ptap_loc.z == 0:
            zmin = ptap_loc.z
        else:
            zmin = zlist_order[zidx-1] + (ptap_loc.z-zlist_order[zidx-1])/2
        if ptap_loc.z != max(zlist_order):
            zmax = ptap_loc.z + (zlist_order[zidx+1] - ptap_loc.z)/2
        else:
            zmax = ptap_loc.z
        # Find matching (x, y) for this point:
        poly_list = []
        for p in range(0, len(plist)):
            if ptap_loc.x == plist[p].x and ptap_loc.y == plist[p].y:
                poly_list.append((ptap_loc.x, ptap_loc.y, zmin))
                poly_list.append((plist[p-1].x, plist[p-1].y, zmin))
                poly_list.append((plist[p-1].x, plist[p-1].y, zmax))
                poly_list.append((ptap_loc.x, ptap_loc.y, zmax))
                if p == len(plist)-1:
                    poly_list.append((plist[0].x, plist[0].y, zmax))
                    poly_list.append((plist[0].x, plist[0].y, zmin))
                else:
                    poly_list.append((plist[p+1].x, plist[p+1].y, zmax))
                    poly_list.append((plist[p+1].x, plist[p+1].y, zmin))
                poly_list.append((ptap_loc.x, ptap_loc.y, zmin))
                tap_poly_list.append(Polygon(poly_list))
                break
            else:
                pass
    # Add the polygons to the input DataFrame:
    df_facade['Tap Polygon'] = tap_poly_list
    fig = plt.figure()
    ax = plt.axes(projection='3d')
    for idx in df_facade.index:
        ptap_loc = df_facade['Real Life Location'][idx]
        ax.scatter(ptap_loc.x, ptap_loc.y, ptap_loc.z)
        coords_list = df_facade['Tap Polygon'][idx].exterior.coords
        xpoly, ypoly, zpoly = [], [], []
        for c in coords_list:
            xpoly.append(c[0])
            ypoly.append(c[1])
            zpoly.append(c[2])
        ax.plot(xpoly, ypoly, zpoly)
    plt.show()
    return df_facade

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
generate_pressure_loading(test, wind_speed, wind_direction, tpu_flag=True, csv_flag=True)
#get_voronoi(test)
ftree(test, zone_flag=True)
