import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from shapely.geometry import Polygon, Point, LineString, MultiPoint
from scipy.stats import norm, uniform
from tpu_pressures import calc_tpu_pressures, convert_to_tpu_wdir
from bldg_code import ASCE7
from OBDM.element import Roof, Wall
from code_pressures import PressureCalc
from Wind_WBD_Effects_Simulation.get_debris import get_trajectory, get_num_dobjects, get_traj_line


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


def wbd_ftree(target_bldg, source_bldg, df_fail_source, df_site_debris, pressure_fail_target, wind_speed, wind_direction, length_unit, plot_flag, parcel_flag, rng):
    """
    A function to conduct the WBD portion of the fault tree analysis
    :param target_bldg: (Building object) describing the target building. Should have footprint geometry and wall impact
                        resistance (Wall.hasCapacity). Wall objects should also be populated with linear and planar
                        geometries
    :param source_bldg: (Building object) describing the source building. Should have footprint geometry 'reference
                        Cartesian' (i.e., relative to target building)
    :param df_fail_source: (Pandas DataFrame) containing description of all roof failure occurrences for source building
    :param df_site_debris: (Pandas DataFrame) containing description of site debris characteristics (e.g., debris types,
                            mass/unit area, directional debris region, etc.)
    :param pressure_fail_target: (List) containing all walls that have already experienced pressure-related failure
    :param wind_speed: The wind speed used to quantify debris trajectories. Simplified analysis allows for this to be
                        wind speed at source building's mean roof height (in corresponding site conditions)
    :param wind_direction: (Int) The actual (real-life) wind direction.
    :param length_unit: The length unit for the wind speed, set to 'mi' or 'm'
    :param plot_flag: (Boolean) True if you want summary plots showing source building, target building, and debris
                    trajectories
    :param parcel_flag: (Boolean) True if the target's Building object does not contain information regarding component
                        sizing.
    :param rng: (From np.random.default_rng(seed)) Random number generator object
    :return: debris_dict: (Dict) with keys = flight path, fail element, fail region, values= list of Shapely
            LineStrings, list of element objects, list of Shapely polygons
    """
    # Plot the failure regions on roof if necessary:
    if plot_flag:
        fig, ax = plt.subplots()
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
        # Create dictionary to hold data:
        debris_dict = {'flight path': [], 'fail element': [], 'fail region': []}
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
            # Save wbd information:
            debris_dict['fail region'].append(gcrs_fail_region)
            if plot_flag:
                xfail, yfail = gcrs_fail_region.exterior.xy
                ax.plot(np.array(xfail)/3.281, np.array(yfail)/3.281, 'b')
                # Add source and target building geometries:
                xsource_rect, ysource_rect = source_roof_geometry.exterior.xy
                ax.plot(np.array(xsource_rect)/3.281, np.array(ysource_rect)/3.281, 'k')
                xtarget, ytarget = target_bldg_footprint.exterior.xy
                ax.plot(np.array(xtarget)/3.281, np.array(ytarget)/3.281, 'r')
                # Plot the directional debris region:
                dir_debris_region = df_site_debris.loc[df_site_debris['debris name']==source_bldg.adjacentElement['Roof'][0].hasCover, 'directional debris region'].values[0]
                xdir, ydir = dir_debris_region.exterior.xy
                ax.plot(np.array(xdir)/3.281, np.array(ydir)/3.281, color='orange', linewidth=2)
            else:
                pass
            # 2) Calculate the debris trajectory (in gcrs):
            model_input = df_debris_char.loc[df_debris_char.index[0]].to_dict()
            if num_dobjects > 0:
                # Keep track of trajectories that hit the building:
                hit_traj_list = []
                all_traj_list = []
                for n in range(0, num_dobjects):
                    alongwind_dist, acrosswind_dist = get_trajectory(model_input, wind_speed, length_unit,
                                                                     mcs_flag=False, rng=rng)
                    traj_line = get_traj_line(alongwind_dist[0], acrosswind_dist[0], wind_direction,
                                              origin_pt=gcrs_fail_region.centroid)
                    all_traj_list.append(traj_line)
                    # Check if this debris object will hit the building:
                    if traj_line.intersects(target_bldg_footprint):
                        hit_traj_list.append(traj_line)
                    else:
                        pass
                    # Add plotting if needed:
                    if plot_flag:
                        xt, yt = traj_line.xy
                        ax.plot(np.array(xt)/3.281, np.array(yt)/3.281, 'b', linestyle='dashed')
                        ax.scatter(gcrs_fail_region.centroid.x/3.281, gcrs_fail_region.centroid.y/3.281)
                debris_dict['flight path'].append(all_traj_list)
                # if plot_flag:
                #     # Add source and target building geometries:
                #     xsource_rect, ysource_rect = source_roof_geometry.exterior.xy
                #     ax.plot(np.array(xsource_rect)/3.281, np.array(ysource_rect)/3.281, 'k')
                #     xtarget, ytarget = target_bldg_footprint.exterior.xy
                #     ax.plot(np.array(xtarget)/3.281, np.array(ytarget)/3.281, 'r')
                #     # Plot the directional debris region:
                #     dir_debris_region = df_site_debris.loc[df_site_debris['debris name']==source_bldg.adjacentElement['Roof'][0].hasCover, 'directional debris region'].values[0]
                #     xdir, ydir = dir_debris_region.exterior.xy
                #     ax.plot(np.array(xdir)/3.281, np.array(ydir)/3.281, color='orange', linewidth=2)
                # 3) Now find what elements in target building are affected by impact:
                wall_fail_list = []
                for hit_traj in hit_traj_list:
                    wall_list = []
                    for wall in target_bldg.adjacentElement['Walls']:
                        # First make sure the wall in question has not already experienced failure:
                        if wall in pressure_fail_target:
                            pass
                        else:
                            # Pull the wall's line geometry:
                            wall_line = wall.hasGeometry['1D Geometry']['local']
                            if hit_traj.intersects(wall_line):
                                # z-constraint: check wall's z coordinates:
                                wall_planar_pts = list(wall.hasGeometry['3D Geometry']['local'].exterior.coords)
                                zs = []
                                for pt in wall_planar_pts:
                                    zs.append(pt[2])
                                if max(zs) <= source_bldg.hasGeometry['Height']:
                                    wall_list.append(wall)
                                else:
                                    pass
                            else:
                                pass
                    # Find out which element got damaged:
                    prob_hit = uniform.rvs(size=len(wall_list), random_state=rng)
                    max_idx = np.where(prob_hit == max(prob_hit))[0][0]
                    # Extract the impacted walls:
                    if parcel_flag:
                        # Narrow the impact region based on the typical or maximum width of WBD-vulnerable element:
                        ref_wall = wall_list[max_idx]
                        ipt = hit_traj.intersection(ref_wall.hasGeometry['1D Geometry']['local'])
                        xl, yl = ref_wall.hasGeometry['1D Geometry']['local'].xy
                        # Create a new line showing max impact region:
                        new_pt_list = []
                        for k in range(0, len(xl)):
                            new_line = LineString([ipt, (xl[k], yl[k])])
                            new_pt = new_line.interpolate(distance=5/2)
                            new_pt_list.append(new_pt)
                        # Create 3D Geometry:
                        coords_list = list(ref_wall.hasGeometry['3D Geometry']['local'].exterior.coords)
                        zs = []
                        for c in coords_list:
                            zs.append(c[-1])
                        wbd_wall_poly = Polygon([(new_pt_list[0].x, new_pt_list[0].y, min(zs)), (new_pt_list[1].x,
                                                                                                 new_pt_list[1].y, min(zs)), (new_pt_list[1].x, new_pt_list[1].y, max(zs)), (new_pt_list[0].x, new_pt_list[0].y, max(zs)), (new_pt_list[0].x, new_pt_list[0].y, min(zs))])
                        new_wall = Wall()
                        new_wall.hasGeometry['3D Geometry']['local'] = wbd_wall_poly
                        new_wall.hasGeometry['1D Geometry']['local'] = LineString([(new_pt_list[0].x, new_pt_list[0].y), (new_pt_list[1].x,
                                                                                                 new_pt_list[1].y)])
                        new_wall.hasGeometry['Height'] = max(zs)-min(zs)
                        new_wall.hasGeometry['Area'] = new_wall.hasGeometry['1D Geometry']['local'].length*new_wall.hasGeometry['Height']
                        wall_fail_list.append(new_wall)
                    else:
                        wall_fail_list.append(wall_list[max_idx])
                debris_dict['fail element'].append(wall_fail_list)
            else:
                debris_dict['flight path'].append([None])
                debris_dict['fail element'].append([None])
        if plot_flag:
            ax.set_xlabel('x [m]')
            ax.set_ylabel('y [m]')
            ax.set_yticks(np.arange(-50, 200, 50))
            fig.set_tight_layout(True)
            plt.show()
        else:
            pass
    else:
        pass
    return debris_dict


def wind_pressure_ftree(bldg, wind_speed, facade_flag, parcel_flag, rng):
    """
    A function to conduct the wind pressure fault tree analysis of a building.
    :param bldg: (Building object) with hasDemand attribute populated with external wind pressures. Wall and Roof
                objects in Building.adjacentElement
    :param wind_speed: The wind speed that will be used to quantify the pressure demand. This should be the wind speed
                        in Exposure C, 10 m reference height at the building location
    :param facade_flag: (Boolean) True if the fault tree analysis includes assessment of facade component performance
    :param parcel_flag: (Boolean) True if the Building object is populated with minimum descriptions (i.e., has no
                        information regarding component sizing)
    :param rng: (From np.random.default_rng(seed)) Random number generator object
    :return: df_fail: (Pandas DataFrame) with columns = failure elements (Wall/Roof objects), failure regions
            (Shapely polygon), and whether element is a roof element (True/False)
    """
    # For each building:
    # 1) Sample pressure coefficients and calculate wind pressure loading demand:
    df_bldg_cps = bldg.hasDemand['wind pressure']['external']

    def get_sample_cp(mean_cp, cp_std_dev):
        return norm.rvs(mean_cp, cp_std_dev, random_state=rng)
    # Sample from gaussian distribution with mean = mean cp and std dev = 0.3
    df_bldg_cps['Sample Cp'] = get_sample_cp(df_bldg_cps['Mean Cp'], df_bldg_cps['Cp Std Dev'])
    # Quantify pressures:
    pressure_calc = PressureCalc()
    df_bldg_cps['Pressure'] = df_bldg_cps['Sample Cp'].apply(lambda j: pressure_calc.get_tpu_pressure(wind_speed, j, 'B', bldg.hasGeometry['Height'], 'mph'))
    # Apply correction for pressure taps at the bottom: pressure = 0
    idx_col = np.where(df_bldg_cps.columns == 'Sample Cp')[0][0]
    for idx in df_bldg_cps.index.to_list():
        if df_bldg_cps['Real Life Location'][idx].z == 0:
            df_bldg_cps.iat[idx, idx_col] = 0
        else:
            pass
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
                    # Capacity versus demand checks:
                    area_idx = 0
                    for p in tap_pressures.index.to_list():
                        fail_flag = False
                        if tap_pressures.loc[p] == 0:  # If no pressure, skip
                            pass
                        elif tap_pressures.loc[p] < 0:
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
                            if parcel_flag:  # Failure region is the tap area:
                                fail_regions.append(df_bldg_cps['Tap Polygon'][p])
                                elem.hasFailure['wind pressure'] = True
                                fail_elements.append(elem)
                            else:
                                if 'GLASS' in elem.hasType.upper():
                                    fail_regions.append(elem.hasGeometry['3D Geometry']['local'])
                                    elem.hasFailure['wind pressure'] = True
                                    fail_elements.append(elem)
                                else:
                                    print('Glass check not working')
                                    fail_regions.append(tap_areas[area_idx])
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
