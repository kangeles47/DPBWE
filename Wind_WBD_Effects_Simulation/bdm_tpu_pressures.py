import numpy as np
from math import atan2, degrees, cos, sin, sqrt
from shapely.geometry import Point, Polygon, LineString
from shapely.ops import split
from shapely import affinity
from shapely.errors import TopologicalError
from scipy.interpolate import griddata
import matplotlib.pyplot as plt
from scipy.io import loadmat
from scipy.spatial import Voronoi
import pandas as pd


def map_tpu_ptaps(bldg, tpu_wdir, high_value_flag):
    # Create new key-value pairs in the data model:
    bldg.hasGeometry['TPU_surfaces'] = {'local': []}
    # Step 1: Determine the building's TPU use case:
    eave_length = 0
    h_bldg = bldg.hasGeometry['Height']
    match_flag, num_surf, side_lines, model_file, hb_ratio, db_ratio, rect, surf_dict, rect_surf_dict = find_tpu_use_case(bldg, tpu_wdir, eave_length)
    if num_surf == 5:
        bfull, hfull, dfull, rect_surf_dict = get_TPU_surfaces(bldg, match_flag, num_surf, side_lines, hb_ratio, db_ratio, rect, tpu_wdir, surf_dict, rect_surf_dict)
        df_simple_map = map_tap_data(tpu_wdir, model_file, num_surf, bfull, hfull, dfull, side_lines, surf_dict, match_flag, h_bldg, rect_surf_dict, bldg, high_value_flag)
    elif num_surf == 6:
        bfull, hfull, dfull, surf_dict = get_tpu_gable_rsurfaces(bldg, match_flag, side_lines, hb_ratio, db_ratio, rect, tpu_wdir, high_value_flag)
        df_simple_map = map_gable_roof_tap_data(tpu_wdir, model_file, bfull, hfull, dfull, side_lines, surf_dict, match_flag,
                                h_bldg, rect, bldg, high_value_flag)
    return df_simple_map


def find_tpu_use_case(bldg, tpu_wdir, eave_length):
    """
    A function to identify the TPU use case for the given building.
    Function also returns various parameters (e.g., aspect ratios) pertinent to transformation of model building to
    full-scale geometries.

    :param bldg: A Building object with (at minimum): building height, building footprint in cartesian coordinates,
                roof geometry information (shape)
    :param tpu_wdir: The wind direction, following TPU convention.
    :param eave_length: The eave length. Enter 0 if none.
    :return: match_flag: Boolean: True if the input building's geometry exactly matches the model building geometry
    :return: num_surf: The number of surfaces corresponding to the model building geometry
    :return: side_lines:
    :return: model_file:
    :return: hb_ratio:
    :return: db_ratio:
    :return: rect:
    :return: surf_dict:
    :return: ref_surf_dict:
    """
    # This function determines the appropriate TPU use case for the given building.
    # Various tags are populated to identify the correct .mat file with TPU data
    # Given a building, determine its corresponding use case:
    # Step 1: wdir_tag:
    wdir_tag = ''
    if tpu_wdir == 0 or tpu_wdir == 180:
        wdir_tag = '00.mat'
    elif tpu_wdir == 15 or tpu_wdir == 165 or tpu_wdir == 195 or tpu_wdir == 345:
        wdir_tag = '15.mat'
    elif tpu_wdir == 30 or tpu_wdir == 150 or tpu_wdir == 210 or tpu_wdir == 330:
        wdir_tag = '30.mat'
    elif tpu_wdir == 45 or tpu_wdir == 135 or tpu_wdir == 225 or tpu_wdir == 315:
        wdir_tag = '45.mat'
    elif tpu_wdir == 60 or tpu_wdir == 120 or tpu_wdir == 240 or tpu_wdir == 300:
        wdir_tag = '60.mat'
    elif tpu_wdir == 75 or tpu_wdir == 105 or tpu_wdir == 255 or tpu_wdir == 285:
        wdir_tag = '75.mat'
    elif tpu_wdir == 90 or tpu_wdir == 270:
        wdir_tag = '90.mat'
    if len(wdir_tag) == 0:
        # Assign wind direction tag based on "closest" wind direction:
        print('Exact TPU wind direction not available for ' + str(tpu_wdir) + ' degrees')
        if tpu_wdir <= 7.5 or tpu_wdir > 352.5 or (172.5 < tpu_wdir <= 187.5):
            wdir_tag = '00.mat'
        elif (7.5 < tpu_wdir <= 22.5) or (157.5 < tpu_wdir <= 172.5) or (187.5 < tpu_wdir <= 202.5) or (337.5 < tpu_wdir <= 352.5):
            wdir_tag = '15.mat'
        elif (22.5 < tpu_wdir <= 37.5) or (142.5 < tpu_wdir <= 157.5) or (202.5 < tpu_wdir <= 217.5) or (322.5 < tpu_wdir <= 337.5):
            wdir_tag = '30.mat'
        elif (37.5 < tpu_wdir <= 52.5) or (127.5 < tpu_wdir <= 142.5) or (217.5 < tpu_wdir <= 232.5) or (307.5 < tpu_wdir <= 322.5):
            wdir_tag = '45.mat'
        elif (52.5 < tpu_wdir <= 67.5) or (112.5 < tpu_wdir <= 127.5) or (232.5 < tpu_wdir <= 247.5) or (292.5 < tpu_wdir <= 307.5):
            wdir_tag = '60.mat'
        elif (67.5 < tpu_wdir <= 82.5) or (97.5 < tpu_wdir <= 112.5) or (247.5 < tpu_wdir <= 262.5) or (277.5 < tpu_wdir <= 292.5):
            wdir_tag = '75.mat'
        elif (82.5 < tpu_wdir <= 90) or (262.5 < tpu_wdir <= 277.5):
            wdir_tag = '90.mat'
        print('Approximate TPU wind direction will be used: ' + wdir_tag[:-3])
    else:
        pass
    # Step 2: Determine the building's aspect ratios:
    # Use an equivalent rectangle to calculate aspect ratios:
    rect = bldg.hasGeometry['Footprint']['local'].minimum_rotated_rectangle  # local coords only for now
    xrect, yrect = rect.exterior.xy
    # Determine the lengths of rectangle's sides using line segments:
    side_lines = {'lines': [], 'length': [], 'TPU direction': [], 'real life direction': []}
    max_length = 0  # Initialize dummy variable
    for ind in range(0, len(xrect) - 1):
        # First figure out if the line is dominantly in x or y:
        if abs(xrect[ind]-xrect[ind+1]) > abs(yrect[ind]-yrect[ind+1]):
            side_lines['real life direction'].append('x')
        else:
            side_lines['real life direction'].append('y')
        new_line = LineString([(xrect[ind], yrect[ind]), (xrect[ind + 1], yrect[ind + 1])])
        side_lines['lines'].append(new_line)
        side_lines['length'].append(new_line.length)
        # Update the maximum length if needed:
        if new_line.length > max_length:
            max_length = new_line.length
        else:
            pass
    # With the line geometry and their lengths, can now find the TPU direction of each line:
    for line in range(0, len(side_lines['lines'])):
        # For each line, figure out if line is in the TPU x-direction (longer length):
        if side_lines['lines'][line].length == max_length:
            line_direction = 'x'
        else:
            line_direction = 'y'
        # Record line directions:
        side_lines['TPU direction'].append(line_direction)
    # Re-arrange points if needed:
    if side_lines['real life direction'][1] == 'y' and side_lines['TPU direction'][1] == 'x':
        # Re-arrange points to satisfy code for companion use case:
        pts_list = list(rect.exterior.coords)
        new_pts_list = []
        new_side_lines = {'lines': [], 'length': [], 'TPU direction': [], 'real life direction': []}
        for j in range(0, len(side_lines['lines'])):
            if j < len(side_lines['lines'])-1:
                new_pts_list.append(pts_list[j+1])
                for key in new_side_lines:
                    new_side_lines[key].append(side_lines[key][j+1])
            else:
                new_pts_list.append(pts_list[0])
                for key in new_side_lines:
                    new_side_lines[key].append(side_lines[key][0])
        side_lines = new_side_lines
        rect = Polygon(new_pts_list)
    else:
        pass
    # Calculate aspect ratios:
    hb = bldg.hasGeometry['Height'] / min(side_lines['length'])
    db = max(side_lines['length']) / min(side_lines['length'])
    # Step 3: Use the building's aspect ratios to determine its corresponding TPU model building
    # Note: For gable roof cases --> height is h0: the height at base of roof
    # Determine the use case and the corresponding number of surfaces:
    if eave_length == 0:
        breadth_model = 160  # [mm]
        match_flag = True  # Start by assuming the geometry coincides with TPU
        # Height to breadth use case - same for flat, gable, and hip roof
        if hb == (1 / 4):
            height_model = 40  # [mm]
            hb_ratio = 1 / 4
        elif hb == (2 / 4):
            height_model = 80  # [mm]
            hb_ratio = 2 / 4
        elif hb == (3 / 4):
            height_model = 120  # [mm]
            hb_ratio = 3 / 4
        elif hb == 1:
            height_model = 160  # [mm]
            hb_ratio = 1
        else:
            # Choose the closest ratio:
            match_flag = False
            model_hbs = np.array([1 / 4, 2 / 4, 3 / 4, 1])
            diff_hbs = model_hbs - hb
            closest_hb = min(abs(diff_hbs))
            hb_index = np.where(diff_hbs == closest_hb)[0]
            try:
                hb_ratio = model_hbs[hb_index[0]]
            except IndexError:
                hb_index = np.where(diff_hbs == closest_hb * -1)[0]
                hb_ratio = model_hbs[hb_index[0]]
            # Assign the appropriate model height
            height_model = model_hbs[hb_index[0]] * breadth_model
        # Populate the height tag needed to access the correct data file:
        if height_model == 40:
            htag = '02'
        elif height_model == 80:
            htag = '04'
        elif height_model == 120:
            htag = '06'
        elif height_model == 160:
            htag = '08'
        # Depth to breadth use case:
        if bldg.adjacentElement['Roof'][0].hasShape['flat'] or bldg.adjacentElement['Roof'][0].hasShape['gable']:
            if db == 1:
                depth_model = 160
                db_ratio = 1
            elif db == 3 / 2:
                depth_model = 240
                db_ratio = 3 / 2
            elif db == 5 / 2:
                depth_model = 400
                db_ratio = 5 / 2
            else:
                # Choose the closest ratio:
                match_flag = False
                model_dbs = np.array([1, 3 / 2, 5 / 2])
                diff_dbs = model_dbs - db
                closest_db = min(abs(diff_dbs))
                db_index = np.where(diff_dbs == closest_db)[0]
                try:
                    db_ratio = model_dbs[db_index[0]]
                except IndexError:
                    db_index = np.where(diff_dbs == closest_db * -1)[0]
                    db_ratio = model_dbs[db_index[0]]
                # Assign the appropriate model height
                depth_model = model_dbs[db_index[0]] * breadth_model
            # Populate the height tag needed to access the correct data file:
            if depth_model == 160:
                dtag = '08'
            elif depth_model == 240:
                dtag = '12'
            elif depth_model == 400:
                dtag = '20'
            # Initialize roof tag, num_surf and, surf_dictionaries for each use case:
            if bldg.adjacentElement['Roof'][0].hasShape['flat']:
                num_surf = 5
                surf_dict = {1: None, 2: None, 3: None, 4: None, 5: None}
                rtag = '00'
            elif bldg.adjacentElement['Roof'][0].hasShape['gable']:
                num_surf = 6
                surf_dict = {1: None, 2: None, 3: None, 4: None, 5: None, 6: None}
                if bldg.adjacentElement['Roof'][0].hasPitch == 4.8:
                    rtag = '05'
                elif bldg.adjacentElement['Roof'][0].hasPitch == 9.4:
                    rtag = '10'
                elif bldg.adjacentElement['Roof'][0].hasPitch == 14:
                    rtag = '14'
                elif bldg.adjacentElement['Roof'][0].hasPitch == 18.4:
                    rtag = '18'
                elif bldg.adjacentElement['Roof'][0].hasPitch == 21.8:
                    rtag = '22'
                elif bldg.adjacentElement['Roof'][0].hasPitch == 26.7:
                    rtag = '27'
                elif bldg.adjacentElement['Roof'][0].hasPitch == 30:
                    rtag = '30'
                elif bldg.adjacentElement['Roof'][0].hasPitch == 45:
                    rtag = '45'
                else:
                    # Find the closest roof pitch use case:
                    model_rpitches = np.array([4.8, 9.4, 14, 18.4, 21.8, 26.7, 30, 45])
                    diff_rpitches = model_rpitches - bldg.adjacentElement['Roof'][0].hasPitch
                    closest_rpitch = min(abs(diff_rpitches))
                    rtag_list = ['05', '10', '14', '18', '22', '27', '30', '45']
                    # Assign the appropriate roof pitch:
                    try:
                        rpitch_index = np.where(abs(diff_rpitches) == closest_rpitch)[0][0]
                    except IndexError:
                        rpitch_index = np.where(diff_rpitches == closest_rpitch * -1)[0][0]
                    rtag = rtag_list[rpitch_index]
            # Initialize string to access the correct model building file:
            model_file = 'Cp_ts_g' + dtag + htag + rtag + wdir_tag
        elif bldg.adjacentElement['Roof'][0].hasShape['hip']:  # Note: most common hip roof pitches 4:12-6:12
            num_surf = 8
            surf_dict = {1: None, 2: None, 3: None, 4: None, 5: None, 6: None, 7: None, 8: None}
            db_ratio = 3 / 2  # One option for hip roof
            # Initialize string to access the correct model building file:
            model_file = 'Cp_ts_h'
        else:
            print('Roof shape not supported. Please provide a valid roof shape.')
        # Create an empty dictionary to hold the parcel's equivalent rectangle geometry:
        rect_surf_dict = {}
        for key in surf_dict:
            rect_surf_dict[key] = None
    else:
        print('Buildings with eaves are not yet supported')
    return match_flag, num_surf, side_lines, model_file, hb_ratio, db_ratio, rect, surf_dict, rect_surf_dict


def get_TPU_surfaces(bldg, match_flag, num_surf, side_lines, hb_ratio, db_ratio, rect, tpu_wdir, surf_dict, rect_surf_dict):
    # Convert TPU model building geometries into full-scale:
    # Create the TPU footprint geometry from the real-life building's equivalent rectangle:
    # 1) Quantify the model building's full scale breadth, depth, and height:
    if match_flag:
        # The real-life building's geometry can be used directly:
        bfull = min(side_lines['length'])
        hfull = bldg.hasGeometry['Height']
        dfull = max(side_lines['length'])
    else:
        # Use the real-life building's breadth to create the full-scale geometry:
        bfull = min(side_lines['length'])
        hfull = hb_ratio * bfull
        dfull = db_ratio * bfull
    # 2) Create full-scale building footprint for model building using line geometries from reference building's
    # rectangular footprint:
    tpu_poly_pts = []
    for line in range(0, len(side_lines['lines'])):
        if side_lines['TPU direction'][line] == 'y':
            pass  # breadth is fixed
        else:
            # x-direction in TPU = building depth:
            ref_pt = side_lines['lines'][line].centroid  # line centroid
            line_pts = list(side_lines['lines'][line].coords)
            # Create two new lines to project full-scale depth:
            new_line1 = LineString([ref_pt, Point(line_pts[0])])
            new_line2 = LineString([ref_pt, Point(line_pts[1])])
            # Distribute half of dfull to each line segment:
            new_point1 = new_line1.interpolate(dfull / 2)
            new_point2 = new_line2.interpolate(dfull / 2)
            # Create new line corresponding to full scale depth:
            #tpu_line = LineString([new_point1, new_point2])
            # Save points for model building's full-scale footprint:
            tpu_poly_pts.append((new_point1.x, new_point1.y))
            tpu_poly_pts.append((new_point2.x, new_point2.y))
    # 3) Create model building's full-scale geometry (surfaces):
    new_zpts = []  # Placeholder for x, y, z points
    tpu_polys = []  # Placeholder for surface polygons
    if num_surf == 5:
        new_zpts.append(create_zcoords(Polygon(tpu_poly_pts), 0))
        new_zpts.append(create_zcoords(Polygon(tpu_poly_pts), hfull))
    else:
        pass
    # When building geometries do not match, also create this building's 3D box geometry for comparison:
    if not match_flag:
        bldg_zpts = []  # Placeholder for x, y, z points
        bldg_polys = []  # Placeholder for surface polygons
        if num_surf == 5:
            zcoord_base = bldg.hasStory[0].hasElevation[0]
            zcoord_roof = bldg.hasStory[-1].hasElevation[-1]
            bldg_zpts.append(create_zcoords(rect, zcoord_base))
            bldg_zpts.append(create_zcoords(rect, zcoord_roof))
        else:
            pass
    # Set up plotting:
    fig = plt.figure()
    ax = plt.axes(projection='3d')
    if num_surf == 5 or num_surf == 8:  # Hip and gable roofs both have rectangular vertical planes
        for plane in range(0, len(new_zpts) - 1):
            for zpt in range(0, len(new_zpts[plane]) - 1):
                # Create the surface polygon:
                tpu_surf = Polygon([new_zpts[plane][zpt], new_zpts[plane + 1][zpt], new_zpts[plane + 1][zpt + 1], new_zpts[plane][zpt + 1]])
                tpu_polys.append(tpu_surf)
                # Extract xs, ys, and zs and plot
                surf_xs = []
                surf_ys = []
                surf_zs = []
                for surf_points in list(tpu_surf.exterior.coords):
                    surf_xs.append(surf_points[0])
                    surf_ys.append(surf_points[1])
                    surf_zs.append(surf_points[2])
                # Plot the surfaces for the entire building to verify:
                ax.plot(np.array(surf_xs) / 3.281, np.array(surf_ys) / 3.281, np.array(surf_zs) / 3.281, linestyle='dashed', color='gray')
                # Repeat this process for buildings with geometries that do not exactly match TPU:
                if not match_flag:
                    bldg_surf = Polygon([bldg_zpts[plane][zpt], bldg_zpts[plane + 1][zpt], bldg_zpts[plane + 1][zpt + 1], bldg_zpts[plane][zpt + 1]])
                    bldg_polys.append(bldg_surf)
                    bsurf_xs = []
                    bsurf_ys = []
                    bsurf_zs = []
                    for bsurf_points in list(bldg_surf.exterior.coords):
                        bsurf_xs.append(bsurf_points[0])
                        bsurf_ys.append(bsurf_points[1])
                        bsurf_zs.append(bsurf_points[2])
                    # Plot the surfaces for the entire building:
                    ax.plot(np.array(bsurf_xs) / 3.281, np.array(bsurf_ys) / 3.281, np.array(bsurf_zs) / 3.281, linestyle='dashed', color='gray')
        # Plot the building geometry:
        for poly in bldg.hasGeometry['3D Geometry']['local']:
            x_bpoly, y_bpoly, z_bpoly = [], [], []
            for bpt in list(poly.exterior.coords):
                x_bpoly.append(bpt[0])
                y_bpoly.append(bpt[1])
                z_bpoly.append(bpt[2])
            #ax.plot(np.array(x_bpoly)/3.281, np.array(y_bpoly)/3.281, np.array(z_bpoly)/3.281, color='k')
        # Make the panes transparent:
        ax.set_zlim3d(bottom=0, top=16)
        ax.set_zticks(np.arange(0, 20, 4))
        ax.xaxis.set_tick_params(labelsize=16)
        ax.yaxis.set_tick_params(labelsize=16)
        ax.zaxis.set_tick_params(labelsize=16)
        ax.w_xaxis.set_pane_color((1.0, 1.0, 1.0, 1.0))
        ax.w_yaxis.set_pane_color((1.0, 1.0, 1.0, 1.0))
        ax.w_zaxis.set_pane_color((1.0, 1.0, 1.0, 1.0))
        # Make the grids transparent:
        ax.xaxis._axinfo["grid"]['color'] = (1, 1, 1, 0)
        ax.yaxis._axinfo["grid"]['color'] = (1, 1, 1, 0)
        ax.zaxis._axinfo["grid"]['color'] = (1, 1, 1, 0)
        # Plot labels
        ax.set_xlabel('x [m]', fontsize=16, labelpad=10)
        ax.set_ylabel('y [m]', fontsize=16, labelpad=10)
        ax.set_zlabel('z [m]', fontsize=16, labelpad=10)
        plt.show()
        # Add roof surfaces to the end of the list:
        if num_surf == 5:
            roof_surf = Polygon(new_zpts[-1])
            tpu_polys.append(roof_surf)
            if not match_flag:
                broof_surf = Polygon(bldg_zpts[-1])
                bldg_polys.append(broof_surf)
        elif num_surf == 8:  # Placeholder for hip roof polygons
            pass
    else:
        pass
    # 4 ) Determine surface numberings following TPU convention:
    if side_lines['TPU direction'][1] == 'x':
        # Polygon order:
        # When TPU and global axes are both running in general E-W direction:
        # TPU surfaces 1, 2, 3, 4, 5 correspond to surfaces in positions 0, 1, 2, 3, 4 in tpu_polys
        if tpu_wdir <= 90:
            # TPU and global axes are aligned:
            # TPU Surface 1 is windward surface and order is ccw: 1, 2, 3, 4, 5
            poly_order = [0, 1, 2, 3, 4]
        elif 90 < tpu_wdir <= 180:
            # TPU Surface 3 is windward surface and order is cw: 3, 2, 1, 4, 5
            poly_order = [2, 1, 0, 3, 4]
        elif 180 < tpu_wdir <= 270:
            # TPU Surface 3 is windward surface and order is ccw: 3, 4, 1, 2, 5
            poly_order = [3, 4, 1, 2, 5]
        elif 270 < tpu_wdir <= 360:
            # TPU Surface 1 is windward surface and order is cw: 1, 4, 3, 2, 5
            poly_order = [0, 3, 2, 1, 4]
    elif side_lines['TPU direction'][1] == 'y' and side_lines['real life direction'][1] == 'y':
        # When TPU y-axis is running in N-S direction:
        # TPU surfaces 1, 2, 3, 4, 5 correspond to surfaces in positions 3, 0, 1, 2, 4 in tpu_polys
        if tpu_wdir <= 90:
            # TPU Surface 1 is windward surface and order is ccw: 1, 2, 3, 4, 5
            poly_order = [1, 2, 3, 0, 4]
        elif 90 < tpu_wdir <= 180:
            # TPU Surface 3 is windward surface and order is cw: 3, 2, 1, 4, 5
            poly_order = [3, 2, 1, 0, 4]
        elif 180 < tpu_wdir <= 270:
            # TPU Surface 3 is windward surface and order is ccw: 3, 4, 1, 2, 5
            poly_order = [3, 0, 1, 2, 4]
        elif 270 < tpu_wdir <= 360:
            # TPU Surface 1 is windward surface and order is cw: 1, 4, 3, 2, 5
            poly_order = [1, 0, 3, 2, 4]
    elif side_lines['TPU direction'][1] == 'y' and side_lines['real life direction'][1] == 'x':
        # When TPU y-axis is running in E-W direction:
        if tpu_wdir <= 90:
            poly_order = [3, 0, 1, 2, 4]
        elif 90 < tpu_wdir <= 180:
            poly_order = [1, 0, 3, 2, 4]
        elif 180 < tpu_wdir <= 270:
            poly_order = [1, 2, 3, 0, 4]
        elif 270 < tpu_wdir <= 360:
            poly_order = [3, 2, 1, 0, 4]
    else:
        print('Cannot determine dominant axis')
    # Assign the surfaces to the correct key
    idx = surf_dict.keys()
    # Set up plotting:
    fig2 = plt.figure()
    ax2 = plt.axes(projection='3d')
    for i in idx:
        surf_dict[i] = tpu_polys[poly_order[i - 1]]
        if not match_flag:
            rect_surf_dict[i] = bldg_polys[poly_order[i-1]]
        else:
            pass
        # Optional: Plotting:
        # Extract xs, ys, and zs and plot
        poly_xs = []
        poly_ys = []
        poly_zs = []
        for pts in list(surf_dict[i].exterior.coords):
            poly_xs.append(pts[0])
            poly_ys.append(pts[1])
            poly_zs.append(pts[2])
        # Define various line colors to keep track of surfaces:
        colors = ['b', 'g', 'r', 'y', 'm']
        # Plot the surface geometry:
        ax2.plot(poly_xs, poly_ys, poly_zs, color=colors[i-1], label='Surface' + str(i))
        #ax2.plot(poly_xs, poly_ys, poly_zs, color='0.50', linestyle=(0, (1, 1)), label='Surface' + str(i))
    ax2.legend(loc='best')
    # Plot the building 3D Geometry:
    for poly in bldg.hasGeometry['3D Geometry']['local']:
        x_bpoly, y_bpoly, z_bpoly = [], [], []
        for bpt in list(poly.exterior.coords):
            x_bpoly.append(bpt[0])
            y_bpoly.append(bpt[1])
            z_bpoly.append(bpt[2])
        # Plot the building geometry:
        ax2.plot(x_bpoly, y_bpoly, z_bpoly, 'k')
    # Make the panes transparent:
    ax2.w_xaxis.set_pane_color((1.0, 1.0, 1.0, 1.0))
    ax2.w_yaxis.set_pane_color((1.0, 1.0, 1.0, 1.0))
    ax2.w_zaxis.set_pane_color((1.0, 1.0, 1.0, 1.0))
    # Make the grids transparent:
    ax2.xaxis._axinfo["grid"]['color'] = (1, 1, 1, 0)
    ax2.yaxis._axinfo["grid"]['color'] = (1, 1, 1, 0)
    ax2.zaxis._axinfo["grid"]['color'] = (1, 1, 1, 0)
    # Plot labels
    ax2.set_xlabel('x [m]')
    ax2.set_ylabel('y [m]')
    ax2.set_zlabel('z [m]')
    ax2.set_title('Surfaces for TPU Wind Direction: ' + str(tpu_wdir))
    # plt.axis('off')
    plt.show()
    # Step 5: Save the surfaces to the building description:
    bldg.hasGeometry['TPU_surfaces']['local'] = surf_dict
    return bfull, hfull, dfull, rect_surf_dict


def get_tpu_gable_rsurfaces(bldg, match_flag, side_lines, hb_ratio, db_ratio, rect, tpu_wdir, high_value_flag):
    # Convert TPU model building geometries into full-scale:
    # Create the TPU footprint geometry from the real-life building's equivalent rectangle:
    # 1) Quantify the model building's full scale breadth, depth, and height:
    if match_flag:
        # The real-life building's geometry can be used directly:
        bfull = min(side_lines['length'])
        hfull = bldg.hasGeometry['Height']
        dfull = max(side_lines['length'])
    else:
        # Use the real-life building's breadth to create the full-scale geometry:
        bfull = min(side_lines['length'])
        hfull = hb_ratio * bfull
        dfull = db_ratio * bfull
    # 2) Create full-scale building footprint for model building using line geometries from reference building's
    # rectangular footprint:
    tpu_footprint_pts = []
    split_line_pts = []
    for line in range(0, len(side_lines['lines'])):
        if side_lines['TPU direction'][line] == 'y':
            ref_pt = side_lines['lines'][line].centroid  # line centroid
            split_line_pts.append(ref_pt)
        else:
            # x-direction in TPU = building depth:
            scale_factor = dfull/max(side_lines['length'])
            scale_line = affinity.scale(side_lines['lines'][line], xfact=scale_factor, yfact=scale_factor)
            line_pts_list = list(scale_line.coords)
            # ref_pt = side_lines['lines'][line].centroid  # line centroid
            # line_pts = list(side_lines['lines'][line].coords)
            # # Create two new lines to project full-scale depth:
            # new_line1 = LineString([ref_pt, Point(line_pts[0])])
            # new_line2 = LineString([ref_pt, Point(line_pts[1])])
            # # Distribute half of dfull to each line segment:
            # if new_line1.length < dfull/2:
            #     new_point1 = new_line1.interpolate(dfull / 2)
            #     new_point2 = new_line2.interpolate(dfull / 2)
            # else:
            #     new_point1 = new_line1.interpolate(dfull / 2)
            #     new_point2 = new_line2.interpolate(dfull / 2)
            # Create new line corresponding to full scale depth:
            #tpu_line = LineString([new_point1, new_point2])
            # Save points for model building's full-scale footprint:
            tpu_footprint_pts.append(line_pts_list[0])
            tpu_footprint_pts.append(line_pts_list[1])
    # 3) Create 2D surfaces for surface 5 and 6 (roof):
    tpu_roof_polys = split(Polygon(tpu_footprint_pts), affinity.scale(LineString(split_line_pts), xfact=1.5, yfact=1.5))
    # 4) Figure out which polygon corresponds to surface 5 and 6, respectively:
    surf_dict = {5: None, 6: None}
    if side_lines['TPU direction'][1] == 'y' and side_lines['real life direction'][1] == 'y':
        if tpu_wdir <= 180:
            if tpu_roof_polys[0].centroid.y < tpu_roof_polys[1].centroid.y:
                surf_dict[5] = tpu_roof_polys[0]
                surf_dict[6] = tpu_roof_polys[1]
            else:
                surf_dict[5] = tpu_roof_polys[1]
                surf_dict[6] = tpu_roof_polys[0]
        elif 180 < tpu_wdir <= 360:
            if tpu_roof_polys[0].centroid.y > tpu_roof_polys[1].centroid.y:
                surf_dict[5] = tpu_roof_polys[0]
                surf_dict[6] = tpu_roof_polys[1]
            else:
                surf_dict[5] = tpu_roof_polys[1]
                surf_dict[6] = tpu_roof_polys[0]
    elif side_lines['TPU direction'][1] == 'y' and side_lines['real life direction'][1] == 'x':
        if tpu_wdir <= 180:
            if tpu_roof_polys[0].centroid.x < tpu_roof_polys[1].centroid.x:
                surf_dict[5] = tpu_roof_polys[0]
                surf_dict[6] = tpu_roof_polys[1]
            else:
                surf_dict[5] = tpu_roof_polys[1]
                surf_dict[6] = tpu_roof_polys[0]
        elif 180 < tpu_wdir <= 360:
            if tpu_roof_polys[0].centroid.x > tpu_roof_polys[1].centroid.x:
                surf_dict[5] = tpu_roof_polys[0]
                surf_dict[6] = tpu_roof_polys[1]
            else:
                surf_dict[5] = tpu_roof_polys[1]
                surf_dict[6] = tpu_roof_polys[0]
    # Plot the result:
    fig, ax = plt.subplots()
    for key in surf_dict:
        xs, ys = surf_dict[key].exterior.xy
        ax.plot(np.array(xs)/3.281, np.array(ys)/3.281, label='Surface ' + str(key))
        # Convert to 3D coordinates?
        if not high_value_flag:
            surf_dict[key] = Polygon(create_zcoords(surf_dict[key], hfull))
        else:
            pass
    xr, yr = rect.exterior.xy
    ax.plot(np.array(xr)/3.281, np.array(yr)/3.281, label='Actual building rectangle')
    ax.legend()
    ax.set_xlabel('x [m]', fontsize=16)
    ax.set_ylabel('y [m]', fontsize=16)
    plt.show()
    # 5) : Save the surfaces to the building description:
    bldg.hasGeometry['TPU_surfaces']['local'] = surf_dict
    return bfull, hfull, dfull, surf_dict


def map_tap_data(tpu_wdir, model_file, num_surf, bfull, hfull, dfull, side_lines, surf_dict, match_flag, h_bldg, rect_surf_dict, bldg, high_value_flag):
    # 1) Read in pressure data file and add to a DataFrame:
    tpu_file = 'D:/Users/Karen/Documents/Github/DPBWE/Datasets/TPU/' + model_file
    tpu_data = loadmat(tpu_file)
    # Export Location_of_measured_points into a DataFrame for easier manipulation:
    df = pd.DataFrame(tpu_data['Location_of_measured_points'], index=['x', 'y', 'Point Number', 'Surface Number'])
    df = df.T
    # Convert coordinate positions to ft:
    df['x'] = df['x'] / 305
    df['y'] = df['y'] / 305
    # Start by plotting out the points to see what they look like:
    # plt.plot(df['x'], df['y'], 'o')
    #plt.show()
    # 2) Convert pressure tap locations to full-scale:
    for pt in range(0, len(df['Point Number'])):
        if df['Surface Number'][pt] < 5:
            if df['Surface Number'][pt] == 1:
                df['x'][pt] = df['x'][pt] * (bfull / (tpu_data['Building_breadth'][0][0] / 305))
                df['y'][pt] = df['y'][pt] * (hfull / (tpu_data['Building_height'][0][0] / 305))
            elif df['Surface Number'][pt] == 2:
                df['x'][pt] = df['x'][pt] * (bfull / (tpu_data['Building_breadth'][0][0] / 305))
                df['y'][pt] = df['y'][pt] * (hfull / (tpu_data['Building_height'][0][0] / 305))
            elif df['Surface Number'][pt] == 3:
                df['x'][pt] = df['x'][pt] * (dfull / (tpu_data['Building_depth'][0][0] / 305))
                df['y'][pt] = df['y'][pt] * (hfull / (tpu_data['Building_height'][0][0] / 305))
            elif df['Surface Number'][pt] == 4:
                df['x'][pt] = df['x'][pt] * (dfull / (tpu_data['Building_depth'][0][0] / 305))
                df['y'][pt] = df['y'][pt] * (hfull / (tpu_data['Building_height'][0][0] / 305))
        else:
            # Different approach for roof:
            if num_surf == 5 and df['Surface Number'][pt] == 5:
                df['x'][pt] = df['x'][pt] * (dfull / (tpu_data['Building_depth'][0][0] / 305))
                df['y'][pt] = df['y'][pt] * (bfull / (tpu_data['Building_breadth'][0][0] / 305))
            elif num_surf == 8:
                pass
            elif (num_surf == 6 and df['Surface Number'][pt] == 5) or (num_surf == 6 and df['Surface Number'][pt] == 6):
                df['x'][pt] = df['x'][pt] * (dfull / (tpu_data['Building_depth'][0][0] / 305))
                df['y'][pt] = df['y'][pt] * (bfull / (tpu_data['Building_breadth'][0][0] / 305))
    # Uncomment next two lines to show full-scale conversion of pressure tap locations:
    # plt.plot(df['x'], df['y'], 'o')
    # plt.show()
    # 3) Quantify the mean Cp for each pressure tap location:
    mean_cps = []
    std_dev = []
    for pnum in df['Point Number']:
        mean_cps.append(np.mean(tpu_data['Wind_pressure_coefficients'][:, int(pnum) - 1]))
        std_dev.append(np.std(tpu_data['Wind_pressure_coefficients'][:, int(pnum) - 1]))
    # Add this information to the Dataframe:
    df['Mean Cp'] = mean_cps
    df['Cp Std Dev'] = std_dev
    # 4) Contour plots/interpolating data - necessary to wrap onto real-life geometries
    # Set up placeholders to save contour plot coefficients:
    contour_values = {'x': [], 'y': [], 'Surface Number': [], 'Mean Cp': [], 'Cp Std Dev': []}
    # Step 4a: To create Cp values for entire surface, need to first define points at surface boundaries and add data
    for surf in range(1, num_surf + 1):
        if num_surf == 5:
            # Grab max and min values for x, y, respectively (pressure tap locations)
            min_x = min(df.loc[df['Surface Number'] == surf, 'x'])
            max_x = max(df.loc[df['Surface Number'] == surf, 'x'])
            min_y = min(df.loc[df['Surface Number'] == surf, 'y'])
            max_y = max(df.loc[df['Surface Number'] == surf, 'y'])
            # Need the indices of our four extreme points in original data to extract their Cp values
            # Idea here: simply extend Cp values to the extremes of the geometry (actual values may be higher/lower)
            xs = [min_x, min_x, max_x, max_x]
            ys = [min_y, max_y, min_y, max_y]
            df_surf = df.loc[df['Surface Number'] == surf]
            ind_list = []
            for j in range(0, len(xs)):
                ind_list.append(
                    df_surf.loc[((df_surf['x'] == xs[j]) & (df_surf['y'] == ys[j])), 'Point Number'].index.to_list()[0])
            # Assign boundary geometry based off of full-scale dim
            if surf == 1 or surf == 3:
                dim_x = (hfull - (abs(max_x - min_x))) / 2
                dim_y = (bfull - (abs(max_y - min_y))) / 2
                px = [min_x - dim_x, min_x - dim_x, max_x + dim_x, max_x + dim_x]
                py = [max_y + dim_y, min_y - dim_y, min_y - dim_y, max_y + dim_y]
                boundary_cps = [df_surf['Mean Cp'][ind_list[1]], df_surf['Mean Cp'][ind_list[0]],
                                df_surf['Mean Cp'][ind_list[2]], df_surf['Mean Cp'][ind_list[3]]]
                boundary_std_devs = [df_surf['Cp Std Dev'][ind_list[1]], df_surf['Cp Std Dev'][ind_list[0]],
                                    df_surf['Cp Std Dev'][ind_list[2]], df_surf['Cp Std Dev'][ind_list[3]]]
            elif surf == 2 or surf == 4:
                dim_x = (dfull - (abs(max_x - min_x))) / 2
                dim_y = (hfull - (abs(max_y - min_y))) / 2
                px = [min_x - dim_x, max_x + dim_x, max_x + dim_x, min_x - dim_x]
                py = [min_y - dim_y, min_y - dim_y, max_y + dim_y, max_y + dim_y]
                boundary_cps = [df_surf['Mean Cp'][ind_list[0]], df_surf['Mean Cp'][ind_list[2]],
                                df_surf['Mean Cp'][ind_list[3]], df_surf['Mean Cp'][ind_list[1]]]
                boundary_std_devs = [df_surf['Cp Std Dev'][ind_list[0]], df_surf['Cp Std Dev'][ind_list[2]],
                                    df_surf['Cp Std Dev'][ind_list[3]], df_surf['Cp Std Dev'][ind_list[1]]]
            elif surf == 5:
                # Add points for surface 5:
                px = [-dfull / 2, dfull / 2, dfull / 2, -dfull / 2]
                py = [-bfull / 2, -bfull / 2, bfull / 2, bfull / 2]
                boundary_cps = [df_surf['Mean Cp'][ind_list[0]], df_surf['Mean Cp'][ind_list[2]],
                                df_surf['Mean Cp'][ind_list[3]], df_surf['Mean Cp'][ind_list[1]]]
                boundary_std_devs = [df_surf['Cp Std Dev'][ind_list[0]], df_surf['Cp Std Dev'][ind_list[2]],
                                df_surf['Cp Std Dev'][ind_list[3]], df_surf['Cp Std Dev'][ind_list[1]]]
            # Add in new locations and filler Cp data:
            for pt in range(0, len(px)):
                df = df.append({'x': px[pt], 'y': py[pt], 'Point Number': df['Point Number'].iloc[-1] + 1,
                                'Surface Number': 1 * surf, 'Mean Cp': boundary_cps[pt], 'Cp Std Dev': boundary_std_devs[pt]}, ignore_index=True)
            # Up to this point, code designates the four points marking quadrilateral geometry
            # Determine remaining boundary geometries (points within line segments) and assign pressure coefficients:
            xcoords = df.loc[df['Surface Number'] == surf, 'x']
            ycoords = df.loc[df['Surface Number'] == surf, 'y']
            mcps = df.loc[df['Surface Number'] == surf, 'Mean Cp']
            std_dev_cps = df.loc[df['Surface Number'] == surf, 'Cp Std Dev']
            index_list = xcoords.index.to_list()
            # Loop through xcoords and create horizontal boundaries
            for x in index_list:
                if xcoords[x] == min_x:  # recall that this is original min_x
                    # Add new point to DataFrame and use current point's mean Cp:
                    df = df.append({'x': min(df.loc[df['Surface Number'] == surf, 'x']), 'y': ycoords[x],
                                    'Point Number': df['Point Number'].iloc[-1] + 1, 'Surface Number': 1 * surf,
                                    'Mean Cp': mcps[x], 'Cp Std Dev': std_dev_cps[x]}, ignore_index=True)
                elif xcoords[x] == max_x:
                    df = df.append({'x': max(df.loc[df['Surface Number'] == surf, 'x']), 'y': ycoords[x],
                                    'Point Number': df['Point Number'].iloc[-1] + 1, 'Surface Number': 1 * surf,
                                    'Mean Cp': mcps[x], 'Cp Std Dev': std_dev_cps[x]}, ignore_index=True)
            # Loop through ycoords and create vertical boundaries:
            for y in index_list:
                if ycoords[y] == min_y:  # recall that this is original min_x
                    # Add new point to DataFrame and use current point's mean Cp:
                    df = df.append({'x': xcoords[y], 'y': min(df.loc[df['Surface Number'] == surf, 'y']),
                                    'Point Number': df['Point Number'].iloc[-1] + 1, 'Surface Number': 1 * surf,
                                    'Mean Cp': mcps[y], 'Cp Std Dev': std_dev_cps[y]}, ignore_index=True)
                elif ycoords[y] == max_y:
                    df = df.append({'x': xcoords[y], 'y': max(df.loc[df['Surface Number'] == surf, 'y']),
                                    'Point Number': df['Point Number'].iloc[-1] + 1, 'Surface Number': 1 * surf,
                                    'Mean Cp': mcps[y], 'Cp Std Dev': std_dev_cps[y]}, ignore_index=True)
        else:
            pass
        # Step 3b: Create contours of pressure coefficients:
        # Create x and y meshgrids:
        xvals = np.linspace(min(df.loc[df['Surface Number'] == surf, 'x']),
                            max(df.loc[df['Surface Number'] == surf, 'x']), 10)
        yvals = np.linspace(min(df.loc[df['Surface Number'] == surf, 'y']),
                            max(df.loc[df['Surface Number'] == surf, 'y']), 10)
        x, y = np.meshgrid(xvals, yvals)
        # Extract the mean pressure coefficients for each pressure tap location:
        surf_cps = df.loc[df['Surface Number'] == surf, 'Mean Cp']
        surf_std_dev_cps = df.loc[df['Surface Number'] == surf, 'Cp Std Dev']
        # Determine the corresponding "z" (i.e., Cp) values:
        points = np.column_stack((df.loc[df['Surface Number'] == surf, 'x'], df.loc[df['Surface Number'] == surf, 'y']))
        mcp_zvals = griddata(points, surf_cps, (x, y), method='cubic')
        std_dev_zvals = griddata(points, surf_std_dev_cps, (x, y), method='cubic')
        # Save the (x, y) coordinate pairs and their corresponding Cp according to surface number:
        for col in range(0, len(xvals)):
            for row in range(0, len(yvals)):
                # Record x and y-values:
                contour_values['x'].append(xvals[col])
                contour_values['y'].append(yvals[row])
                # Record the surface number:
                contour_values['Surface Number'].append(surf)
                # Grab the Cp value corresponding to this (x,y) pair:
                contour_values['Mean Cp'].append(mcp_zvals[row][col])
                contour_values['Cp Std Dev'].append(std_dev_zvals[row][col])
        # Uncomment to produce 2D contour plots:
        # cp = plt.contourf(x, y, zvals)
        # plt.colorbar()
        # plt.show()
    # Create a new DataFrame with new set of (x, y) and Cps:
    df_contour = pd.DataFrame(contour_values)
    # Step 3b: Coordinate transformation (for tpu_wdir > 90)
    if tpu_wdir > 90:
        # Find index for column we are modifying:
        for col in range(0, len(df_contour.columns)):
            if df_contour.columns[col] == 'x':
                x_col = col
            elif df_contour.columns[col] == 'y':
                y_col = col
            else:
                pass
        for row in range(0, len(df_contour['Mean Cp'])):
            surf_num = df_contour['Surface Number'][row]
            if 90 < tpu_wdir <= 180:
                if surf_num == 1 or surf_num == 3 or surf_num == 5:
                    # Reflect Surface 1, 3, and 5 coordinates over x-axis:
                    df_contour.iat[row, x_col] = df_contour['x'][row] * -1
                elif surf_num == 2 or surf_num == 4:
                    # Reflect Surface 2 and 4 coordinates over x-axis:
                    df_contour.iat[row, x_col] = df_contour['x'][row] * -1
            elif 180 < tpu_wdir <= 270:
                    # Reflect all Surface coordinates over x-axis and y-axis:
                    df_contour.iat[row, x_col] = df_contour['x'][row] * -1
                    df_contour.iat[row, y_col] = df_contour['y'][row] * -1
            else:
                if surf_num == 1 or surf_num == 3 or surf_num == 5:
                    # Reflect Surface 1, 3, and 5 coordinates over x-axis:
                    df_contour.iat[row, y_col] = df_contour['y'][row] * -1
                elif surf_num == 2 or surf_num == 4:
                    # Reflect Surface 2 and 4 coordinates over x-axis:
                    df_contour.iat[row, x_col] = df_contour['x'][row] * -1
    else:
        pass
    # 5) Mapping pressure tap locations to real-life scenario:
    proj_dict = {'Index': [], 'Real Life Location': [], 'Surface Number': [], 'Mean Cp': [], 'Cp Std Dev': []}
    for surf in surf_dict:  # surf_dict holds surface geometries for each TPU surface number
        df_csurf = df_contour.loc[df_contour['Surface Number'] == surf]
        # Extract all index and Surface numbers first (b/c dictionary key order is arbitrary):
        for idx in df_csurf.index.tolist():
            proj_dict['Index'].append(idx)
            proj_dict['Surface Number'].append(surf)
        # Finding real-life pressure tap locations:
        # Define an origin point for each surface and calculate distances of pressure taps from this point
        # Note: Origin is chosen such that surface geometry follows ccw rotation about building footprint
        if num_surf == 5:
            if tpu_wdir <= 90:
                # Define this surface's origin point (working with TPU 2D plane for contour plots):
                if surf == 1:
                    surf_origin = Point(min(df_csurf['x']), max(df_csurf['y']))
                elif surf == 2:
                    surf_origin = Point(min(df_csurf['x']), min(df_csurf['y']))
                elif surf == 3:
                    surf_origin = Point(max(df_csurf['x']), min(df_csurf['y']))
                elif surf == 4:
                    surf_origin = Point(max(df_csurf['x']), max(df_csurf['y']))
                elif surf == 5:
                    surf_origin = Point(min(df_csurf['x']), min(df_csurf['y']))  # Intersection of surfaces 1 and 2
            elif 90 < tpu_wdir <= 180:
                if surf == 1:
                    surf_origin = Point(max(df_csurf['x']), max(df_csurf['y']))
                elif surf == 2:
                    surf_origin = Point(max(df_csurf['x']), min(df_csurf['y']))
                elif surf == 3:
                    surf_origin = Point(min(df_csurf['x']), min(df_csurf['y']))
                elif surf == 4:
                    surf_origin = Point(min(df_csurf['x']), max(df_csurf['y']))
                elif surf == 5:
                    surf_origin = Point(max(df_csurf['x']), min(df_csurf['y']))
            elif 180 < tpu_wdir <= 270:
                if surf == 1:
                    surf_origin = Point(max(df_csurf['x']), min(df_csurf['y']))
                elif surf == 2:
                    surf_origin = Point(max(df_csurf['x']), max(df_csurf['y']))
                elif surf == 3:
                    surf_origin = Point(min(df_csurf['x']), max(df_csurf['y']))
                elif surf == 4:
                    surf_origin = Point(min(df_csurf['x']), min(df_csurf['y']))
                elif surf == 5:
                    surf_origin = Point(max(df_csurf['x']), max(df_csurf['y']))
            elif 270 < tpu_wdir <= 360:
                if surf == 1:
                    surf_origin = Point(min(df_csurf['x']), min(df_csurf['y']))
                elif surf == 2:
                    surf_origin = Point(min(df_csurf['x']), max(df_csurf['y']))
                elif surf == 3:
                    surf_origin = Point(max(df_csurf['x']), max(df_csurf['y']))
                elif surf == 4:
                    surf_origin = Point(max(df_csurf['x']), min(df_csurf['y']))
                elif surf == 5:
                    surf_origin = Point(min(df_csurf['x']), max(df_csurf['y']))
            # Re-reference surface pressure tap locations according to real-life geometry and orientation:
            for row in df_csurf.index:
                # Find the distance between surf_origin and pressure tap location:
                if surf == 1 or surf == 3:
                    distx = abs(df_csurf.loc[row, 'y'] - surf_origin.y)
                    disty = abs(df_csurf.loc[row, 'x'] - surf_origin.x)
                else:
                    distx = abs(df_csurf.loc[row, 'x'] - surf_origin.x)
                    disty = abs(df_csurf.loc[row, 'y'] - surf_origin.y)
                # Use these distances to define a new point within the real-life geometry:
                if surf != 5:
                    spts = list(surf_dict[surf].exterior.coords)
                    # Surface coordinates at the same elevation follow ccw rotation around building footprint
                    # For wind directions <= 90, this is the direction we want to project in
                    if tpu_wdir < 90 or (180 < tpu_wdir <= 270):
                        surf_2D = LineString([spts[1], spts[2]])
                    else:
                        surf_2D = LineString([spts[2], spts[1]])
                    # Given an x-value, determine the corresponding (x, y) coordinate:
                    proj_pt = surf_2D.interpolate(distx)
                    # Use disty to determine points z location of the surface:
                    rl_point = Point(proj_pt.x, proj_pt.y, disty)
                else:
                    # Use sidelines and surf_dict to determine building orientation:
                    if side_lines['TPU direction'][1] == 'x':
                        pass
                    elif side_lines['TPU direction'][1] == 'y':
                        # Building orientation is determined using surface 1 geometry:
                        rect = bldg.hasGeometry['Footprint'][
                            'local'].minimum_rotated_rectangle  # local coords only for now
                        xrect, yrect = rect.exterior.xy
                        if side_lines['real life direction'][1] == 'y':
                            # Find out the building's orientation:
                            xdist = xrect[3] - xrect[2]
                            ydist = yrect[3] - yrect[2]
                            theta = degrees(atan2(ydist, xdist))
                        else:
                            xdist = xrect[2] - xrect[1]
                            ydist = yrect[2] - yrect[1]
                            theta = degrees(atan2(ydist, xdist)) - 90
                        # Rotate the roof point about the building's equivalent rectangle centroid:
                        rotate_pt = affinity.rotate(Point(df_csurf['x'][row], df_csurf['y'][row]), theta, (0,0))
                        rl_point = Point(rotate_pt.x+surf_dict[5].centroid.x, rotate_pt.y+surf_dict[5].centroid.y, hfull)
                # Save the point's real-life location:
                proj_dict['Real Life Location'].append(rl_point)
                # Save the point's mean Cp and std dev:
                if rl_point.z == 0:
                    proj_dict['Mean Cp'].append(0)
                    proj_dict['Cp Std Dev'].append(0)
                else:
                    proj_dict['Mean Cp'].append(df_csurf['Mean Cp'][row])
                    proj_dict['Cp Std Dev'].append(df_csurf['Cp Std Dev'][row])
        else:
            print('gable and hip roofs not yet supported')
    # Convert the dictionary into a DataFrame:
    df_simple_map = pd.DataFrame(proj_dict).set_index('Index')
    # # Calculate the pressure at each location:
    # pressure_calc = PressureCalc()
    # pressures = []
    # for k in df_simple_map.index.to_list():
    #     #pressures.append(pressure_calc.get_tpu_pressure(wind_speed, df_simple_map['Mean Cp'][k], 'B', df_simple_map['Real Life Location'][k].z, 'mph'))
    #     pressures.append(pressure_calc.get_tpu_pressure(wind_speed, df_simple_map['Mean Cp'][k], 'B', hfull, 'mph'))
    # # Add a new column with the calculated pressures to the DataFrame:
    # df_simple_map['Pressure'] = pressures
    # Plot the real-life pressure tap locations:
    # fig2 = plt.figure()
    # ax2 = plt.axes(projection='3d')
    # for i in df_simple_map['Real Life Location']:
    # ax2.scatter(np.array([i.x])/3.281, np.array([i.y])/3.281, np.array([i.z])/3.281, 'o')
    # plt.show()
    # Plot the full-scale pressures:
    fig3 = plt.figure()
    ax3 = plt.axes(projection='3d')
    rl_xs = []
    rl_ys = []
    rl_zs = []
    for k in df_simple_map.index.to_list():
        rl_xs.append(df_simple_map['Real Life Location'][k].x)
        rl_ys.append(df_simple_map['Real Life Location'][k].y)
        rl_zs.append(df_simple_map['Real Life Location'][k].z)
    img = ax3.scatter3D(np.array([rl_xs]) / 3.281, np.array([rl_ys]) / 3.281, np.array([rl_zs]) / 3.281,
                        c=df_simple_map['Mean Cp'], cmap=plt.get_cmap('copper', 5))
    fig3.colorbar(img)
    # Make the panes transparent:
    ax3.w_xaxis.set_pane_color((1.0, 1.0, 1.0, 1.0))
    ax3.w_yaxis.set_pane_color((1.0, 1.0, 1.0, 1.0))
    ax3.w_zaxis.set_pane_color((1.0, 1.0, 1.0, 1.0))
    # Make the grids transparent:
    ax3.xaxis._axinfo["grid"]['color'] = (1, 1, 1, 0)
    ax3.yaxis._axinfo["grid"]['color'] = (1, 1, 1, 0)
    ax3.zaxis._axinfo["grid"]['color'] = (1, 1, 1, 0)
    # Plot labels
    ax3.set_xlabel('x [m]')
    ax3.set_ylabel('y [m]')
    ax3.set_zlabel('z [m]')
    # Plot all surface geometries for verification
    for key in surf_dict:
        xsurf, ysurf, zsurf = [], [], []
        xr, yr, zr = [], [], []
        for p in list(surf_dict[key].exterior.coords):
            xsurf.append(p[0])
            ysurf.append(p[1])
            zsurf.append(p[2])
        for b in list(rect_surf_dict[key].exterior.coords):
            xr.append(b[0])
            yr.append(b[1])
            zr.append(b[2])
        ax3.plot(np.array(xsurf)/3.281, np.array(ysurf)/3.281, np.array(zsurf)/3.281, linestyle='dashed', color='gray')
        ax3.plot(np.array(xr) / 3.281, np.array(yr) / 3.281, np.array(zr) / 3.281, linestyle='dashed', color='gray')
    plt.show()
    # When geometries between actual building and model building are not fully compatible:
    # Wrap the pressures to the the parcel's full scale geometry:
    if match_flag:
        pass
    else:
        # Pull necessary columns indices:
        # Find index for column we are modifying:
        for r in range(0, len(df_simple_map.columns)):
            if df_simple_map.columns[r] == 'Real Life Location':
                rl_loc = r
                break
            else:
                pass
        # First check if there is a difference between the actual vs. model building height:
        if hfull == h_bldg:
            pass
        else:
            # Quantify the difference between the model bldg height and actual height:
            hscale = h_bldg/hfull
            # Add or subtract the height difference to each coordinate:
            for pt in range(0, len(df_simple_map['Real Life Location'])):
                tap_loc = df_simple_map['Real Life Location'][pt]
                df_simple_map.iat[pt, rl_loc] = Point(tap_loc.x, tap_loc.y, tap_loc.z*hscale)
        # Check difference in depth:
        # Note: No need to check for breadth since these are an exact match
        depth_idx = side_lines['TPU direction'].index('x')
        if dfull == side_lines['length'][depth_idx]:
            pass
        else:
            # In order to wrap the model building geometry to the equivalent rectangle geometry:
            # 1) Translate Surface 1 and 3 planes to the full depth
            # 2) Re-space the coordinates in Surfaces 2, 4, and 5
            for snum in surf_dict:
                # Setting up variables:
                # Pull up the coordinate pairs for the equivalent rectangle and the model bldg geometry (only need x,y):
                xrect, yrect = rect_surf_dict[snum].exterior.xy  # equiv. rect (x,y) pairs
                xmodel, ymodel = surf_dict[snum].exterior.xy  # model bldg (x,y) pairs
                # Determine if this surface has unique x, y values or if it is exception case
                if len(set(xrect)) > 1:
                    xflag = True
                    min_rect_idx = xrect.index(min(xrect))  # first index for minimum x in equiv rect surface description
                    min_idx = xmodel.index(min(xmodel))  # first index for minimum x for model bldg description
                else:
                    xflag = False  # Exception: all x values are the same
                    min_rect_idx = yrect.index(min(yrect))  # first index for minimum x in equiv rect surface description
                    min_idx = ymodel.index(min(ymodel))  # first index for minimum x for model bldg description
                # Calculate the difference in x, y between coordinates:
                xdiff = xrect[min_rect_idx] - xmodel[min_idx]
                ydiff = yrect[min_rect_idx] - ymodel[min_idx]
                # Pull this surface's points from the DataFrame:
                surf_pts = df_simple_map.loc[df_simple_map['Surface Number'] == snum, 'Real Life Location']
                # Go through surfaces:
                if snum == 1 or snum == 3:
                    # Translate all points for this surface:
                    for pt in surf_pts.index.to_list():
                        current_pt = df_simple_map['Real Life Location'][pt]
                        df_simple_map.iat[pt, rl_loc] = Point(current_pt.x + xdiff, current_pt.y + ydiff, current_pt.z)
                else:
                    # To conduct the re-spacing, points are first shifted to the edge of the surface:
                    dist = sqrt(xdiff**2 + ydiff**2)  # distance between model and equiv. rectangle surface corners
                    if side_lines['length'][depth_idx] < dfull:
                        dist = -1*dist
                    else:
                        pass
                    # Determine the model bldg and equiv rect spacing:
                    # Note: xvals previously defined for creating mesh in contour plot: use to determine spacing
                    new_space = side_lines['length'][depth_idx] / (len(xvals) - 1)  # new spacing
                    # To conduct the re-spacing, will need to project cosine and since components for x, y:
                    theta = atan2(ydiff, xdiff)  # Angle of the line
                    # Pull all x and y values for the surface in order to determine multipliers for spacing
                    xpt, ypt = [], []
                    for spt in surf_pts:
                        xpt.append(spt.x)
                        ypt.append(spt.y)
                    x_unique = np.unique(xpt)
                    y_unique = np.unique(ypt)
                    # Update the coordinates for each point in the surface:
                    for pt in surf_pts.index.to_list():
                        current_pt = df_simple_map['Real Life Location'][pt]
                        # Find the index of the current x or y value - used for spacing multipliers:
                        if xflag:
                            idx = np.where(x_unique == current_pt.x)[0] - 1
                        else:
                            idx = np.where(y_unique == current_pt.y)[0] - 1  # Exception: Surf 2 and 4 || to N-S direction
                        if 90 < tpu_wdir <= 270 and snum == 5:
                            # Shift all points to the corner of the windward surface:
                            df_simple_map.iat[pt, rl_loc] = Point(current_pt.x - dist * cos(theta),
                                                                     current_pt.y - dist * sin(theta), current_pt.z)
                        else:
                            # Shift all points to the corner of the windward surface:
                            if side_lines['TPU direction'][1] == 'y' and side_lines['real life direction'][1] == 'y':
                                df_simple_map.iat[pt, rl_loc] = Point(current_pt.x + dist * cos(theta),
                                                                         current_pt.y + dist * sin(theta), current_pt.z)
                            elif side_lines['TPU direction'][1] == 'y' and side_lines['real life direction'][1] == 'x':
                                df_simple_map.iat[pt, rl_loc] = Point(current_pt.x - dist * cos(theta),
                                                                      current_pt.y - dist * sin(theta), current_pt.z)
                        if snum != 5:
                            if current_pt.x == xmodel[min_idx] and current_pt.y == ymodel[min_idx]:
                                pass
                            else:
                                # Shift the point again to create the new spacing:
                                df_simple_map.iat[pt, rl_loc] = Point(xrect[min_rect_idx] - new_space * idx * cos(theta), yrect[min_rect_idx] - new_space * idx * sin(theta), current_pt.z)
                        else:
                            pass
                    if snum != 5:
                        pass
                    else:
                        # Finish new spacing for roof coordinates
                        # Note: Roof coordinates run in the direction of Surfaces 1 and 3
                        point_indices = surf_pts.index.to_list()
                        origin_idx = point_indices[0:len(xvals)]  # Starting points for new spacing (these are at edge)
                        for idx in origin_idx:
                            origin_pt = df_simple_map['Real Life Location'][idx]
                            for multiplier in range(1, len(xvals)):  # Note: origin_idx already where they need to be
                                pt_idx = idx + len(xvals)*multiplier
                                # Note: Point lines are parallel to surface 2 and 4
                                # Use origin pts and multiplier to define new coordinate pairs:
                                if tpu_wdir <= 90:
                                    if side_lines['TPU direction'][1] == 'y' and side_lines['real life direction'][1] == 'y':
                                        df_simple_map.iat[pt_idx, rl_loc] = Point(origin_pt.x - (new_space * multiplier * cos(theta)), origin_pt.y - (new_space * multiplier * sin(theta)), origin_pt.z)
                                    elif side_lines['TPU direction'][1] == 'y' and side_lines['real life direction'][1] == 'x':
                                        df_simple_map.iat[pt_idx, rl_loc] = Point(
                                            origin_pt.x + (new_space * multiplier * cos(theta)),
                                            origin_pt.y + (new_space * multiplier * sin(theta)), origin_pt.z)
                                elif 90 < tpu_wdir <= 270:
                                    df_simple_map.iat[pt_idx, rl_loc] = Point(
                                        origin_pt.x + (new_space * multiplier * cos(theta)),
                                        origin_pt.y + (new_space * multiplier * sin(theta)), origin_pt.z)
        # Plot the new pressure tap locations and their Cps:
        fig4 = plt.figure()
        ax4 = plt.axes(projection='3d')
        rl_xs, rl_ys, rl_zs = [], [], []
        for k in df_simple_map.index.to_list():
            rl_xs.append(df_simple_map['Real Life Location'][k].x)
            rl_ys.append(df_simple_map['Real Life Location'][k].y)
            rl_zs.append(df_simple_map['Real Life Location'][k].z)
        img = ax4.scatter3D(np.array([rl_xs]) / 3.281, np.array([rl_ys]) / 3.281, np.array([rl_zs]) / 3.281, c=df_simple_map['Mean Cp'], cmap=plt.get_cmap('copper', 5))
        fig4.colorbar(img)
        # Make the panes transparent:
        ax4.w_xaxis.set_pane_color((1.0, 1.0, 1.0, 1.0))
        ax4.w_yaxis.set_pane_color((1.0, 1.0, 1.0, 1.0))
        ax4.w_zaxis.set_pane_color((1.0, 1.0, 1.0, 1.0))
        # Make the grids transparent:
        ax4.xaxis._axinfo["grid"]['color'] = (1, 1, 1, 0)
        ax4.yaxis._axinfo["grid"]['color'] = (1, 1, 1, 0)
        ax4.zaxis._axinfo["grid"]['color'] = (1, 1, 1, 0)
        # Plot labels
        ax4.set_xlabel('x [m]', fontsize=16, labelpad=10)
        ax4.set_ylabel('y [m]', fontsize=16, labelpad=10)
        ax4.set_zlabel('z [m]', fontsize=16, labelpad=10)
        # Set label styles:
        ax4.set_zticks(np.arange(0, 20, 4))
        ax4.xaxis.set_tick_params(labelsize=16)
        ax4.yaxis.set_tick_params(labelsize=16)
        ax4.zaxis.set_tick_params(labelsize=16)
        # Plot the surface geometries for verification
        for key in rect_surf_dict:
            xsurf, ysurf, zsurf = [], [], []
            for p in list(rect_surf_dict[key].exterior.coords):
                xsurf.append(p[0])
                ysurf.append(p[1])
                zsurf.append(p[2])
            ax4.plot(np.array(xsurf) / 3.281, np.array(ysurf) / 3.281, np.array(zsurf) / 3.281, linestyle='dashed', color='gray', linewidth=2)
            # Plot the building 3D Geometry:
        for poly in bldg.hasGeometry['3D Geometry']['local']:
            x_bpoly, y_bpoly, z_bpoly = [], [], []
            for bpt in list(poly.exterior.coords):
                x_bpoly.append(bpt[0])
                y_bpoly.append(bpt[1])
                z_bpoly.append(bpt[2])
                # Plot the building geometry:
            ax4.plot(np.array(x_bpoly)/3.281, np.array(y_bpoly)/3.281, np.array(z_bpoly)/3.281, 'k', linewidth=2)
        plt.show()
        # Last part: Mapping pressures onto the true 3D geometry:
        if not high_value_flag:
            df_bldg_cps = df_simple_map
        else:
            df_simple_map['Surface Match'] = False  # Start by assuming there is not a perfect match with actual geometry
            df_bldg_cps = pd.DataFrame(columns=df_simple_map.columns)  # Create master DataFrame for entire building
            df_roof_cps = pd.DataFrame(columns=df_simple_map.columns)
            # Set up plotting:
            fig5 = plt.figure()
            ax5 = plt.axes(projection='3d')
            # Use the actual constructed building's 3D geometry to define boundaries for the points:
            # First figure out what surface is directly in line with the 3D building geometry:
            for bsurf in bldg.hasGeometry['3D Geometry']['local'][1:]:
                # Skip the surface corresponding to the ground floor:
                # Create a DataFrame to save pressure tap data for this surface:
                if bsurf.exterior.coords[0][2] == bldg.hasGeometry['Height']:
                    roof_flag = True
                else:
                    roof_flag = False
                    df_surf_cps = pd.DataFrame(columns=df_simple_map.columns)
                # Pull the surface geometry:
                xb, yb = bsurf.exterior.xy
                b1 = Point(xb[0], yb[0])
                b2 = Point(xb[2], yb[2])
                # Plot the surface geometry:
                xsurf, ysurf, zsurf = [], [], []
                for surf_pt in list(bsurf.exterior.coords):
                    xsurf.append(surf_pt[0])
                    ysurf.append(surf_pt[1])
                    zsurf.append(surf_pt[2])
                ax5.plot(np.array(xsurf) / 3.281, np.array(ysurf) / 3.281, np.array(zsurf) / 3.281, 'k', linewidth=2)
                rsurf_list = []
                for key in rect_surf_dict:
                    xr, yr = rect_surf_dict[key].exterior.xy
                    if key != 5:
                        range_poly = Polygon([(xr[0], yr[0]), (xr[0], yr[2]), (xr[2], yr[2]), (xr[2], yr[0])])
                    else:
                        range_poly = rect_surf_dict[key]
                    if b1.within(range_poly) and b2.within(range_poly):
                        if key != 5:
                            # Create a polygon to define the range of x,y values for the building's surface:
                            surf_range_poly = Polygon([(xb[0], yb[0]), (xb[0], yb[2]), (xb[2], yb[2]), (xb[2], yb[0])])
                        else:
                            xroof, yroof = bldg.hasGeometry['3D Geometry']['local'][0].exterior.xy
                            roof_pts = []
                            for i in range(0, len(xroof)):
                                roof_pts.append(Point(xroof[i], yroof[i]))
                            surf_range_poly = Polygon(roof_pts)
                        # Pull column indexes:
                        # Find index for column we are modifying:
                        for m in range(0, len(df_simple_map.columns)):
                            if df_simple_map.columns[m] == 'Surface Match':
                                surf_match_col = m
                                break
                            else:
                                pass
                        # Pull the corresponding pressure taps:
                        tap_indices = df_simple_map[df_simple_map['Surface Number'] == key].index.to_list()
                        for tap_idx in tap_indices:
                            ref_pt = Point(df_simple_map['Real Life Location'][tap_idx].x, df_simple_map['Real Life Location'][tap_idx].y)
                            if ref_pt.within(surf_range_poly):
                                df_simple_map.iat[tap_idx, surf_match_col] = True
                                tap_info = df_simple_map.iloc[tap_idx]
                                if key != 5:
                                    df_surf_cps = df_surf_cps.append(tap_info, ignore_index=True)
                                else:
                                    df_roof_cps = df_roof_cps.append(tap_info, ignore_index=True)
                            else:
                                pass
                    elif b1.within(range_poly) or b2.within(range_poly):
                        rsurf_list.append(key)
                    else:
                        pass
                if not roof_flag:
                    if len(rsurf_list) > 1:
                        # Define surface line geometries:
                        bsurf_line = LineString([b1, b2])  # Line geometry of incompatible surface
                        rx1, ry1 = rect_surf_dict[rsurf_list[0]].exterior.xy
                        rx2, ry2 = rect_surf_dict[rsurf_list[1]].exterior.xy
                        rline1 = LineString([(rx1[0], ry1[0]), (rx1[2], ry1[2])])
                        rline2 = LineString([(rx2[0], ry2[0]), (rx2[2], ry2[2])])
                        # Find the shared point between the two surfaces:
                        if rline1.coords[0] == rline2.coords[0] or rline1.coords[0] == rline2.coords[1]:
                            origin_pt = rline1.coords[0]
                        else:
                            origin_pt = rline1.coords[1]
                        # Grab the points for each surface on the model building geometry:
                        surf_pts = df_simple_map[(df_simple_map['Surface Number'] == rsurf_list[0]) | (df_simple_map['Surface Number'] == rsurf_list[1])]
                        # Use a dictionary to keep track of data for this surface:
                        new_dict = {}
                        for col in df_simple_map.columns:
                            new_dict[col] = []
                        # Loop through the surface points
                        # Two things that need to be done here:
                        # (1) For each tap, project the point onto the desired surface and determine if intersection occurs
                        #   (a) Need a perpendicular line from the tap's surface to desired surface at tap location
                        #   (b) Equivalent line is line || to the adjacent surface at the tap location
                        for p in surf_pts.index.to_list():
                            # Calculate the distance between this tap location and the origin_pt:
                            xd = surf_pts['Real Life Location'][p].x - origin_pt[0]
                            yd = surf_pts['Real Life Location'][p].y - origin_pt[1]
                            pt_dist = sqrt(xd**2 + yd**2)
                            # Create the parallel line:
                            if surf_pts['Surface Number'][p] == rsurf_list[0]:
                                pline = rline2.parallel_offset(pt_dist, side='Left')
                            else:
                                pline = rline1.parallel_offset(pt_dist, side='Left')
                            # Determine if intersection occurs with desired surface:
                            int_flag = pline.intersects(bsurf_line)
                            if int_flag:
                                int_pt = pline.intersection(bsurf_line)
                                # Save this point's information:
                                for key in new_dict:
                                    if key == 'Real Life Location':
                                        new_dict[key].append(Point(int_pt.x, int_pt.y, surf_pts['Real Life Location'][p].z))
                                    else:
                                        new_dict[key].append(surf_pts[key][p])
                            else:
                                pass
                        # Create a new dictionary to hold the final pressure tap locations and pressures:
                        proj_tap_dict = {}
                        for key in new_dict:
                            proj_tap_dict[key] = []
                        # Loop through projected points, check if there is a duplicate point (from other surface)
                        # In case of duplicate point, choose the larger pressure:
                        for row in range(0, len(new_dict['Real Life Location'])):
                            new_pt = new_dict['Real Life Location'][row]
                            # Check for a duplicate point:
                            if new_dict['Real Life Location'].count(new_pt) > 1:
                                # Find the duplicate point:
                                try:
                                    dup_idx = new_dict['Real Life Location'][row:].index(new_pt) + row  # Use remaining part of list
                                    # Choose the larger pressure:
                                    if abs(new_dict['Pressure'][row]) > abs(new_dict['Pressure'][dup_idx]):
                                        pmax = new_dict['Pressure'][row]
                                    else:
                                        pmax = new_dict['Pressure'][dup_idx]
                                    # Add the tap information to the final dictionary:
                                    for k in proj_tap_dict:
                                        if k == 'Pressure':
                                            proj_tap_dict[k].append(pmax)
                                        else:
                                            proj_tap_dict[k].append(new_dict[k][row])
                                except:
                                    pass  # Case when duplicate point has already been taken care of earlier in the loop
                            else:
                                for k in proj_tap_dict:
                                    proj_tap_dict[k].append(new_dict[k][row])
                        df_tap_info = pd.DataFrame(new_dict)
                        # Add this information to the surface's DataFrame:
                        df_surf_cps = df_surf_cps.append(df_tap_info, ignore_index=True)
                    else:
                        # Grab any edge roof points:
                        for tap in df_surf_cps.index.to_list():
                            tap_pt = df_surf_cps['Real Life Location'][tap]
                            if round(tap_pt.z, 4) == round(bldg.hasGeometry['Height'], 4):
                                roof_taps = df_simple_map.loc[df_simple_map['Surface Number'] == 5]
                                for rtap in roof_taps.index.to_list():
                                    if round(roof_taps['Real Life Location'][rtap].x, 4) == round(tap_pt.x,4) and round(roof_taps['Real Life Location'][rtap].y,4) == round(tap_pt.y,4):
                                        rtap_info = df_simple_map.iloc[rtap]
                                        df_roof_cps = df_roof_cps.append(rtap_info, ignore_index=True)
                                    else:
                                        pass
                            else:
                                pass
                else:
                    pass
                # Load the surface and its corresponding DataFrame into the building's data model:
                if roof_flag:
                    roof_poly = bsurf
                else:
                    #bldg.hasDemand['wind pressure']['external']['surfaces'].append(bsurf)
                    #bldg.hasDemand['wind pressure']['external']['values'].append(df_surf_cps)
                    # Add the surface pressure tap data to the master DataFrame:
                    df_bldg_cps = df_bldg_cps.append(df_surf_cps, ignore_index=True)
            # Save the roof surface and data:
            #bldg.hasDemand['wind pressure']['external']['surfaces'].append(roof_poly)
            #bldg.hasDemand['wind pressure']['external']['values'].append(df_roof_cps)
            df_bldg_cps = df_bldg_cps.append(df_roof_cps, ignore_index=True)
            df_bldg_cps = ptap_adjust(df_bldg_cps, bldg)
            # Plot the projected pressure taps:
            xf, yf, zf = [], [], []
            for k in df_bldg_cps.index.to_list():
                xf.append(df_bldg_cps['Real Life Location'][k].x)
                yf.append(df_bldg_cps['Real Life Location'][k].y)
                zf.append(df_bldg_cps['Real Life Location'][k].z)
            img = ax5.scatter3D(np.array([xf]) / 3.281, np.array([yf]) / 3.281, np.array([zf]) / 3.281,
                                c=df_bldg_cps['Mean Cp'], cmap=plt.get_cmap('copper', 5))
            fig5.colorbar(img)
            ax5.set_xlim(left=-20, right=20)
            ax5.set_ylim3d(bottom=-20, top=20)
            # Make the panes transparent:
            ax5.w_xaxis.set_pane_color((1.0, 1.0, 1.0, 1.0))
            ax5.w_yaxis.set_pane_color((1.0, 1.0, 1.0, 1.0))
            ax5.w_zaxis.set_pane_color((1.0, 1.0, 1.0, 1.0))
            # Make the grids transparent:
            ax5.xaxis._axinfo["grid"]['color'] = (1, 1, 1, 0)
            ax5.yaxis._axinfo["grid"]['color'] = (1, 1, 1, 0)
            ax5.zaxis._axinfo["grid"]['color'] = (1, 1, 1, 0)
            # Plot labels
            ax5.set_xlabel('x [m]', fontsize=14, labelpad=10)
            ax5.set_ylabel('y [m]', fontsize=14, labelpad=10)
            ax5.set_zlabel('z [m]', fontsize=14, labelpad=10)
            # Set label styles:
            ax5.set_zticks(np.arange(0, 20, 4))
            ax5.xaxis.set_tick_params(labelsize=14)
            ax5.yaxis.set_tick_params(labelsize=14)
            ax5.zaxis.set_tick_params(labelsize=14)
            plt.show()
        # Final step: Get tap tributary areas:
        df_bldg_cps = get_tap_trib_areas(bldg, df_bldg_cps, high_value_flag, roof_flag=True, facade_flag=True)
    return df_bldg_cps


def map_gable_roof_tap_data(tpu_wdir, model_file, bfull, hfull, dfull, side_lines, surf_dict, match_flag, h_bldg, rect, bldg, high_value_flag):
    # 1) Read in pressure data file and add to a DataFrame:
    tpu_file = 'D:/Users/Karen/Documents/Github/DPBWE/Datasets/TPU/' + model_file
    tpu_data = loadmat(tpu_file)
    # Export Location_of_measured_points into a DataFrame for easier manipulation:
    df = pd.DataFrame(tpu_data['Location_of_measured_points'], index=['x', 'y', 'Point Number', 'Surface Number'])
    df = df.T
    # 2) Quantify the mean Cp and std_dev for each pressure tap location and add to DataFrame:
    mean_cps = []
    std_dev = []
    for pnum in df['Point Number']:
        mean_cps.append(np.mean(tpu_data['Wind_pressure_coefficients'][:, int(pnum) - 1]))
        std_dev.append(np.std(tpu_data['Wind_pressure_coefficients'][:, int(pnum) - 1]))
    df['Mean Cp'] = mean_cps
    df['Cp Std Dev'] = std_dev
    # 3) Drop any points not on the roof and convert coordinate positions to ft:
    facade_indices = df.loc[df['Surface Number'] < 5].index.to_list()
    df = df.drop(facade_indices)
    df['x'] = df['x'] / 305
    df['y'] = df['y'] / 305
    # Start by plotting out the points to see what they look like:
    # plt.plot(df['x'], df['y'], 'o')
    #plt.show()
    # 4) Convert pressure tap locations to full-scale (in [ft]):
    df['x'] = df['x'] * (dfull / (tpu_data['Building_depth'][0][0] / 305))
    df['y']= df['y'] * (bfull / (tpu_data['Building_breadth'][0][0] / 305))
    # Uncomment next two lines to show full-scale conversion of pressure tap locations:
    # plt.plot(df['x'], df['y'], 'o')
    # plt.show()
    # 5) Contour plots/interpolating data - necessary to wrap onto real-life geometries
    # Set up placeholders to save contour plot coefficients:
    contour_values = {'x': [], 'y': [], 'Surface Number': [], 'Mean Cp': [], 'Cp Std Dev': []}
    # Step 4a: To create Cp values for entire surface, need to first define points at surface boundaries and add data
    # Grab max and min values for x, y, respectively (pressure tap locations)
    min_x = min(df['x'])
    max_x = max(df['x'])
    min_y = min(df['y'])
    max_y = max(df['y'])
    # Need the indices of our four extreme points in original data to extract their Cp values
    # Idea here: simply extend Cp values to the extremes of the geometry (actual values may be higher/lower)
    xs = [min_x, min_x, max_x, max_x]
    ys = [min_y, max_y, min_y, max_y]
    ind_list = []
    for j in range(0, len(xs)):
        ind_list.append(df.loc[((df['x'] == xs[j]) & (df['y'] == ys[j])), 'Point Number'].index.to_list()[0])
    # Assign boundary geometry based off of full-scale dim
    px = [-dfull / 2, dfull / 2, dfull / 2, -dfull / 2]
    py = [-bfull / 2, -bfull / 2, bfull / 2, bfull / 2]
    surf_num_list = [5, 5, 6, 6]
    boundary_cps = [df['Mean Cp'][ind_list[0]], df['Mean Cp'][ind_list[2]],
                    df['Mean Cp'][ind_list[3]], df['Mean Cp'][ind_list[1]]]
    boundary_std_devs = [df['Cp Std Dev'][ind_list[0]], df['Cp Std Dev'][ind_list[2]],
                        df['Cp Std Dev'][ind_list[3]], df['Cp Std Dev'][ind_list[1]]]
    # Add in new locations and filler Cp data:
    for pt in range(0, len(px)):
        df = df.append({'x': px[pt], 'y': py[pt], 'Point Number': df['Point Number'].iloc[-1] + 1,
                        'Surface Number': surf_num_list[pt], 'Mean Cp': boundary_cps[pt], 'Cp Std Dev': boundary_std_devs[pt]}, ignore_index=True)
    # Up to this point, code designates the four points marking quadrilateral geometry
    # Determine remaining boundary geometries (points within line segments) and assign pressure coefficients:
    max_surf5_y = df.loc[df['Surface Number']==5, 'y'].max()
    index_list = df.index.to_list()
    # Loop through xcoords and create horizontal boundaries
    for x in index_list:
        if df['x'][x] == min_x:  # recall that this is original min_x
            if df['y'][x] > max_surf5_y:
                snum = 6
            else:
                snum = 5
            # Add new point to DataFrame and use current point's mean Cp:
            df = df.append({'x': min_x, 'y': df['y'][x],
                            'Point Number': df['Point Number'].iloc[-1] + 1, 'Surface Number': snum,
                            'Mean Cp': df['Mean Cp'][x], 'Cp Std Dev': df['Cp Std Dev'][x]}, ignore_index=True)
        elif df['x'][x] == max_x:
            if df['y'][x] > max_surf5_y:
                snum = 6
            else:
                snum = 5
            df = df.append({'x': max_x, 'y': df['y'][x],
                            'Point Number': df['Point Number'].iloc[-1] + 1, 'Surface Number': snum,
                            'Mean Cp': df['Mean Cp'][x], 'Cp Std Dev': df['Cp Std Dev'][x]}, ignore_index=True)
    # Loop through ycoords and create vertical boundaries:
    for y in index_list:
        if df['y'][y] == min_y:
            # Add new point to DataFrame and use current point's mean Cp:
            df = df.append({'x': df['x'][y], 'y': min_y,
                            'Point Number': df['Point Number'].iloc[-1] + 1, 'Surface Number': 5,
                            'Mean Cp': df['Mean Cp'][y], 'Cp Std Dev': df['Cp Std Dev'][y]}, ignore_index=True)
        elif df['y'][y] == max_y:
            df = df.append({'x': df['x'][y], 'y': max_y,
                            'Point Number': df['Point Number'].iloc[-1] + 1, 'Surface Number': 6,
                            'Mean Cp': df['Mean Cp'][y], 'Cp Std Dev': df['Cp Std Dev'][y]}, ignore_index=True)
    # Step 3b: Create contours of pressure coefficients:
    # Create x and y meshgrids:
    xvals = np.linspace(df['x'].min(), df['x'].max(), 10)
    yvals = np.linspace(df['y'].min(), df['y'].max(), 10)
    x, y = np.meshgrid(xvals, yvals)
    # Determine the corresponding "z" (i.e., Mean Cp, std dev) values:
    points = np.column_stack((df['x'], df['y']))
    mcp_zvals = griddata(points, df['Mean Cp'], (x, y), method='cubic')
    std_dev_zvals = griddata(points, df['Cp Std Dev'], (x, y), method='cubic')
    # Save the (x, y) coordinate pairs and their corresponding Cp according to surface number:
    for col in range(0, len(xvals)):
        for row in range(0, len(yvals)):
            # Record x and y-values:
            contour_values['x'].append(xvals[col])
            contour_values['y'].append(yvals[row])
            # Record the surface number:
            if yvals[row] > 0:
                contour_values['Surface Number'].append(6)
            else:
                contour_values['Surface Number'].append(5)
            # Grab the mean Cp and std dev corresponding to this (x,y) pair:
            contour_values['Mean Cp'].append(mcp_zvals[row][col])
            contour_values['Cp Std Dev'].append(std_dev_zvals[row][col])
    # Uncomment to produce 2D contour plots:
    #cp = plt.contourf(x, y, mcp_zvals)
    # cp = plt.contourf(x, y, std_dev_zvals)
    # plt.colorbar()
    # plt.show()
    # Create a new DataFrame with new set of (x, y) and Cps:
    df_contour = pd.DataFrame(contour_values)
    # 6): Coordinate transformation (for tpu_wdir > 90)
    if tpu_wdir > 90:
        # Find index for column we are modifying:
        for col in range(0, len(df_contour.columns)):
            if df_contour.columns[col] == 'x':
                x_col = col
            elif df_contour.columns[col] == 'y':
                y_col = col
            else:
                pass
        # Apply transformations:
        if 90 < tpu_wdir <= 180:
            # Reflect over the x-axis:
            df_contour['x'] = -1 * df_contour['x']
        elif 180 < tpu_wdir <= 270:
            # Reflect over x-axis and y-axis:
            df_contour['x'] = -1 * df_contour['x']
            df_contour['y'] = -1 * df_contour['y']
        else:
            # Reflect coordinates over y-axis:
            df_contour['y'] = -1 * df_contour['y']
    else:
        pass
    # 5) Mapping pressure tap locations to real-life scenario::
    proj_dict = {'Index': df_contour.index.to_list(), 'Real Life Location': [],
                 'Surface Number': df_contour['Surface Number'].to_list(), 'Mean Cp': [], 'Cp Std Dev': []}
    upoly = surf_dict[5].union(surf_dict[6])
    # Re-reference surface pressure tap locations according to real-life geometry and orientation:
    for row in df_contour.index:
        # Use sidelines and surf_dict to determine orientation of roof taps:
        if side_lines['TPU direction'][1] == 'x':
            pass
        elif side_lines['TPU direction'][1] == 'y':
            # Building orientation is determined using surface 1 geometry:
            #rect = bldg.hasGeometry['Footprint']['local'].minimum_rotated_rectangle  # local coords only for now
            xrect, yrect = rect.exterior.xy
            if side_lines['real life direction'][1] == 'y':
                # Find out the building's orientation:
                xdist = xrect[3] - xrect[2]
                ydist = yrect[3] - yrect[2]
                theta = degrees(atan2(ydist, xdist))
            else:
                xdist = xrect[2] - xrect[1]
                ydist = yrect[2] - yrect[1]
                theta = degrees(atan2(ydist, xdist)) - 90
            # Rotate the roof point about the building's equivalent rectangle centroid:
            rotate_pt = affinity.rotate(Point(df_contour['x'][row], df_contour['y'][row]), theta, (0,0))
            rl_point = Point(rotate_pt.x + upoly.centroid.x, rotate_pt.y + upoly.centroid.y, hfull)
        # Save the point's real-life location:
        proj_dict['Real Life Location'].append(rl_point)
        # Save the point's mean Cp value:
        if rl_point.z == 0:
            proj_dict['Mean Cp'].append(0)
            proj_dict['Cp Std Dev'].append(0)
        else:
            proj_dict['Mean Cp'].append(df_contour['Mean Cp'][row])
            proj_dict['Cp Std Dev'].append(df_contour['Cp Std Dev'][row])
    # Convert the dictionary into a DataFrame:
    df_simple_map = pd.DataFrame(proj_dict).set_index('Index')
    # Plot the full-scale geometries and taps + Cps:
    # fig3 = plt.figure()
    # ax3 = plt.axes(projection='3d')
    rl_xs = []
    rl_ys = []
    rl_zs = []
    for k in df_simple_map.index.to_list():
        rl_xs.append(df_simple_map['Real Life Location'][k].x)
        rl_ys.append(df_simple_map['Real Life Location'][k].y)
        rl_zs.append(df_simple_map['Real Life Location'][k].z)
    # img = ax3.scatter3D(np.array([rl_xs]) / 3.281, np.array([rl_ys]) / 3.281, np.array([rl_zs]) / 3.281,
    #                     c=df_simple_map['Mean Cp'], cmap=plt.get_cmap('copper', 5))
    # fig3.colorbar(img)
    # Make the panes transparent:
    # ax3.w_xaxis.set_pane_color((1.0, 1.0, 1.0, 1.0))
    # ax3.w_yaxis.set_pane_color((1.0, 1.0, 1.0, 1.0))
    # ax3.w_zaxis.set_pane_color((1.0, 1.0, 1.0, 1.0))
    # # Make the grids transparent:
    # ax3.xaxis._axinfo["grid"]['color'] = (1, 1, 1, 0)
    # ax3.yaxis._axinfo["grid"]['color'] = (1, 1, 1, 0)
    # ax3.zaxis._axinfo["grid"]['color'] = (1, 1, 1, 0)
    # # Plot labels
    # ax3.set_xlabel('x [m]')
    # ax3.set_ylabel('y [m]')
    # ax3.set_zlabel('z [m]')
    # Plot all the model building's surface geometries for verification
    for key in surf_dict:
        xsurf, ysurf, zsurf = [], [], []
        for p in list(surf_dict[key].exterior.coords):
            xsurf.append(p[0])
            ysurf.append(p[1])
            zsurf.append(p[2])
        # ax3.plot(np.array(xsurf) / 3.281, np.array(ysurf) / 3.281, np.array(zsurf) / 3.281, linestyle='dashed',
        #          color='gray')
    # Plot the building's rectangular roof geometry:
    xr, yr = bldg.hasGeometry['Footprint']['local'].minimum_rotated_rectangle.exterior.xy
    # ax3.plot(np.array(xr) / 3.281, np.array(yr) / 3.281, np.ones(len(xr))*bldg.hasGeometry['Height'] / 3.281, linestyle='dashed', color='gray')
    # plt.show()
    # When geometries between actual building and model building are not fully compatible:
    # Wrap the pressures to the the parcel's full scale geometry:
    if match_flag:
        pass
    else:
        # Set up scale factors:
        hscale = h_bldg / hfull
        bscale = 1
        dscale = max(side_lines['length'])/dfull
        # Scale roof taps to actual constructed building's dimensions (rectangular representation):
        if side_lines['TPU direction'][0] == side_lines['real life direction'][0]:
            df_simple_map['Real Life Location'] = df_simple_map['Real Life Location'].apply(
                lambda x: affinity.scale(x, xfact=dscale, yfact=bscale, zfact=hscale, origin=(0, 0, 0)))
        else:
            df_simple_map['Real Life Location'] = df_simple_map['Real Life Location'].apply(
                lambda x: affinity.scale(x, xfact=bscale, yfact=dscale, zfact=hscale, origin=(0, 0, 0)))
        # Plot the new pressure tap locations and their Cps:
        # fig4 = plt.figure()
        # ax4 = plt.axes(projection='3d')
        rl_xs, rl_ys, rl_zs = [], [], []
        for k in df_simple_map.index.to_list():
            rl_xs.append(df_simple_map['Real Life Location'][k].x)
            rl_ys.append(df_simple_map['Real Life Location'][k].y)
            rl_zs.append(df_simple_map['Real Life Location'][k].z)
        # img = ax4.scatter3D(np.array([rl_xs]) / 3.281, np.array([rl_ys]) / 3.281, np.array([rl_zs]) / 3.281, c=df_simple_map['Mean Cp'], cmap=plt.get_cmap('copper', 5))
        # fig4.colorbar(img)
        # # Make the panes transparent:
        # ax4.w_xaxis.set_pane_color((1.0, 1.0, 1.0, 1.0))
        # ax4.w_yaxis.set_pane_color((1.0, 1.0, 1.0, 1.0))
        # ax4.w_zaxis.set_pane_color((1.0, 1.0, 1.0, 1.0))
        # # Make the grids transparent:
        # ax4.xaxis._axinfo["grid"]['color'] = (1, 1, 1, 0)
        # ax4.yaxis._axinfo["grid"]['color'] = (1, 1, 1, 0)
        # ax4.zaxis._axinfo["grid"]['color'] = (1, 1, 1, 0)
        # # Plot labels
        # ax4.set_xlabel('x [m]', fontsize=16, labelpad=10)
        # ax4.set_ylabel('y [m]', fontsize=16, labelpad=10)
        # ax4.set_zlabel('z [m]', fontsize=16, labelpad=10)
        # # Set label styles:
        # ax4.set_zticks(np.arange(0, 20, 4))
        # ax4.xaxis.set_tick_params(labelsize=16)
        # ax4.yaxis.set_tick_params(labelsize=16)
        # ax4.zaxis.set_tick_params(labelsize=16)
        # # Plot the building's equivalent rectangle roof for verification:
        # ax4.plot(np.array(xr) / 3.281, np.array(yr) / 3.281, np.ones(len(xr))*bldg.hasGeometry['Height'] / 3.281, linestyle='dashed', color='gray', linewidth=2)
        # # Plot the building's actual planar roof geometry:
        xb, yb = bldg.hasGeometry['Footprint']['local'].exterior.xy
        # ax4.plot(np.array(xb)/3.281, np.array(yb)/3.281, np.ones(len(xb))*bldg.hasGeometry['Height']/3.281, 'k', linewidth=2)
        # plt.show()
        # Last part: Mapping pressures onto the true 3D geometry:
        if not high_value_flag:
            df_bldg_cps = df_simple_map
        else:
            print('High value roof mapping not available at this time')
        # Final step: Get tap tributary areas:
        df_bldg_cps = get_tap_trib_areas(bldg, df_bldg_cps, high_value_flag, roof_flag=True, facade_flag=False)
    return df_bldg_cps


def ptap_adjust(df_bldg_cps, bldg):
    # Use the building footprint to ensure pressure taps are intersecting:
    xf, yf = bldg.hasGeometry['Footprint']['local'].exterior.xy
    # Gather all unique x, y pairs for a given elevation:
    xys = []
    for i in df_bldg_cps.index.to_list():
        if df_bldg_cps['Real Life Location'][i].z != bldg.hasGeometry['Height']:
            xtap = df_bldg_cps['Real Life Location'][i].x
            ytap = df_bldg_cps['Real Life Location'][i].y
            if (xtap, ytap) in xys:
                pass
            else:
                xys.append((xtap, ytap))
        else:
            pass
    # Use points around building footprint to create line geometries and create bounding box per line:
    footprint_bounds = {'lines': [], 'bounding boxes': []}
    for k in range(0, len(xf)-1):
        new_line = LineString([(xf[k], yf[k]), (xf[k+1], yf[k+1])])
        footprint_bounds['lines'].append(new_line)
        xl, yl = new_line.xy
        bound_poly = Polygon([(min(xl), min(yl)), (min(xl), max(yl)), (max(xl), max(yl)), (max(xl), min(yl))])
        footprint_bounds['bounding boxes'].append(bound_poly)
    # Implement corrections for any (x,y) that do not intersect building footprint:
    new_xys = []
    for j in xys:
        ref_pt = Point(j)
        if ref_pt.intersects(bldg.hasGeometry['Footprint']['local']):
            new_xys.append(ref_pt)
        else:
            # Find what line this point is supposed to belong to:
            for m in range(0, len(footprint_bounds['lines'])):
                if ref_pt.within(footprint_bounds['bounding boxes'][m]):
                    # Find which point on the line this point is the closest to:
                    xl, yl = footprint_bounds['lines'][m].xy
                    dist1 = Point(xl[0], yl[0]).distance(ref_pt)
                    ipt = footprint_bounds['lines'][m].interpolate(dist1)
                    new_xys.append(ipt)
                else:
                    pass
    # Update (x,y) for each pressure tap on the perimeter:
    # Find Real life location column:
    for col in range(0, len(df_bldg_cps.columns)):
        if df_bldg_cps.columns[col] == 'Real Life Location':
            col_idx = col
            break
        else:
            pass
    for p in df_bldg_cps.index.to_list():
        ptap_loc = df_bldg_cps['Real Life Location'][p]
        # Find the index of this pressure tap's (x, y) pair:
        try:
            xy_idx = xys.index((ptap_loc.x, ptap_loc.y))
            new_pt = new_xys[xy_idx]
            new_ptap_loc = Point(new_pt.x, new_pt.y, ptap_loc.z)
            df_bldg_cps.iat[p, col_idx] = new_ptap_loc
        except ValueError:  # Roof interior pressure taps
            pass
    return df_bldg_cps


def create_zcoords(footprint, zcoord):
    # Input footprint polygon (either local or geodesic) and elevation:
    zs = []
    # Create z coordinates for the given building footprint and elevation:
    xs, ys = footprint.exterior.xy
    for pt in range(0, len(xs)):
        # Define z-coordinates for bottom floor of each story:
        zs.append(Point(xs[pt], ys[pt], zcoord))
    return zs


def convert_to_tpu_wdir(wind_direction, bldg):
    # TPU wind direction is dependent on (1) real-life wind direction AND (2) building's orientation:
    rect = bldg.hasGeometry['Footprint']['local'].minimum_rotated_rectangle  # local coords only for now
    xrect, yrect = rect.exterior.xy
    # Figure out TPU direction of the building:
    side_lines = {'lines': [], 'length': [], 'TPU direction': [], 'real life direction': []}
    # First inventory all lines of the rectangular building geometry:
    max_length = 0  # Initialize dummy variable
    for ind in range(0, len(xrect) - 1):
        # Figure out if the line is dominantly in x or y:
        if abs(xrect[ind] - xrect[ind + 1]) > abs(yrect[ind] - yrect[ind + 1]):
            side_lines['real life direction'].append('x')
        else:
            side_lines['real life direction'].append('y')
        new_line = LineString([(xrect[ind], yrect[ind]), (xrect[ind + 1], yrect[ind + 1])])
        side_lines['lines'].append(new_line)
        side_lines['length'].append(new_line.length)
        # Update the maximum length if needed:
        if new_line.length > max_length:
            max_length = new_line.length
        else:
            pass
    # With the line geometry and their lengths, can now find the TPU direction of each line:
    for line in range(0, len(side_lines['lines'])):
        # For each line, figure out if line is in the TPU x-direction (longer length):
        if side_lines['lines'][line].length == max_length:
            line_direction = 'x'
        else:
            line_direction = 'y'
        # Record line directions:
        side_lines['TPU direction'].append(line_direction)
    if side_lines['TPU direction'][1] == 'y' and side_lines['real life direction'][1] == 'y':
        # Find out the building's orientation:
        xdist = xrect[3] - xrect[2]
        ydist = yrect[3] - yrect[2]
    elif side_lines['TPU direction'][1] == 'y' and side_lines['real life direction'][1] == 'x':
        xdist = xrect[1] - xrect[0]
        ydist = yrect[1] - yrect[0]
    elif side_lines['TPU direction'][1] == 'x' and side_lines['real life direction'][1] == 'y':
        xdist = xrect[2] - xrect[1]
        ydist = yrect[2] - yrect[1]
    theta = degrees(atan2(ydist, xdist))
    # Find the tpu wind direction according to building orientation and IRL wind direction:
    tpu_wdir = wind_direction*-1 + 270 + -1*(theta)
    return tpu_wdir


def map_ptaps_to_components(bldg, df_bldg_cps, roof_flag, facade_flag):
    # 1) Find roof indices (for data segmentation):
    if max(df_bldg_cps['Surface Number']) == 5:
        roof_indices = df_bldg_cps.loc[df_bldg_cps['Surface Number'] == 5].index
    elif max(df_bldg_cps['Surface Number']) == 6:
        roof_indices = df_bldg_cps.loc[(df_bldg_cps['Surface Number'] == 5) | (df_bldg_cps['Surface Number'] == 6)].index
    # 2) Map roof pressure taps to roof sub-elements (this is conducted in the x-y plane):
    if not roof_flag:
        pass
    else:
        for subelem in bldg.adjacentElement['Roof'][0].hasSubElement['cover']:
            subelem.hasDemand['wind pressure']['external'] = {'intersecting area': [], 'tap number': []}
        for idx in roof_indices:
            rtap_poly = df_bldg_cps['Tap Polygon'][idx]
            for subelem in bldg.adjacentElement['Roof'][0].hasSubElement['cover']:
                if rtap_poly.within(subelem.hasGeometry['2D Geometry']['local']) or rtap_poly.intersects(
                        subelem.hasGeometry['2D Geometry']['local']):
                    # Save the tap location and intersecting region:
                    subelem.hasDemand['wind pressure']['external']['tap number'].append(idx)
                    if rtap_poly.within(subelem.hasGeometry['2D Geometry']['local']):
                        subelem.hasDemand['wind pressure']['external']['intersecting area'].append(rtap_poly)
                    else:
                        try:
                            iarea = subelem.hasGeometry['2D Geometry']['local'].intersection(rtap_poly)
                        except TopologicalError:
                            # Get rid of any duplicate points:
                            xe, ye = subelem.hasGeometry['2D Geometry']['local'].exterior.xy
                            new_pts = []
                            for e in range(0, len(xe)):
                                round_x = round(xe[e], 6)
                                round_y = round(ye[e],6)
                                if (round_x, round_y) not in new_pts:
                                    new_pts.append((round_x, round_y))
                                else:
                                    pass
                            # Update sublement geometry:
                            subelem.hasGeometry['2D Geometry']['local'] = Polygon(new_pts)
                            iarea = subelem.hasGeometry['2D Geometry']['local'].intersection(rtap_poly)
                        # Save intersecting area
                        subelem.hasDemand['wind pressure']['external']['intersecting area'].append(iarea)
                else:
                    pass
            # Each pressure tap should be mapped, so if it is not try buffering the polygon:
            # if not map_flag:
            #     # Try buffering the polygon:
            #     bpoly = rtap_poly.buffer(distance=3)
            #     for subelem in bldg.adjacentElement['Roof'][0].hasSubElement['cover']:
            #         if bpoly.intersects(subelem.hasGeometry['2D Geometry']['local']):
            #             subelem.hasDemand['wind pressure']['external'].append(idx)
            #             map_flag = True
            #         else:
            #             pass
            # if not map_flag:
            #     no_map_roof.append(df_roof.loc[idx])
        # print(len(no_map_roof))
    # 3) Map pressure taps to exterior walls:
    if not facade_flag:
        pass
    else:
        # Set up placeholders:
        for wall in bldg.adjacentElement['Walls']:
            wall.hasDemand['wind pressure']['external'] = {'intersecting area': [], 'tap number': []}
        # Get facade pressure taps:
        df_facade = df_bldg_cps.drop(roof_indices)
        no_map = []  # Empty list to hold any unmapped taps (due to numerical error)
        # Mapping: use tap line geometries to map to walls
        for idx in df_facade.index:
            map_flag = False
            tap_pts = df_facade['Tap Polygon'][idx].exterior.coords
            xt, yt, zt = [], [], []
            tap_line_pts = []
            for t in tap_pts:
                xt.append(t[0])
                yt.append(t[1])
                tap_line_pts.append((t[0], t[1]))
                zt.append(t[2])
            tap_line = LineString(tap_line_pts)
            # tap_line = LineString([(min(xt), min(yt)), (max(xt), max(yt))])
            # bound_tap_poly = Polygon([(max(xtap), max(ytap)), (min(xtap), max(ytap)), (min(xtap), min(ytap)), (max(xtap), min(ytap))])
            for story in bldg.hasStory:
                if story.hasElevation[0] <= min(zt) <= story.hasElevation[1] or story.hasElevation[0] <= max(zt) <= story.hasElevation[1]:
                    for wall in story.adjacentElement['Walls']:
                        wall_pts = list(wall.hasGeometry['3D Geometry']['local'].exterior.coords)
                        xw, yw, zw = [], [], []
                        for w in wall_pts:
                            xw.append(w[0])
                            yw.append(w[1])
                            zw.append(w[2])
                        bound_poly = Polygon(
                            [(max(xw), max(yw)), (min(xw), max(yw)), (min(xw), min(yw)), (max(xw), min(yw))])
                        if tap_line.within(bound_poly) or tap_line.intersects(bound_poly):
                            if min(zw) <= min(zt) <= max(zw) or min(zw) <= max(zt) <= max(zw):
                                wall.hasDemand['wind pressure']['external']['tap number'].append(idx)
                                wall.hasDemand['wind pressure']['external']['intersecting area'].append(0)
                                map_flag = True
                            else:
                                pass  # Point within x-y boundary but not wall height (z)
                        else:
                            pass
                else:
                    pass
            if not map_flag:
                no_map.append(idx)


def get_tap_trib_areas(bldg, df_bldg_cps, high_value_flag, roof_flag, facade_flag):
    """
    A function to apply DAD or code-informed pressures onto the building envelope.
    Updates bldg Roof object and/or subelements with pressures and tap information.
    Updates facade elements with pressure and tap information.

    :param bldg: The building that is going to be pressurized.
    :param df_bldg_cps: Output DataFrame from map_tap_data
    :param roof_flag: Boolean, True if trib areas for roof object is the only one needed.
    """
    # 1) Save Cps to Building object if necessary:
    if bldg.hasDemand['wind pressure']['external'] is None:
        bldg.hasDemand['wind pressure']['external'] = df_bldg_cps
    else:
        pass
    # 2) Find tributary areas: Roof
    # 2a) Start with facade components: Find their indices
    if max(df_bldg_cps['Surface Number']) == 5:
        roof_indices = df_bldg_cps.loc[df_bldg_cps['Surface Number'] == 5].index
    elif max(df_bldg_cps['Surface Number']) == 6:
        roof_indices = df_bldg_cps.loc[(df_bldg_cps['Surface Number'] == 5) | (df_bldg_cps['Surface Number'] == 6)].index
    if roof_flag:
        df_roof = df_bldg_cps.iloc[roof_indices]
        # Use voronoi diagram to get 2D pressure tap tributary areas:
        df_roof = get_roof_2d_mesh(bldg, df_roof, high_value_flag)
    else:
        df_roof = None
    # 3) Find tributary areas: Facade
    if facade_flag:
        df_facade = df_bldg_cps.drop(roof_indices)
        df_facade = get_facade_mesh(bldg, df_facade)
    else:
        df_facade = None
    # Figure out what df_bldg_cps will be comprised of:
    if df_roof is None:
        df_bldg_cps = df_facade
    elif df_facade is None:
        df_bldg_cps = df_roof
    else:
        # Put both dataframes back together:
        if min(df_roof.index.to_list()) < min(df_facade.index.to_list()):
            df_bldg_cps = pd.concat([df_roof, df_facade])
        else:
            df_bldg_cps = pd.concat([df_facade, df_roof])
    return df_bldg_cps


def get_facade_mesh(bldg, df_facade):
    # Collect (x, y) tap locations around bldg perimeter:
    perim_points = []
    xp, yp = [], []
    zlist = []
    for idx in df_facade.index:
        ptap_loc = df_facade['Real Life Location'][idx]
        zlist.append(round(ptap_loc.z, 6))
        if ptap_loc.z == 0:
            perim_points.append(ptap_loc)
            xp.append(ptap_loc.x)
            yp.append(ptap_loc.y)
    # Order z locations:
    zlist_order = np.sort(np.array(list(set(zlist))))
    # Order points according to building footprint geometry:
    plist = []
    x, y = bldg.hasGeometry['Footprint']['local'].exterior.xy
    # np_list = []
    # for p in perim_points:
    #     if p.intersects(bldg.hasGeometry['Footprint']['local']):
    #         np_list.append(p)
    #     else:
    #         npt = nearest_points(Point(p.x, p.y), bldg.hasGeometry['Footprint']['local'])
    #         for n in npt:
    #             if n.intersects(bldg.hasGeometry['Footprint']['local']):
    #                 np_list.append(p)
    #             else:
    #                 pass
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
        zidx = np.where(zlist_order==round(ptap_loc.z, 6))[0][0]
        if ptap_loc.z == 0:
            zmin = ptap_loc.z
        else:
            zmin = zlist_order[zidx-1] + (ptap_loc.z-zlist_order[zidx-1])/2
        if round(ptap_loc.z, 6) != max(zlist_order):
            zmax = ptap_loc.z + (zlist_order[zidx+1] - ptap_loc.z)/2
        else:
            zmax = ptap_loc.z
        # Find matching (x, y) for this point:
        poly_list = []
        for p in range(0, len(plist)):
            if ptap_loc.x == plist[p].x and ptap_loc.y == plist[p].y:
                # Find the point between this point and the point preceding it:
                new_line1 = LineString([(ptap_loc.x, ptap_loc.y), (plist[p-1].x, plist[p-1].y)])
                dist1 = Point(ptap_loc.x, ptap_loc.y).distance(plist[p-1])
                ip1 = new_line1.interpolate(distance=dist1/2)
                poly_list.append((ptap_loc.x, ptap_loc.y, zmin))
                poly_list.append((ip1.x, ip1.y, zmin))
                poly_list.append((ip1.x, ip1.y, zmax))
                poly_list.append((ptap_loc.x, ptap_loc.y, zmax))
                if p == len(plist)-1:
                    new_line2 = LineString([(ptap_loc.x, ptap_loc.y), (plist[0].x, plist[0].y)])
                    dist2 = Point(ptap_loc.x, ptap_loc.y).distance(plist[0])
                    ip2 = new_line2.interpolate(distance=dist2/2)
                    poly_list.append((ip2.x, ip2.y, zmax))
                    poly_list.append((ip2.x, ip2.y, zmin))
                else:
                    new_line2 = LineString([(ptap_loc.x, ptap_loc.y), (plist[p + 1].x, plist[p + 1].y)])
                    dist2 = Point(ptap_loc.x, ptap_loc.y).distance(plist[p + 1])
                    ip2 = new_line2.interpolate(distance=dist2/2)
                    poly_list.append((ip2.x, ip2.y, zmax))
                    poly_list.append((ip2.x, ip2.y, zmin))
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
        ax.scatter(ptap_loc.x, ptap_loc.y, ptap_loc.z, color='c')
        coords_list = df_facade['Tap Polygon'][idx].exterior.coords
        xpoly, ypoly, zpoly = [], [], []
        for c in coords_list:
            xpoly.append(c[0])
            ypoly.append(c[1])
            zpoly.append(c[2])
        ax.plot(xpoly, ypoly, zpoly, 'k')
    plt.show()
    return df_facade


def get_roof_2d_mesh(bldg, df_roof, high_value_flag):
    # Get the voronoi discretization of pressure tap areas - element specific:
    # Start with roof elements and their pressure taps:
    coord_list = []
    for idx in df_roof.index:
        ptap_loc = df_roof.loc[idx]['Real Life Location']
        coord_list.append((ptap_loc.x, ptap_loc.y))
    # Adjust roof geometry based on value of property:
    if not high_value_flag:
        bldg.adjacentElement['Roof'][0].hasGeometry['2D Geometry']['local'] = bldg.hasGeometry['Footprint']['local'].minimum_rotated_rectangle
    else:
        bldg.adjacentElement['Roof'][0].hasGeometry['2D Geometry']['local'] = bldg.hasGeometry['Footprint']['local']
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
    # Loop through each pressure tap and add its corresponding polygon:
    tap_poly_list = []
    no_poly_idx = []
    for idx in df_roof.index:
        ptap_loc = df_roof.loc[idx]['Real Life Location']
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
    df_roof.insert(len(df_roof.columns), 'Tap Polygon', tap_poly_list, False)
    # Find which polygons were not mapped:
    no_map_poly = []
    for poly in poly_list:
        if isinstance(poly, Polygon):
            if poly in tap_poly_list:
                pass
            else:
                no_map_poly.append(poly)
    # Buffer points without polygons to find corresponding geometry:
    df_sub = df_roof.loc[no_poly_idx]
    for idx in df_sub.index:
        ptap_loc = df_sub.loc[idx]['Real Life Location']
        bpt = Point(ptap_loc.x, ptap_loc.y).buffer(distance=3)
        for no_map in no_map_poly:
            if bpt.intersects(no_map):
                df_roof.at[idx, 'Tap Polygon'] = no_map
                break
        else:
            pass
    return df_roof