import numpy as np
from math import atan2, degrees
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
    match_flag, num_surf, side_lines, model_file, hb_ratio, db_ratio, rect, surf_dict = find_tpu_use_case(bldg, key, tpu_wdir, eave_length)
    bfull, hfull, dfull = get_TPU_surfaces(bldg, key, match_flag, num_surf, side_lines, hb_ratio, db_ratio, rect, tpu_wdir, surf_dict)
    df_tpu_pressures = map_tap_data(tpu_wdir, model_file, num_surf, bfull, hfull, dfull, side_lines, surf_dict, wind_speed, exposure, edition, cat, hpr)
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
            if bldg.hasStorey[-1].adjacentElement['Roof'].hasShape == 'flat':
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
    else:
        print('Buildings with eaves are not yet supported')
    return match_flag, num_surf, side_lines, model_file, hb_ratio, db_ratio, rect, surf_dict


def get_TPU_surfaces(bldg, key, match_flag, num_surf, side_lines, hb_ratio, db_ratio, rect, tpu_wdir, surf_dict):
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
            zcoord_base = bldg.hasStorey[0].hasElevation[0]
            zcoord_roof = bldg.hasStorey[-1].hasElevation[-1]
            bldg_zpts.append(create_zcoords(rect, zcoord_base))
            bldg_zpts.append(create_zcoords(rect, zcoord_roof))
        else:
            pass
    # Create general surface geometries:
    xs = [dfull/2, dfull/2, -dfull/2, -dfull/2, dfull/2]
    ys = [-bfull/2, bfull/2, bfull/2, -bfull/2, -bfull/2]
    plt.plot(np.array(xs)/3.281, np.array(ys)/3.281, linestyle = 'dashed', color='gray')
    xbldg, ybldg = bldg.hasGeometry['Footprint']['local'].exterior.xy
    plt.plot(np.array(xbldg)/3.281, np.array(ybldg)/3.281, 'k')
    plt.xlabel('x [m]')
    plt.ylabel('y [m]')
    plt.show()
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
    fig2 = plt.figure(dpi=200)
    ax2 = plt.axes(projection='3d')
    for i in idx:
        surf_dict[i] = tpu_polys[poly_order[i - 1]]
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
    return bfull, hfull, dfull


def map_tap_data(tpu_wdir, model_file, num_surf, bfull, hfull, dfull, side_lines, surf_dict, wind_speed, exposure, edition, cat, hpr):
    # Read in pressure data file:
    tpu_file = 'D:/Users/Karen/Documents/GitHub/DPBWE/Datasets/TPU/' + model_file
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
                        surf_2D = LineString([spts[1], spts[2]])
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
                    proj_dict['Mean Cp'].append(df_csurf['Mean Cp'][row])
            else:
                pass
        else:
            print('gable and hip roofs not yet supported')
    # Convert the dictionary into a DataFrame:
    df_tpu_pressures = pd.DataFrame(proj_dict).set_index('Index')
    # Calculate the pressure at each location:
    pressure_calc = PressureCalc()
    pressures = []
    for k in df_tpu_pressures.index.to_list():
        pressures.append(
            pressure_calc.tpu_pressure(wind_speed, exposure, edition, df_tpu_pressures['Real Life Location'][k].z,
                                       df_tpu_pressures['Mean Cp'][k], cat, hpr))
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
                        c=df_tpu_pressures['Pressure'] / 0.020885, cmap=plt.get_cmap('hot'))
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
        for p in list(surf_dict[key].exterior.coords):
            xsurf.append(p[0])
            ysurf.append(p[1])
            zsurf.append(p[2])
        ax3.plot(np.array(xsurf)/3.281, np.array(ysurf)/3.281, np.array(zsurf)/3.281, 'k')
    plt.show()
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




# Let's play with rotations for a little bit:
                #theta = radians(self.hasOrientation)
                #zrot_mat = np.array([[cos(theta), -sin(theta), 0], [sin(theta), cos(theta), 0], [0, 0, 1]])
                #roof_pts = new_zpts[-1]
                #roof_pts = [Point(0,0,0), Point()]
                #rotate_x = []
                #rotate_y = []
                #rotate_z = []
                #for pt in roof_pts:
                    # Create an array with the points x, y, z:
                    #vec = np.array([[pt.x], [pt.y], [pt.z]])
                    # Rotate x, y about z plane:
                    #rpts = zrot_mat.dot(vec)
                    # Save these as a new point:
                    #rotate_x.append(rpts[0][0])
                    #rotate_y.append(rpts[1][0])
                    #rotate_z.append(rpts[2][0])
                # Plot the rotated x, y pairs:
                #plt.plot(rotate_x, rotate_y)
                #plt.show()