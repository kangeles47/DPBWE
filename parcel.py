import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import numpy as np
import geopandas as gpd
from geopy import distance
from math import sqrt, pi, sin, atan2, degrees
from scipy import spatial
from shapely.geometry import LineString, Point, Polygon
from shapely import affinity
import bldg_code
from OBDM.zone import Building
from OBDM.element import Roof, Wall, Floor, Ceiling
from OBDM.interface import Interface
from survey_data import SurveyData


class Parcel(Building):  # Note here: Consider how story/floor assignments may need to change for elevated structures

    def __init__(self, pid, num_stories, occupancy, yr_built, address, area, lon, lat, length_unit, plot_flag):
        Building.__init__(self)  # Bring in all of the attributes that are defined in the BIM class for the parcel model
        # Add parcel data:
        self.add_parcel_data(pid, num_stories, occupancy, yr_built, address, area, lon, lat, length_unit, loc_flag=True)
        # Define building-level attributes that are specific to parcel models
        # Building footprint:
        self.assign_footprint(self, num_stories)
        plt.rcParams["font.family"] = "Times New Roman"
        # Clean up building footprint for illustrative example:
        for key in self.hasGeometry['Footprint']:
            if key == 'type':
                pass
            else:
                xcoord, ycoord = self.hasGeometry['Footprint'][key].exterior.xy
                new_point_list = []
                if address == '1002 23RD ST W PANAMA CITY 32405':
                    for idx in range(2, len(xcoord) - 2):
                        new_point_list.append(Point(xcoord[idx], ycoord[idx]))
                    self.hasGeometry['Footprint'][key] = Polygon(new_point_list)
                else:
                    pass
                xfpt, yfpt = self.hasGeometry['Footprint'][key].exterior.xy
                if plot_flag:
                    plt.plot(np.array(xfpt) / 3.281, np.array(yfpt) / 3.281, 'k')
                if key == 'local':
                    # Rotate the footprint to create a "rotated cartesian" axis:
                    rect = self.hasGeometry['Footprint'][key].minimum_rotated_rectangle
                    spts = list(rect.exterior.coords)
                    theta = degrees(atan2((spts[1][0] - spts[2][0]), (spts[1][1] - spts[2][1])))
                    # Rotate the the building footprint to create the TPU axis:
                    rotated_b = affinity.rotate(Polygon(new_point_list), theta, origin='centroid')
                    rflag = True
                    rx, ry = rotated_b.exterior.xy
                    if plot_flag:
                        plt.plot(np.array(rx) / 3.281, np.array(ry) / 3.281, color='gray', linestyle='dashed')
                        plt.legend(['local Cartesian', 'rotated Cartesian'], prop={"size":22}, loc='upper right')
                else:
                    rflag= False
                    # Uncomment to plot the footprint:
                if plot_flag:
                    plt.xlabel('x [m]', fontsize=22)
                    plt.ylabel('y [m]', fontsize=22)
                    plt.xticks(fontsize=22)
                    plt.yticks(fontsize=22)
                    plt.show()
        #if rflag:
            #self.hasGeometry['Footprint']['rotated'] = rotated_b
        # Pull building/story height information from DOE reference buildings:
        survey_data = SurveyData()  # create an instance of the survey data class
        survey_data.run(self, ref_bldg_flag=True, parcel_flag=False)
        # Create an instance of the BldgCode class and populate building-level code-informed attributes for the parcel:
        #if self.hasLocation['State'] == 'FL':
            #code_informed = bldg_code.FBC(self, loading_flag=False)  # Need building code for code-based descriptions
        #else:
            #pass
        # Now that we have the building and story heights, render the 3D geometries:
        # Extract points for the building footprint and add the base z coordinate:
        geo_keys = self.hasGeometry['Footprint'].keys()
        for key in geo_keys:
            if key == 'type':
                pass
            else:
                new_zpts = []
                roof_zs = []
                # Create z coordinates for each story:
                for story_num in range(0, len(self.hasStory)):
                    zcoord = self.hasStory[story_num].hasElevation[0]
                    zs = self.create_zcoords(self.hasGeometry['Footprint'][key], zcoord)
                    if story_num == len(self.hasStory) - 1:
                        zcoord_roof = self.hasStory[story_num].hasElevation[-1]
                        roof_zs = self.create_zcoords(self.hasGeometry['Footprint'][key], zcoord_roof)
                    else:
                        pass
                    # Save 3D coordinates:
                    new_zpts.append(zs)
                new_zpts.append(roof_zs)
                # With new 3D coordinates for each horizontal plane, create surface geometry:
                # Set up plotting:
                if plot_flag:
                    fig = plt.figure()
                    ax = plt.axes(projection='3d')
                for plane in range(0, len(new_zpts) - 1):
                    # Add the bottom and top planes for the Story:
                    plane_poly1 = Polygon(new_zpts[plane])
                    plane_poly2 = Polygon(new_zpts[plane + 1])
                    self.hasStory[plane].hasGeometry['3D Geometry'][key].append(plane_poly1)
                    self.hasStory[plane].hasGeometry['3D Geometry'][key].append(plane_poly2)
                    for zpt in range(0, len(new_zpts[plane]) - 1):
                        # Create the surface polygon:
                        surf_poly = Polygon([new_zpts[plane][zpt], new_zpts[plane + 1][zpt], new_zpts[plane + 1][zpt + 1], new_zpts[plane][zpt + 1]])
                        # Save the polygon to the story's geometry:
                        self.hasStory[plane].hasGeometry['3D Geometry'][key].append(surf_poly)
                        self.hasStory[plane].hasGeometry['Facade'][key].append(surf_poly)
                        # Extract xs, ys, and zs and plot
                        surf_xs = []
                        surf_ys = []
                        surf_zs = []
                        for surf_points in list(surf_poly.exterior.coords):
                            surf_xs.append(surf_points[0])
                            surf_ys.append(surf_points[1])
                            surf_zs.append(surf_points[2])
                        if plot_flag:
                            # Plot the surfaces for the entire building to verify:
                            ax.plot(np.array(surf_xs)/3.281, np.array(surf_ys)/3.281, np.array(surf_zs)/3.281, 'k')
                            # Make the panes transparent:
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
                            #ax.set_zlim(0, 16)
                            ax.set_zlim3d(0, 16)
                # Show the surfaces for each story:
                #ax.set_xticks(np.arange(-20,20,5))
                #ax.set_yticks(np.arange(-20, 20, 5))
                if plot_flag:
                    ax.set_zticks(np.arange(0, 20, 4))
                    ax.xaxis.set_tick_params(labelsize=16)
                    ax.yaxis.set_tick_params(labelsize=16)
                    ax.zaxis.set_tick_params(labelsize=16)
                    plt.show()
                # Define full 3D surface renderings for the building using base plane and top plane:
                base_poly = Polygon(new_zpts[0])
                top_poly = Polygon(new_zpts[-1])
                self.hasGeometry['3D Geometry'][key].append(base_poly)
                self.hasGeometry['3D Geometry'][key].append(top_poly)
                for pt in range(0, len(new_zpts[0]) - 1):
                    # Create the surface polygon:
                    bsurf_poly = Polygon([new_zpts[0][pt], new_zpts[-1][pt], new_zpts[-1][pt + 1], new_zpts[0][pt + 1]])
                    # Save the polygon to the building geometry:
                    self.hasGeometry['3D Geometry'][key].append(bsurf_poly)
                    self.hasGeometry['Facade'][key].append(bsurf_poly)
        # Generate a set of building elements (with default attributes) for the parcel:
        self.parcel_elements(self, zone_flag=True)
        # Update the Building's Elements:
        self.update_elements()
        # Populate instance attributes informed by national survey data:
        survey_data.run(self, ref_bldg_flag=False, parcel_flag=True)  # populate the component-level attributes using survey data
        if survey_data.isSurvey == 'CBECS':
            # Populate code-informed component-level information
            code_informed = bldg_code.FBC(self, loading_flag=False)
            code_informed.bldg_attributes(self)
            code_informed.roof_attributes(code_informed.hasEdition, self)
        else:
            pass
        # Update roof cover sub-elements (if-applicable):
        if len(self.adjacentElement['Roof'][0].hasSubElement['cover']) > 0:
            for elem in self.adjacentElement['Roof'][0].hasSubElement['cover']:
                elem.hasCover = self.adjacentElement['Roof'][0].hasCover
                elem.hasPitch = self.adjacentElement['Roof'][0].hasPitch
        else:
            pass

    def assign_footprint(self, parcel, num_stories):
        # Access file with region's building footprint information:
        if parcel.hasLocation['State'] == 'FL' and parcel.hasLocation['County'] == 'Bay':
            jFile = 'D:/Users/Karen/Documents/Github/DPBWE/Datasets/Geojson/BayCounty.geojson'
        else:
            print('Footprints for this region currently not supported')

        data = gpd.read_file(jFile)
        # data is a DataFrame object with column label = ['geometry'] and indexes = [0: end]
        # Accessing a specific Polygon object then requires: data['geometry'][index]

        # Need to access Polygon geometry in order to determine if the parcel's location is within that polygon:
        # Create a Point object with the parcel's lon, lat coordinates:
        ref_pt = parcel.hasLocation['Geodesic']

        # Loop through dataset to find the parcel's corresponding footprint:
        for row in range(0, len(data['geometry'])):
            # Check if point is within the polygon in this row:
            poly = data['geometry'][row]
            if ref_pt.within(poly):
                parcel.hasGeometry['Footprint']['geodesic'] = poly
                parcel.hasGeometry['Footprint']['type'] = 'open data'
            else:
                pass
        # If the lon, lat of the parcel does not fall within bounds of any of the footprints, assign nearest neighbor:
        if parcel.hasGeometry['Footprint']['type'] is None:
            # Populate the KD tree using the centroids of the building footprints:
            centroids = data['geometry'].apply(lambda ind: [ind.centroid.x, ind.centroid.y]).tolist()
            kdtree = spatial.KDTree(centroids)
            # Set up an array of (small) longitude, latitude radii:
            radii = np.arange(0.0001, 0.01, 0.0001)
            # Find the nearest neighbors within the radius (increase until neighbors are present):
            neigh_list = []
            for rad in radii:
                neigh_list.append(kdtree.query_ball_point([ref_pt.x, ref_pt.y], r=rad))
                if len(neigh_list) > 1:
                    break
                else:
                    pass
            # Find the identified building footprints:
            if len(neigh_list[1]) == 1:
                parcel.hasGeometry['Footprint']['geodesic'] = data['geometry'][neigh_list[1][0]]
                parcel.hasGeometry['Footprint']['type'] = 'open data'
            else:
                print('More than 1 building footprint identified', parcel.hasID, parcel.hasLocation['Address'])
                # In the future, might be able to do a match by considering the height of the parcel and it's area

        # Assign a regular footprint to any buildings without an open data footprint:
        if parcel.hasGeometry['Footprint']['type'] == 'open data':
            pass
        else:
            parcel.hasGeometry['Footprint']['type'] = 'default'
            length = (sqrt(self.hasGeometry['Total Floor Area'] / num_stories)) * (1 / (2 * sin(
                pi / 4)))  # Divide total building area by number of stories and take square root, divide by 2
            p1 = distance.distance(miles=length / 5280).destination((ref_pt.y, ref_pt.x), 45)
            p2 = distance.distance(miles=length / 5280).destination((ref_pt.y, ref_pt.x), 135)
            p3 = distance.distance(miles=length / 5280).destination((ref_pt.y, ref_pt.x), 225)
            p4 = distance.distance(miles=length / 5280).destination((ref_pt.y, ref_pt.x), 315)
            parcel.hasGeometry['Footprint']['geodesic'] = Polygon(
                [(p1.longitude, p1.latitude), (p2.longitude, p2.latitude), (p3.longitude, p3.latitude),
                 (p4.longitude, p4.latitude)])
            print('default building footprint:' + parcel.hasLocation['Address'])
        # Given the geodesic footprint, calculate the local (x,y) coordinates for the building footprint:
        # Find the distance between exterior points and the building centroid (origin) to define a new coordinate system:
        xs, ys = parcel.hasGeometry['Footprint']['geodesic'].exterior.xy
        origin = parcel.hasGeometry['Footprint']['geodesic'].centroid
        point_list = []
        for ind in range(0, len(xs)):
            # Find the distance between x, y at origin and x, y for each point:
            xdist = distance.distance((origin.y, origin.x), (origin.y, xs[ind])).miles * 5280  # [ft]
            ydist = distance.distance((origin.y, origin.x), (ys[ind], origin.x)).miles * 5280  # [ft]
            if xs[ind] < origin.x:
                xdist = -1 * xdist
            else:
                pass
            if ys[ind] < origin.y:
                ydist = -1 * ydist
            else:
                pass
            point_list.append(Point(xdist, ydist))
        # Create a new polygon object:
        xy_poly = Polygon(point_list)
        # Add to Parcel:
        parcel.hasGeometry['Footprint']['local'] = xy_poly
        # Find the footprint's orientation using a minimum rectangle and its local geometry:
        rect = self.hasGeometry['Footprint']['local'].minimum_rotated_rectangle
        xrect, yrect = rect.exterior.xy
        xdist = xrect[3] - xrect[2]
        ydist = yrect[3] - yrect[2]
        theta = degrees(atan2(ydist, xdist))
        # Orientation is according to normal cartesian coordinates (i.e., cw = (-) angle, ccw = (+) angle)
        # Add the building's orientation
        self.hasOrientation = theta
        #plt.plot(xrect, yrect)
        #plt.show()

    def parcel_elements(self, parcel, zone_flag):
        # Generate parcel elements with (default) attributes:
        # Floor, Ceiling, and Roof Instances - These are conducted by story to facilitate "hasElement" assignment
        # Exterior Walls - Parcel approach: Geometries are derived considering ASCE 7 C&C zone locations:
        # Exterior Walls - Other approach: Geometries are derived using footprint vertices
        if zone_flag:
            asce7 = bldg_code.ASCE7(parcel, loading_flag=False)
            a = asce7.get_cc_zone_width(parcel)  # Determine the zone width
            zone_pts, roof_polys = asce7.find_cc_zone_points(parcel, a, roof_flag=True, edition=None)  # Coordinates for start/end of zone locations
        else:
            pass
        # Assume that walls span one story for now:
        for story in range(0, len(parcel.hasStory)):
            # Create an empty list to hold all elements:
            element_dict = {'Floor': [], 'Walls': [], 'Ceiling': [], 'Roof': []}
            # Generate floor and ceiling instance(s):
            if story == 0:
                new_floor1 = Floor()
                new_floor1.hasElevation = parcel.hasStory[story].hasElevation[0]
                element_dict['Floor'].append(new_floor1)
            else:
                # Reference the prior story's top floor:
                floor1 = parcel.hasStory[story - 1].hasElement['Floor'][1]
                element_dict['Floor'].append(floor1)
            # Top floor:
            if story == len(parcel.hasStory) - 1:
                new_roof = Roof()
                # Add two-dimensional geometry:
                for key in ['local', 'geodesic']:
                    new_roof.hasGeometry['2D Geometry'][key] = self.hasGeometry['Footprint'][key]
                    # Add three-dimensional geometry:
                    xroof, yroof = new_roof.hasGeometry['2D Geometry'][key].exterior.xy
                    rpt_list = []
                    for x in range(0, len(xroof)):
                        new_pt = Point(xroof[x], yroof[x], self.hasGeometry['Height'])
                        rpt_list.append(new_pt)
                    new_roof.hasGeometry['3D Geometry'][key] = Polygon(rpt_list)
                if zone_flag:
                    # Create roof sub_elements for C&C:
                    for key in roof_polys.keys():
                        for poly in roof_polys[key]:
                            new_sub_element = Roof()
                            new_sub_element.hasGeometry['2D Geometry']['local'] = poly
                            # Add 3D geometry:
                            xpoly, ypoly = poly.exterior.xy
                            poly_3d = []
                            for j in range(0, len(xpoly)):
                                poly_3d.append(Point(xpoly[j], ypoly[j], self.hasGeometry['Height']))
                            new_sub_element.hasGeometry['3D Geometry']['local'] = Polygon(poly_3d)
                            # Add subelement to roof:
                            new_roof.hasSubElement['cover'].append(new_sub_element)
                else:
                    pass
                # Add roof to the story:
                parcel.hasStory[story].adjacentElement.update({'Roof': [new_roof]})
                element_dict['Roof'].append(new_roof)
            else:
                new_floor2 = Floor()
                new_floor2.hasElevation = parcel.hasStory[story].hasElevation[1]
                # new_floor_list.append(new_floor2)
                element_dict['Floor'].append(new_floor2)
            # Create a new ceiling for the floor:
            new_ceiling = Ceiling()
            # Add the ceiling to element_dict:
            element_dict['Ceiling'].append(new_ceiling)
            # Parcel models: Use ASCE 7 C&C zones to create a preliminary set of wall elements
            # Loop through zone_pts and assign geometries to wall elements:
            new_wall_list = []
            if zone_flag:
                for ind in zone_pts.index:
                    for col in range(0, len(zone_pts.loc[ind]) - 1):
                        # Create a new Wall Instance:
                        ext_wall = Wall()
                        ext_wall.isExterior = True
                        ext_wall.inLoadPath = True
                        ext_wall.hasGeometry['Height'] = parcel.hasStory[story].hasGeometry['Height']
                        ext_wall.hasGeometry['1D Geometry']['local'] = LineString([zone_pts.iloc[ind, col], zone_pts.iloc[
                            ind, col + 1]])  # Line segment with start/end coordinates of wall (respetive to building origin)
                        ext_wall.hasGeometry['Length'] = ext_wall.hasGeometry['1D Geometry']['local'].length
                        # (x, y, z) coordinates:
                        zbottom = parcel.hasStory[story].hasGeometry['Height']*story
                        ztop = parcel.hasStory[story].hasGeometry['Height']*(story+1)
                        xline, yline = ext_wall.hasGeometry['1D Geometry']['local'].xy
                        wall_xyz_poly = Polygon([Point(xline[0], yline[0], zbottom), Point(xline[1], yline[1], zbottom), Point(xline[1], yline[1], ztop), Point(xline[0], yline[0], ztop), Point(xline[0], yline[0], zbottom)])
                        ext_wall.hasGeometry['3D Geometry']['local'] = wall_xyz_poly
                        new_wall_list.append(ext_wall)
            else:
                xf, yf = parcel.hasGeometry['Footprint']['local'].exterior.xy
                for pt in range(0, len(xf)-1):
                    # Create a new Wall Instance:
                    ext_wall = Wall()
                    ext_wall.isExterior = True
                    ext_wall.inLoadPath = True
                    ext_wall.hasGeometry['Height'] = parcel.hasStory[story].hasGeometry['Height']
                    ext_wall.hasGeometry['1D Geometry']['local'] = LineString([(xf[pt], yf[pt]), (xf[pt+1], yf[pt+1])])  # Line segment with start/end coordinates of wall (respetive to building origin)
                    ext_wall.hasGeometry['Length'] = ext_wall.hasGeometry['1D Geometry']['local'].length
                    new_wall_list.append(ext_wall)
            # Add all walls to element_dict:
            element_dict['Walls'] = new_wall_list
            # Each wall shares interfaces with the walls before and after it:
            for w in range(0, len(new_wall_list) - 1):
                # Create new Interface instance
                new_interface = Interface([new_wall_list[w], new_wall_list[w + 1]])
                parcel.hasStory[story].hasInterface.append(new_interface)
            # Add all elements to the story's "hasElement" attribute:
            parcel.hasStory[story].containsElement.update({'Ceiling': element_dict['Ceiling']})
            parcel.hasStory[story].adjacentElement.update({'Floor': element_dict['Floor']})
            parcel.hasStory[story].adjacentElement.update({'Walls': element_dict['Walls']})
            # Update hasElement attribute for the story:
            parcel.hasStory[story].hasElement.update(element_dict)