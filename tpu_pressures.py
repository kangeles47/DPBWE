import numpy as np
from math import atan2, degrees, cos, sin, sqrt
from shapely.geometry import Point, Polygon, LineString
from shapely import affinity
from scipy.interpolate import griddata
import matplotlib.pyplot as plt
from scipy.io import loadmat
import pandas as pd
from code_pressures import PressureCalc


def calc_tpu_pressures(bldg, key, tpu_wdir, wind_speed, exposure, edition, cat, hpr):
    # Step 1: Determine the building's TPU use case:
    eave_length = 0
    h_bldg = bldg.hasGeometry['Height']
    match_flag, num_surf, side_lines, model_file, hb_ratio, db_ratio, rect, surf_dict, rect_surf_dict = find_tpu_use_case(bldg, key, tpu_wdir, eave_length)
    bfull, hfull, dfull, rect_surf_dict = get_TPU_surfaces(bldg, key, match_flag, num_surf, side_lines, hb_ratio, db_ratio, rect, tpu_wdir, surf_dict, rect_surf_dict)
    df_tpu_pressures = map_tap_data(tpu_wdir, model_file, num_surf, bfull, hfull, dfull, side_lines, surf_dict, wind_speed, match_flag, h_bldg, rect_surf_dict, bldg)
    return df_tpu_pressures

def find_tpu_use_case(bldg, key, tpu_wdir, eave_length):
    # This function determines the appropriate TPU use case for the given building.
    # Various tags are populated to identify the correct .mat file with TPU data
    # Given a building, determine its corresponding use case:
    # Step 1: wdir_tag:
    if tpu_wdir == 0:
        wdir_tag = '00.mat'
    elif tpu_wdir == 15:
        wdir_tag = '15.mat'
    elif tpu_wdir == 30:
        wdir_tag = '30.mat'
    elif tpu_wdir == 45:
        wdir_tag = '45.mat'
    elif tpu_wdir == 60:
        wdir_tag = '60.mat'
    elif tpu_wdir == 75:
        wdir_tag = '75.mat'
    elif tpu_wdir == 90:
        wdir_tag = '90.mat'
    # Step 2: Determine the building's aspect ratios:
    # Use an equivalent rectangle to calculate aspect ratios:
    rect = bldg.hasGeometry['Footprint']['local'].minimum_rotated_rectangle  # local coords only for now
    xrect, yrect = rect.exterior.xy
    # Determine the lengths of rectangle's sides using line segments:
    side_lines = {'lines': [], 'length': [], 'TPU direction': [], 'TPU line': []}
    max_length = 0  # Initialize dummy variable
    for ind in range(0, len(xrect) - 1):
        new_line = LineString([(xrect[ind], yrect[ind]), (xrect[ind + 1], yrect[ind + 1])])
        side_lines['lines'].append(new_line)
        if key == 'geodesic':
            pass
        else:
            side_lines['length'].append(new_line.length)
            # Update the maximum length if needed:
            if new_line.length > max_length:
                max_length = new_line.length
            else:
                pass
    # With the line geometry and their lengths, can now find the TPU direction of each line:
    for line in range(0, len(side_lines['lines'])):
        # For each line, figure out if line is in the TPU x-direction (longer length):
        if key == 'geodesic':
            pass
        else:
            if side_lines['lines'][line].length == max_length:
                line_direction = 'x'
            else:
                line_direction = 'y'
        # Record line directions:
        side_lines['TPU direction'].append(line_direction)
    # Calculate aspect ratios:
    hb = bldg.hasGeometry['Height'] / min(side_lines['length'])
    db = max(side_lines['length']) / min(side_lines['length'])
    # Step 3: Use the building's aspect ratios to determine its corresponding TPU model building
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
            hb_index = np.where(diff_hbs == closest_hb)
            if not hb_index[0]:
                hb_index = np.where(diff_hbs == closest_hb * -1)
            hb_ratio = model_hbs[hb_index[0]][0]
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
        if bldg.adjacentElement['Roof'].hasShape == 'flat' or bldg.adjacentElement['Roof'].hasShape == 'gable':
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
                db_index = np.where(diff_dbs == closest_db)
                if not db_index[0]:
                    db_index = np.where(diff_dbs == closest_db * -1)
                db_ratio = model_dbs[db_index[0]][0]
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
            if bldg.hasStory[-1].adjacentElement['Roof'].hasShape == 'flat':
                num_surf = 5
                surf_dict = {1: None, 2: None, 3: None, 4: None, 5: None}
                rtag = '00'
            else:
                num_surf = 6
                surf_dict = {1: None, 2: None, 3: None, 4: None, 5: None, 6: None}
                if bldg.adjacentElement['Roof'].hasPitch == 4.8:
                    rtag = '05'
                elif bldg.adjacentElement['Roof'].hasPitch == 9.4:
                    rtag = '10'
                elif bldg.adjacentElement['Roof'].hasPitch == 14:
                    rtag = '14'
                elif bldg.adjacentElement['Roof'].hasPitch == 18.4:
                    rtag = '18'
                elif bldg.adjacentElement['Roof'].hasPitch == 21.8:
                    rtag = '22'
                elif bldg.adjacentElement['Roof'].hasPitch == 26.7:
                    rtag = '27'
                elif bldg.adjacentElement['Roof'].hasPitch == 30:
                    rtag = '30'
                elif bldg.adjacentElement['Roof'].hasPitch == 45:
                    rtag = '45'
            # Initialize string to access the correct model building file:
            model_file = 'Cp_ts_g' + dtag + htag + rtag + wdir_tag
        elif bldg.adjacentElement['Roof'].hasShape == 'hip':  # Note: most common hip roof pitches 4:12-6:12
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


def get_TPU_surfaces(bldg, key, match_flag, num_surf, side_lines, hb_ratio, db_ratio, rect, tpu_wdir, surf_dict, rect_surf_dict):
    # Convert TPU model building geometries into full-scale:
    # Create the TPU footprint geometry from the real-life building's equivalent rectangle:
    if num_surf == 5:
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
    # Set up placeholder for footprint polygon:
    tpu_poly_pts = []
    for line in range(0, len(side_lines['lines'])):
        if side_lines['TPU direction'][line] == 'y':
            # y-direction in TPU corresponds to building breadth
            # Leave alone since breadth is fixed to real-life building geometry
            pass
        else:
            # x-direction in TPU corresponds to building depth:
            # Create two new lines using this line's centroid:
            ref_pt = side_lines['lines'][line].centroid
            line_pts = list(side_lines['lines'][line].coords)
            new_line1 = LineString([ref_pt, Point(line_pts[0])])
            new_line2 = LineString([ref_pt, Point(line_pts[1])])
            # Distribute half of dfull to each line segment:
            new_point1 = new_line1.interpolate(dfull / 2)
            new_point2 = new_line2.interpolate(dfull / 2)
            # Combine the two new points into one LineString:
            tpu_line = LineString([new_point1, new_point2])
            # Save points for footprint polygon:
            tpu_poly_pts.append((new_point1.x, new_point1.y))
            tpu_poly_pts.append((new_point2.x, new_point2.y))
    # Convert footprint points into 3D:
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
                #ax.plot(np.array(surf_xs) / 3.281, np.array(surf_ys) / 3.281, np.array(surf_zs) / 3.281, linestyle='dashed', color='gray')
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
        for poly in bldg.hasGeometry['3D Geometry'][key]:
            x_bpoly, y_bpoly, z_bpoly = [], [], []
            for bpt in list(poly.exterior.coords):
                x_bpoly.append(bpt[0])
                y_bpoly.append(bpt[1])
                z_bpoly.append(bpt[2])
            ax.plot(np.array(x_bpoly)/3.281, np.array(y_bpoly)/3.281, np.array(z_bpoly)/3.281, color='k')
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
    # Plotting: Footprints
    fig_ex = plt.figure()
    ax_ex = plt.axes()
    rfx, rfy = roof_surf.exterior.xy
    ax_ex.plot(np.array(rfx)/3.281, np.array(rfy)/3.281, linestyle='dashed', color='gray')
    xrect, yrect = rect.exterior.xy
    ax_ex.plot(np.array(xrect) / 3.281, np.array(yrect) / 3.281, linestyle='dashed', color='gray')
    # Create general surface geometries:
    xs = [dfull/2, dfull/2, -dfull/2, -dfull/2, dfull/2]
    ys = [-bfull/2, bfull/2, bfull/2, -bfull/2, -bfull/2]
    #ax_ex.plot(np.array(xs)/3.281, np.array(ys)/3.281, linestyle = 'dashed', color='gray')
    # plt.plot(0, 0, 'o', color='gray')
    xbldg, ybldg = bldg.hasGeometry['Footprint']['local'].exterior.xy
    ax_ex.plot(np.array(xbldg) / 3.281, np.array(ybldg) / 3.281, 'k')
    # plt.plot(bldg.hasGeometry['Footprint']['local'].centroid.x/3.281, bldg.hasGeometry['Footprint']['local'].centroid.y/3.281, 'ko')
    ax_ex.xaxis.set_tick_params(labelsize=16)
    ax_ex.yaxis.set_tick_params(labelsize=16)
    ax_ex.set_xlabel('x [m]', fontsize=16)
    ax_ex.set_ylabel('y [m]', fontsize=16)
    plt.show()
    # Next step: Determine the surface numberings:
    # First need to establish which polygons correspond to specific TPU surface numbers:
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
    elif side_lines['TPU direction'][1] == 'y':
        # When TPU x-axis is running in N-S direction (i.e., orthogonal to ideal scenario):
        # TPU surfaces 1, 2, 3, 4, 5 correspond to surfaces in positions 3, 0, 1, 2, 4 in tpu_polys
        if tpu_wdir <= 90:
            # TPU Surface 1 is windward surface and order is ccw: 1, 2, 3, 4, 5
            #poly_order = [3, 0, 1, 2, 4]
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
    for poly in bldg.hasGeometry['3D Geometry'][key]:
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
    bldg.hasGeometry['TPU_surfaces'][key] = surf_dict
    return bfull, hfull, dfull, rect_surf_dict


def map_tap_data(tpu_wdir, model_file, num_surf, bfull, hfull, dfull, side_lines, surf_dict, wind_speed, match_flag, h_bldg, rect_surf_dict, bldg):
    # Read in pressure data file:
    tpu_file = 'C:/Users/Karen/PycharmProjects/DPBWE/Datasets/TPU/' + model_file
    tpu_data = loadmat(tpu_file)
    # Export Location_of_measured_points into a DataFrame for easier manipulation:
    df = pd.DataFrame(tpu_data['Location_of_measured_points'], index=['x', 'y', 'Point Number', 'Surface Number'])
    df = df.T
    # Convert coordinate positions to ft:
    df['x'] = df['x'] / 305
    df['y'] = df['y'] / 305
    # Start by plotting out the points to see what they look like:
    # plt.plot(df['x'], df['y'], 'o')
    plt.show()
    # Step 1: Convert to full-scale dimensions:
    for pt in range(0, len(df['Point Number'])):
        if num_surf == 5 or num_surf == 8:  # Both flat and hip roofs have rectangular vertical planes
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
            # Different approach for roof:
            if num_surf == 5 and df['Surface Number'][pt] == 5:
                df['x'][pt] = df['x'][pt] * (dfull / (tpu_data['Building_depth'][0][0] / 305))
                df['y'][pt] = df['y'][pt] * (bfull / (tpu_data['Building_breadth'][0][0] / 305))
            elif num_surf == 8:
                pass
        elif num_surf == 6:
            pass
    # Uncomment next two lines to show full-scale conversion of pressure tap locations:
    # plt.plot(df['x'], df['y'], 'o')
    # plt.show()
    # Step 2: Determine the mean Cp for each pressure tap location:
    mean_cps = []
    for pnum in df['Point Number']:
        mean_cps.append(np.mean(tpu_data['Wind_pressure_coefficients'][:, int(pnum) - 1]))
    # Add this information to the Dataframe:
    df['Mean Cp'] = mean_cps
    # Step 3: Contour plots/interpolating data
    # Set up placeholders to save contour plot coefficients:
    contour_values = {'x': [], 'y': [], 'Surface Number': [], 'Mean Cp': []}
    # Step 3a: To create Cp values for entire surface, need to first define points at surface boundaries and add data
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
            elif surf == 2 or surf == 4:
                dim_x = (dfull - (abs(max_x - min_x))) / 2
                dim_y = (hfull - (abs(max_y - min_y))) / 2
                px = [min_x - dim_x, max_x + dim_x, max_x + dim_x, min_x - dim_x]
                py = [min_y - dim_y, min_y - dim_y, max_y + dim_y, max_y + dim_y]
                boundary_cps = [df_surf['Mean Cp'][ind_list[0]], df_surf['Mean Cp'][ind_list[2]],
                                df_surf['Mean Cp'][ind_list[3]], df_surf['Mean Cp'][ind_list[1]]]
            elif surf == 5:
                # Add points for surface 5:
                px = [-dfull / 2, dfull / 2, dfull / 2, -dfull / 2]
                py = [-bfull / 2, -bfull / 2, bfull / 2, bfull / 2]
                boundary_cps = [df_surf['Mean Cp'][ind_list[0]], df_surf['Mean Cp'][ind_list[2]],
                                df_surf['Mean Cp'][ind_list[3]], df_surf['Mean Cp'][ind_list[1]]]
            # Add in new locations and filler Cp data:
            for pt in range(0, len(px)):
                df = df.append({'x': px[pt], 'y': py[pt], 'Point Number': df['Point Number'].iloc[-1] + 1,
                                'Surface Number': 1 * surf, 'Mean Cp': boundary_cps[pt]}, ignore_index=True)
            # Up to this point, code designates the four points marking quadrilateral geometry
            # Determine remaining boundary geometries (points within line segments) and assign pressure coefficients:
            xcoords = df.loc[df['Surface Number'] == surf, 'x']
            ycoords = df.loc[df['Surface Number'] == surf, 'y']
            mcps = df.loc[df['Surface Number'] == surf, 'Mean Cp']
            index_list = xcoords.index.to_list()
            # Loop through xcoords and create horizontal boundaries
            for x in index_list:
                if xcoords[x] == min_x:  # recall that this is original min_x
                    # Add new point to DataFrame and use current point's mean Cp:
                    df = df.append({'x': min(df.loc[df['Surface Number'] == surf, 'x']), 'y': ycoords[x],
                                    'Point Number': df['Point Number'].iloc[-1] + 1, 'Surface Number': 1 * surf,
                                    'Mean Cp': mcps[x]}, ignore_index=True)
                elif xcoords[x] == max_x:
                    df = df.append({'x': max(df.loc[df['Surface Number'] == surf, 'x']), 'y': ycoords[x],
                                    'Point Number': df['Point Number'].iloc[-1] + 1, 'Surface Number': 1 * surf,
                                    'Mean Cp': mcps[x]}, ignore_index=True)
            # Loop through ycoords and create vertical boundaries:
            for y in index_list:
                if ycoords[y] == min_y:  # recall that this is original min_x
                    # Add new point to DataFrame and use current point's mean Cp:
                    df = df.append({'x': xcoords[y], 'y': min(df.loc[df['Surface Number'] == surf, 'y']),
                                    'Point Number': df['Point Number'].iloc[-1] + 1, 'Surface Number': 1 * surf,
                                    'Mean Cp': mcps[y]}, ignore_index=True)
                elif ycoords[y] == max_y:
                    df = df.append({'x': xcoords[y], 'y': max(df.loc[df['Surface Number'] == surf, 'y']),
                                    'Point Number': df['Point Number'].iloc[-1] + 1, 'Surface Number': 1 * surf,
                                    'Mean Cp': mcps[y]}, ignore_index=True)
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
        # Determine the corresponding "z" (i.e., Cp) values:
        points = np.column_stack((df.loc[df['Surface Number'] == surf, 'x'], df.loc[df['Surface Number'] == surf, 'y']))
        zvals = griddata(points, surf_cps, (x, y), method='cubic')
        # Save the (x, y) coordinate pairs and their corresponding Cp according to surface number:
        for col in range(0, len(xvals)):
            for row in range(0, len(yvals)):
                # Record x and y-values:
                contour_values['x'].append(xvals[col])
                contour_values['y'].append(yvals[row])
                # Record the surface number:
                contour_values['Surface Number'].append(surf)
                # Grab the Cp value corresponding to this (x,y) pair:
                contour_values['Mean Cp'].append(zvals[row][col])
        # Uncomment to produce 2D contour plots:
        # cp = plt.contourf(x, y, zvals)
        # plt.colorbar()
        # plt.show()
    # Create a new DataFrame with new set of (x, y) and Cps:
    df_contour = pd.DataFrame(contour_values)
    # Step 3b: Coordinate transformation (for tpu_wdir > 90)
    if tpu_wdir > 90:
        for row in range(0, len(df_contour['Mean Cp'])):
            surf_num = df_contour['Surface Number'][row]
            if 90 < tpu_wdir <= 180:
                if surf_num == 1 or surf_num == 3 or surf_num == 5:
                    # Reflect Surface 1, 3, and 5 coordinates over x-axis:
                    df_contour['x'][row] = df_contour['x'][row] * -1
                elif surf_num == 2 or surf_num == 4:
                    # Reflect Surface 2 and 4 coordinates over x-axis:
                    df_contour['y'][row] = df_contour['y'][row] * -1
            elif 180 < tpu_wdir <= 270:
                    # Reflect all Surface coordinates over x-axis and y-axis:
                    df_contour['x'][row] = df_contour['x'][row] * -1
                    df_contour['y'][row] = df_contour['y'][row] * -1
            else:
                if surf_num == 1 or surf_num == 3 or surf_num == 5:
                    # Reflect Surface 1, 3, and 5 coordinates over x-axis:
                    df_contour['y'][row] = df_contour['y'][row] * -1
                elif surf_num == 2 or surf_num == 4:
                    # Reflect Surface 2 and 4 coordinates over x-axis:
                    df_contour['x'][row] = df_contour['x'][row] * -1
    else:
        pass
    # Step 4: Mapping pressure tap locations to real-life scenario and calculating pressure
    proj_dict = {'Index': [], 'Real Life Location': [], 'Surface Number': [], 'Mean Cp': []}
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
                    else:
                        # Building orientation is determined using surface 1 geometry:
                        spts = list(surf_dict[1].exterior.coords)
                        theta = degrees(atan2((spts[1][0]-spts[2][0]), (spts[1][1]-spts[2][1])))
                        # Rotate the roof point about the building's equivalent rectangle centroid:
                        rotate_pt = affinity.rotate(Point(df_csurf.loc[row, 'x'], df_csurf.loc[row, 'y']), -1*theta, (0,0))
                        rl_point = Point(rotate_pt.x+surf_dict[5].centroid.x, rotate_pt.y+surf_dict[5].centroid.y, hfull)
                # Save the point's real-life location:
                proj_dict['Real Life Location'].append(rl_point)
                # Save the point's mean Cp value:
                if rl_point.z == 0:
                    proj_dict['Mean Cp'].append(0)
                else:
                    proj_dict['Mean Cp'].append(df_csurf['Mean Cp'][row])
        else:
            print('gable and hip roofs not yet supported')
    # Convert the dictionary into a DataFrame:
    df_tpu_pressures = pd.DataFrame(proj_dict).set_index('Index')
    # Calculate the pressure at each location:
    pressure_calc = PressureCalc()
    pressures = []
    for k in df_tpu_pressures.index.to_list():
        pressures.append(pressure_calc.get_tpu_pressure(wind_speed, df_tpu_pressures['Mean Cp'][k], 'B', df_tpu_pressures['Real Life Location'][k].z, 'mph'))
    # Add a new column with the calculated pressures to the DataFrame:
    df_tpu_pressures['Pressure'] = pressures
    # Plot the real-life pressure tap locations:
    # fig2 = plt.figure()
    # ax2 = plt.axes(projection='3d')
    # for i in df_tpu_pressures['Real Life Location']:
    # ax2.scatter(np.array([i.x])/3.281, np.array([i.y])/3.281, np.array([i.z])/3.281, 'o')
    # plt.show()
    # Plot the full-scale pressures:
    fig3 = plt.figure()
    ax3 = plt.axes(projection='3d')
    rl_xs = []
    rl_ys = []
    rl_zs = []
    for k in df_tpu_pressures.index.to_list():
        rl_xs.append(df_tpu_pressures['Real Life Location'][k].x)
        rl_ys.append(df_tpu_pressures['Real Life Location'][k].y)
        rl_zs.append(df_tpu_pressures['Real Life Location'][k].z)
    img = ax3.scatter3D(np.array([rl_xs]) / 3.281, np.array([rl_ys]) / 3.281, np.array([rl_zs]) / 3.281,
                        c=df_tpu_pressures['Pressure'] / 0.020885, cmap=plt.get_cmap('copper', 6))
    fig3.colorbar(img)
    print('max and min Surface 1')
    print(max(df_tpu_pressures.loc[df_tpu_pressures['Surface Number'] == 1, 'Pressure'])/0.020885)
    print(min(df_tpu_pressures.loc[df_tpu_pressures['Surface Number'] == 1, 'Pressure'])/0.020885)
    print('max and min Surface 2')
    print(max(df_tpu_pressures.loc[df_tpu_pressures['Surface Number'] == 2, 'Pressure']) / 0.020885)
    print(min(df_tpu_pressures.loc[df_tpu_pressures['Surface Number'] == 2, 'Pressure']) / 0.020885)
    print('max and min Surface 3')
    print(max(df_tpu_pressures.loc[df_tpu_pressures['Surface Number'] == 3, 'Pressure']) / 0.020885)
    print(min(df_tpu_pressures.loc[df_tpu_pressures['Surface Number'] == 3, 'Pressure']) / 0.020885)
    print('max and min Surface 4')
    print(max(df_tpu_pressures.loc[df_tpu_pressures['Surface Number'] == 4, 'Pressure']) / 0.020885)
    print(min(df_tpu_pressures.loc[df_tpu_pressures['Surface Number'] == 4, 'Pressure']) / 0.020885)
    print('max and min Surface 5')
    print(max(df_tpu_pressures.loc[df_tpu_pressures['Surface Number'] == 5, 'Pressure']) / 0.020885)
    print(min(df_tpu_pressures.loc[df_tpu_pressures['Surface Number'] == 5, 'Pressure']) / 0.020885)
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
        # First check if there is a difference between the actual vs. model building height:
        if hfull == h_bldg:
            pass
        else:
            # Quantify the difference between the model bldg height and actual height:
            hscale = h_bldg/hfull
            # Add or subtract the height difference to each coordinate:
            for pt in range(0, len(df_tpu_pressures['Real Life Location'])):
                tap_loc = df_tpu_pressures['Real Life Location'][pt]
                df_tpu_pressures['Real Life Location'][pt] = Point(tap_loc.x, tap_loc.y, tap_loc.z*hscale)
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
                surf_pts = df_tpu_pressures.loc[df_tpu_pressures['Surface Number'] == snum, 'Real Life Location']
                if snum == 1 or snum == 3:
                    # Translate all points for this surface:
                    for pt in surf_pts.index.to_list():
                        current_pt = df_tpu_pressures['Real Life Location'][pt]
                        df_tpu_pressures['Real Life Location'][pt] = Point(current_pt.x + xdiff, current_pt.y + ydiff, current_pt.z)
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
                        current_pt = df_tpu_pressures['Real Life Location'][pt]
                        # Find the index of the current x or y value - used for spacing multipliers:
                        if xflag:
                            idx = np.where(x_unique == current_pt.x)[0] - 1
                        else:
                            idx = np.where(y_unique == current_pt.y)[0] - 1  # Exception: Surf 2 and 4 || to N-S direction
                        # Shift all points to the corner of the surface:
                        df_tpu_pressures['Real Life Location'][pt] = Point(current_pt.x + dist * cos(theta), current_pt.y + dist * sin(theta), current_pt.z)
                        if snum != 5:
                            if current_pt.x == xmodel[min_idx] and current_pt.y == ymodel[min_idx]:
                                pass
                            else:
                                # Shift the point again to create the new spacing:
                                df_tpu_pressures['Real Life Location'][pt] = Point(xrect[min_rect_idx] - new_space * idx * cos(theta), yrect[min_rect_idx] - new_space * idx * sin(theta), current_pt.z)
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
                            origin_pt = df_tpu_pressures['Real Life Location'][idx]
                            for multiplier in range(1, len(xvals)):  # Note: origin_idx already where they need to be
                                pt_idx = idx + len(xvals)*multiplier
                                # Note: Point lines are parallel to surface 2 and 4
                                # Use origin pts and multiplier to define new coordinate pairs:
                                df_tpu_pressures['Real Life Location'][pt_idx] = Point(origin_pt.x - (new_space * multiplier * cos(theta)), origin_pt.y - (new_space * multiplier * sin(theta)), origin_pt.z)
        # Plot the new pressure tap locations and their pressures:
        # Plot the full-scale pressures:
        fig4 = plt.figure()
        ax4 = plt.axes(projection='3d')
        rl_xs, rl_ys, rl_zs = [], [], []
        for k in df_tpu_pressures.index.to_list():
            rl_xs.append(df_tpu_pressures['Real Life Location'][k].x)
            rl_ys.append(df_tpu_pressures['Real Life Location'][k].y)
            rl_zs.append(df_tpu_pressures['Real Life Location'][k].z)
        img = ax4.scatter3D(np.array([rl_xs]) / 3.281, np.array([rl_ys]) / 3.281, np.array([rl_zs]) / 3.281, c=df_tpu_pressures['Pressure'] / 0.020885, cmap=plt.get_cmap('copper', 6))
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
        ax4.set_xlabel('x [m]')
        ax4.set_ylabel('y [m]')
        ax4.set_zlabel('z [m]')
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
        df_tpu_pressures['Surface Match'] = False  # Start by assuming there is not a perfect match with actual geometry
        df_bldg_pressures = pd.DataFrame(columns=df_tpu_pressures.columns)  # Create master DataFrame for entire building
        df_roof_pressures = pd.DataFrame(columns = df_tpu_pressures.columns)
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
                df_surf_pressures = pd.DataFrame(columns=df_tpu_pressures.columns)
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
                    # Pull the corresponding pressure taps:
                    tap_indices = df_tpu_pressures[df_tpu_pressures['Surface Number'] == key].index.to_list()
                    for tap_idx in tap_indices:
                        ref_pt = Point(df_tpu_pressures['Real Life Location'][tap_idx].x, df_tpu_pressures['Real Life Location'][tap_idx].y)
                        if ref_pt.within(surf_range_poly):
                            df_tpu_pressures['Surface Match'][tap_idx] = True
                            tap_info = df_tpu_pressures.iloc[tap_idx]
                            if key != 5:
                                df_surf_pressures = df_surf_pressures.append(tap_info, ignore_index=True)
                            else:
                                df_roof_pressures = df_roof_pressures.append(tap_info, ignore_index=True)
                        else:
                            pass
                elif b1.within(range_poly) or b2.within(range_poly):
                    rsurf_list.append(key)
                else:
                    pass
            if not roof_flag:
                if len(rsurf_list) > 1:
                    print(rsurf_list)
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
                    surf_pts = df_tpu_pressures[(df_tpu_pressures['Surface Number'] == rsurf_list[0]) | (df_tpu_pressures['Surface Number'] == rsurf_list[1])]
                    # Use a dictionary to keep track of data for this surface:
                    new_dict = {}
                    for col in df_tpu_pressures.columns:
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
                    df_surf_pressures = df_surf_pressures.append(df_tap_info, ignore_index=True)
                else:
                    # Grab any edge roof points:
                    for tap in df_surf_pressures.index.to_list():
                        tap_pt = df_surf_pressures['Real Life Location'][tap]
                        if round(tap_pt.z, 4) == round(bldg.hasGeometry['Height'], 4):
                            roof_taps = df_tpu_pressures.loc[df_tpu_pressures['Surface Number'] == 5]
                            for rtap in roof_taps.index.to_list():
                                if round(roof_taps['Real Life Location'][rtap].x, 4) == round(tap_pt.x,4) and round(roof_taps['Real Life Location'][rtap].y,4) == round(tap_pt.y,4):
                                    rtap_info = df_tpu_pressures.iloc[rtap]
                                    df_roof_pressures = df_roof_pressures.append(rtap_info, ignore_index=True)
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
                bldg.hasDemand['wind pressure']['external']['surfaces'].append(bsurf)
                bldg.hasDemand['wind pressure']['external']['values'].append(df_surf_pressures)
                # Add the surface pressure tap data to the master DataFrame:
                df_bldg_pressures = df_bldg_pressures.append(df_surf_pressures, ignore_index=True)
        # Save the roof surface and data:
        bldg.hasDemand['wind pressure']['external']['surfaces'].append(roof_poly)
        bldg.hasDemand['wind pressure']['external']['values'].append(df_roof_pressures)
        df_bldg_pressures = df_bldg_pressures.append(df_roof_pressures, ignore_index=True)
        # Plot the projected pressure taps:
        xf, yf, zf = [], [], []
        for k in df_bldg_pressures.index.to_list():
            xf.append(df_bldg_pressures['Real Life Location'][k].x)
            yf.append(df_bldg_pressures['Real Life Location'][k].y)
            zf.append(df_bldg_pressures['Real Life Location'][k].z)
        img = ax5.scatter3D(np.array([xf]) / 3.281, np.array([yf]) / 3.281, np.array([zf]) / 3.281,
                            c=df_bldg_pressures['Pressure'] / 0.020885, cmap=plt.get_cmap('copper', 6))
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
        ax5.set_xlabel('x [m]')
        ax5.set_ylabel('y [m]')
        ax5.set_zlabel('z [m]')
        plt.show()
        print('a')
    return df_tpu_pressures


def create_zcoords(footprint, zcoord):
    # Input footprint polygon (either local or geodesic) and elevation:
    zs = []
    # Create z coordinates for the given building footprint and elevation:
    xs, ys = footprint.exterior.xy
    for pt in range(0, len(xs)):
        # Define z-coordinates for bottom floor of each story:
        zs.append(Point(xs[pt], ys[pt], zcoord))
    return zs
