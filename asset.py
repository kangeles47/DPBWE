import numpy as np
from math import sqrt, pi, sin, atan2, degrees, cos
import geopandas as gpd
from shapely.geometry import Point, Polygon, LineString
from scipy import spatial
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from element import Roof, Wall, Floor, Ceiling
import bldg_code
from survey_data import SurveyData
from geopy import distance


# The Building Topology Ontology (BOT) is a minimal ontology for describing the core topological concepts of a building.
# BOT representation (logic) is used to organize asset(s) description(s)
# BOT Documentation: https://w3c-lbd-cg.github.io/bot/#


class Zone:
    # Zones represent any 3D geometry
    # Sub-classes include Site, Building, Storey, Space
    def __init__(self, new_zone):
        # Zones can be adjacent to other zones:
        self.adjacentZone = []
        # Zones can intersect:
        self.intersectsZone = []
        # Zones contain themselves and can contain other zones
        # hasBuilding, hasStorey, and hasSpace are sub-properties of containsZone
        if isinstance(new_zone, Site):
            self.hasBuilding = []
        else:
            pass
        if isinstance(new_zone, Building):
            self.hasStorey = []
            self.hasSpace = []
        else:
            pass
        if isinstance(new_zone, Storey):
            self.hasSpace = []
        else:
            pass
        self.containsZone = []
        # Zones have elements (hasElement). The following are subproperties of hasElement:
        self.containsElement = {}
        self.adjacentElement = {}  # Adjacent building elements contribute to bounding the zone
        self.intersectingElement = {}  # Building elements that intersect the zone
        self.hasElement = {}
        self.has3DModel = None
        # Adding in a hasInterface element to keep track of interface objects:
        self.hasInterface = []

    def update_zones(self):
        # Simple function to easily update containsZone assignment
        try:
            for bldg in self.hasBuilding:
                self.containsZone.append(bldg)
        except AttributeError:
            pass
        try:
            for storey in self.hasStorey:
                self.containsZone.append(storey)
        except AttributeError:
            pass
        try:
            for space in self.hasSpace:
                self.containsZone.append(space)
        except AttributeError:
            pass

    def update_elements(self):
        # Simple function to easily update hasElement assignment
        inst_types = ['Site', 'Building', 'Parcel', 'Storey', 'Space']
        a = str(type(self))
        for itype in inst_types:
            if a in itype:
                print(type)
            else:
                pass
        if isinstance(self, Site):
            for bldg in self.hasBuilding:
                for k, v in bldg.hasElement:
                    self.hasElement.append(v)
        elif isinstance(self, Building):
            print(self.__class__.__name__)
            for storey in self.hasStorey:
                for k in storey.hasElement:
                    # Update the hasElement attribute:
                    if k in self.hasElement:
                        if storey.hasElement[k] == self.hasElement[k]:
                            print('Building story-wise elements have already been updated')
                        else:
                            # Create a list with existing and new story's elements and choose only unique values:
                            elem_list = self.hasElement[k] + storey.hasElement[k]
                            unique_elem = set(elem_list)
                            self.hasElement.update({k: list(unique_elem)})
                    else:
                        self.hasElement.update({k: storey.hasElement[k]})
                    # Update the containsElement attribute:
                    if k in self.containsElement:
                        if storey.containsElement[k] == self.containsElement[k]:
                            print('Building story-wise (contains) elements have already been updated')
                        else:
                            # Create a list with existing and new story's elements and choose only unique values:
                            elem_list = self.containsElement[k] + storey.containsElement[k]
                            unique_elem = set(elem_list)
                            self.containsElement.update({k: list(unique_elem)})
                    else:
                        if k in storey.containsElement:
                            self.containsElement.update({k: storey.containsElement[k]})
                        else:
                            pass
                # Update adjacentElement attribute (exterior walls):
                if 'Walls' in self.adjacentElement:
                    # Create a list with existing and new story's elements and choose only unique values:
                    wall_list = self.adjacentElement['Walls'] + storey.adjacentElement['Walls']
                    unique_walls = set(wall_list)
                    self.adjacentElement.update({'Walls': list(unique_walls)})
                else:
                    self.adjacentElement.update({'Walls': storey.adjacentElement['Walls']})
            # Add the roof as an adjacentElement for the building:
            if 'Roof' in self.adjacentElement:
                print('Roof already defined as an adjacent element for this building')
            else:
                self.adjacentElement.update({'Roof': self.hasStorey[-1].adjacentElement['Roof']})
        elif isinstance(self, Storey):
            for space in self.hasSpace:
                # Update the hasElement attribute:
                for k in space.hasElement:
                    if k in self.hasElement:
                        if space.hasElement[k] == self.hasElement[k]:
                            print('Story space-wise elements have already been updated')
                        else:
                            # Create a list with existing and new story's elements and choose only unique values:
                            elem_list = self.hasElement[k] + space.hasElement[k]
                            unique_elem = set(elem_list)
                            self.hasElement.update({k: list(unique_elem)})
                    else:
                        self.hasElement.update({k: space.hasElement[k]})

    def update_interfaces(self):
        # Simple function to easily update hasElement assignment
        if isinstance(self, Site):
            for bldg in self.hasBuilding:
                for interface in bldg.hasInterface:
                    if interface not in self.hasInterface:
                        self.hasInterface.append(interface)
                    else:
                        pass
        elif isinstance(self, Building):
            for storey in self.hasStorey:
                for interface in storey.hasInterface:
                    if interface not in self.hasInterface:
                        self.hasInterface.append(interface)
                    else:
                        pass
        elif isinstance(self, Storey):
            for space in self.hasSpace:
                for interface in space.hasInterface:
                    if interface not in self.hasInterface:
                        self.hasInterface.append(interface)
                    else:
                        pass


class Site(Zone):
    # Sub-class of Zone
    def __init__(self, bldg_list, site_num, num_sites):
        # Populate Zone attributes:
        new_zone = self
        Zone.__init__(self, new_zone)
        # Sites contain one or more buildings
        # Sites contain all of the zones, spaces, elements, etc. within each building model:
        # Given the number of buildings, create instances of Building and pull attributes
        for i in range(0, len(bldg_list)):
            # Sites contain one or more buildings
            new_bldg = Building(pid, num_stories, occupancy, yr_built, address, area, lon,
                                lat)  # These attributes come from building list
            self.hasBuilding.append(new_bldg)
            # Sites contain all of the zones, spaces, elements, etc. within each building model:
            self.update_zones()
            self.update_elements()
        # Sites can be adjacent to/intersect with other sites (which are also zones)
        if num_sites > 0:
            self.adjacentZone = None  # Update these for future regional analysis
            self.intersectsZone = None
        else:
            pass
        # Add the site as a Zone:
        self.hasName = 'Site' + str(site_num)
        self.containsZone.append(self)


class Building(Zone):
    # Sub-class of Zone
    def __init__(self, pid, num_stories, occupancy, yr_built, address, area, lon, lat):
        new_zone = self
        Zone.__init__(self, new_zone)
        # Add the Building as a Zone:
        self.containsZone.append(self)
        # Given the number of stories, create instances of Storey and pull attributes:
        # Exception for single family homes:
        if num_stories == 0:
            num_stories = int(num_stories) + 1
        else:
            num_stories = int(num_stories)
        # Create Storey instances:
        for i in range(0, num_stories):
            # Buildings have Storeys:
            new_storey = Storey()
            new_storey.hasName = 'Storey' + str(i)
            self.hasStorey.append(new_storey)
        # Create Interface instances to relate stories:
        for stry in range(0, len(self.hasStorey) - 1):
            self.hasInterface.append(Interface(self.hasStorey[stry], self.hasStorey[stry + 1]))
        # Buildings contain all of the zones, spaces, elements, etc. within each storey:
        self.update_zones()
        # Attributes outside of BOT:
        self.hasName = pid
        self.hasOccupancy = occupancy
        self.hasYearBuilt = int(yr_built)
        self.hasLocation = {'Address': address, 'State': None, 'County': None, 'Geodesic': Point(lon, lat)}
        self.hasZeroPoint = Point(lon, lat)
        self.hasGeometry = {'Total Floor Area': float(area), 'Footprint': {'type': None, 'geodesic': None, 'local': None},
                            'Height': None, '3D Geometry': {'geodesic': [], 'local': []},
                            'Surfaces': {'geodesic': [], 'local': []}, 'TPU_surfaces': {'geodesic': [], 'local': []}}
        self.hasOrientation = None
        self.hasFundamentalPeriod = {'x': None, 'y': None}
        self.hasStructuralSystem = {'type': None, 'elements': []}
        self.hasImportanceFactor = None
        self.hasRiskCategory = None
        self.hasEffectiveSeismicWeight = None
        self.hasDampingValue = None
        self.hasServiceLife = None
        # Tag the building as "commercial" or "not commercial"
        if self.hasOccupancy == "Profession" or self.hasOccupancy == "Hotel" or self.hasOccupancy == "Motel" or self.hasOccupancy == "Financial":
            self.isComm = True
        else:
            self.isComm = False
        # Define additional attributes regarding the building location:
        self.location_data(self)

    def location_data(self, Building):
        # Here is where we are going to populate any characteristics relevant to the parcel's location:
        # What we get back from the parcel data is the address and zip code:
        zipcode = int(Building.hasLocation['Address'].split()[-1])
        BayCountyZipCodes = np.arange(32401, 32418)
        BayCountyZipCodes = np.append(BayCountyZipCodes, [32438, 32444, 32466])

        if zipcode in BayCountyZipCodes:
            Building.hasLocation['State'] = 'FL'
            Building.hasLocation['County'] = 'Bay'
        else:
            print('County and State Information not currently supported')

    def create_TPU_surfaces(self, key, tpu_wdir):
        # Create an equivalent minimum rectangle for the building footprint::
        rect = self.hasGeometry['Footprint'][key].minimum_rotated_rectangle  # user can specify between geodesic or local coords
        xrect, yrect = rect.exterior.xy
        # Step 1: Create lines for each side on the rectangle and find their lengths and relative orientations
        side_lines = {'lines': [], 'length': [], 'TPU direction': []}
        max_length = 0
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
        # Find the TPU direction of each line:
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
        # Step 2: Determine how many surfaces will be needed using the roof assembly description:
        # Assign the corresponding sides:
        self.hasStorey[-1].adjacentElement['Roof'].hasShape = 'flat'
        if self.hasStorey[-1].adjacentElement['Roof'].hasShape == 'flat':
            num_surf = 5
            surf_dict = {1: None, 2: None, 3: None, 4: None, 5: None}
        elif self.hasStorey[-1].adjacentElement['Roof'].hasShape == 'hip':  # Note: most common hip roof pitches 4:12-6:12
            num_surf = 8
            surf_dict = {1: None, 2: None, 3: None, 4: None, 5: None, 6: None, 7: None, 8: None}
        elif self.hasStorey[-1].adjacentElement['Roof'].hasShape == 'gable':
            num_surf = 6
            surf_dict = {1: None, 2: None, 3: None, 4: None, 5: None, 6: None}
        else:
            print('Roof shape not supported. Please provide a valid roof shape.')
        # Step 3: Convert footprint 2D into 3D points for base and roof:
        new_zpts = []
        if num_surf == 5:
            zcoord_base = self.hasStorey[0].hasElevation[0]
            zcoord_roof = self.hasStorey[-1].hasElevation[-1]
            new_zpts.append(self.create_zcoords(rect, zcoord_base))
            new_zpts.append(self.create_zcoords(rect, zcoord_roof))
        else:
            pass
        # Step 3: find the orientation of the TPU axes:
        # Find how many degrees ccw the building is oriented by using the angle on the bottom LHS of minimum rectangle:
        #if self.hasOrientation == None:
            #if key == 'geodesic':
                #pass
            #else:
                #xdist = xrect[0] - xrect[3]
                #ydist = yrect[0] - yrect[3]
                #theta = degrees(atan2(ydist, xdist))
                #if theta < 0:
                    # Find the equivalent positive angle:
                    #theta = 360 + theta
                #else:
                    #pass
                #self.hasOrientation = theta
        #else:
            #pass
        # Step 4: Create surface geometries using 3D coordinates:
        # Set up plotting:
        fig = plt.figure()
        ax = plt.axes(projection='3d')
        # Create a placeholder for the surfaces:
        tpu_polys = []
        if num_surf == 5 or num_surf == 8:  # Hip and gable roofs both have rectangular vertical planes
            for plane in range(0, len(new_zpts) - 1):
                for zpt in range(0, len(new_zpts[plane]) - 1):
                    # Create the surface polygon:
                    tpu_surf = Polygon([new_zpts[plane][zpt], new_zpts[plane + 1][zpt], new_zpts[plane + 1][zpt + 1],
                                        new_zpts[plane][zpt + 1]])
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
                    ax.plot(surf_xs, surf_ys, surf_zs)
            # Show the surfaces for each story:
            plt.show()
            # Add roof surfaces to the end of the list:
            if num_surf == 5:
                roof_surf = Polygon(new_zpts[-1])
                tpu_polys.append(roof_surf)
            elif num_surf == 8:  # Placeholder for hip roof polygons
                pass
        else:
            pass
        # Step 5: Determine the surface number based on building geometry (TPU axes orientation) and wind direction:
        # Note: Surfaces derived from the Shapely minimum rectangle start at the upper left-hand corner and go ccw
        # Given this, whenever the first side < second side, the building's TPU x-axis will be in general E-W direction
        # If second side > first side, the building's TPU x-axis will be in general N-S direction
        # TPU axes use cases:
        # Choose the second line to check the above conditions:
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
                poly_order = [3, 0, 1, 2, 4]
            elif 90 < tpu_wdir <= 180:
                # TPU Surface 3 is windward surface and order is cw: 3, 2, 1, 4, 5
                poly_order = [1, 0, 3, 2, 4]
            elif 180 < tpu_wdir <= 270:
                # TPU Surface 3 is windward surface and order is ccw: 3, 4, 1, 2, 5
                poly_order = [1, 2, 3, 0, 4]
            elif 270 < tpu_wdir <= 360:
                # TPU Surface 1 is windward surface and order is cw: 1, 4, 3, 2, 5
                poly_order = [3, 2, 1, 0, 4]
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
            ax2.plot(poly_xs, poly_ys, poly_zs, color='0.50', linestyle=(0, (1, 1)), label='Surface' + str(i))
        # ax2.legend(loc='best')
        # Plot the building 3D Geometry:
        for poly in self.hasGeometry['3D Geometry'][key]:
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
        plt.axis('off')
        plt.show()
        # Step 6: Save the surfaces to the building description:
        self.hasGeometry['TPU_surfaces'][key] = surf_dict

    def map_TPUsurfaces(self, key):
        # Given the building, determine the use case:
        eave_length = 0
        # Use an equivalent rectangle to calculate aspect ratios:
        rect = self.hasGeometry['Footprint'][
            key].minimum_rotated_rectangle  # user can specify between geodesic or local coords
        xrect, yrect = rect.exterior.xy
        # Determine side lengths:
        side_lines = {'lines': [], 'length': [], 'TPU direction': []}
        max_length = 0
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
        # Find the TPU direction of each line:
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
        hb = self.hasGeometry['Height'] / min(side_lines['length'])
        db = max(side_lines['length']) / min(side_lines['length'])
        # Determine the use case:
        if eave_length == 0:
            if self.hasStorey[-1].adjacentElement['Roof'].hasShape == 'flat':
                num_surf = 5
                surf_dict = {1: None, 2: None, 3: None, 4: None, 5: None}
                # Height to breadth use case
                if hb <= 1 / 4:
                    hb_ratio = 1 / 4
                elif 1 / 4 < hb <= 2 / 4:
                    hb_ratio = 2 / 4
                elif 2 / 4 < hb <= 3 / 4:
                    hb_ratio = 3 / 4
                elif 3 / 4 < hb <= 1:
                    hb_ratio = 1
                else:
                    print('Height to breadth ratio not supported')
                # Depth to breadth use case:
                if db <= 1:
                    db_ratio = 1
                elif 1 < db <= 3 / 2:
                    db_ratio = 3 / 2
                elif 3 / 2 < db <= 5 / 2:
                    db_ratio = 5 / 2
                else:
                    print('Depth to breadth ratio not supported')
            elif self.hasStorey[-1].adjacentElement['Roof'].hasShape == 'hip':  # Note: most common hip roof pitches 4:12-6:12
                num_surf = 8
                surf_dict = {1: None, 2: None, 3: None, 4: None, 5: None, 6: None, 7: None, 8: None}
            elif self.hasStorey[-1].adjacentElement['Roof'].hasShape == 'gable':
                num_surf = 6
                surf_dict = {1: None, 2: None, 3: None, 4: None, 5: None, 6: None}
            else:
                print('Roof shape not supported. Please provide a valid roof shape.')
        else:
            print('Buildings with eaves are not yet supported')
        # Create the TPU footprint geometry from the building's equivalent rectangle:
        for line in side_lines['lines']:
            pass

    def create_zcoords(self, footprint, zcoord):
        # Input footprint polygon (either local or geodesic) and elevation:
        zs = []
        # Create z coordinates for the given building footprint and elevation:
        xs, ys = footprint.exterior.xy
        for pt in range(0, len(xs)):
            # Define z-coordinates for bottom floor of each story:
            zs.append(Point(xs[pt], ys[pt], zcoord))
        return zs


class Parcel(Building):  # Note here: Consider how story/floor assignments may need to change for elevated structures

    def __init__(self, pid, num_stories, occupancy, yr_built, address, area, lon, lat):
        Building.__init__(self, pid, num_stories, occupancy, yr_built, address, area, lon,
                          lat)  # Bring in all of the attributes that are defined in the BIM class for the parcel model
        # Define building-level attributes that are specific to parcel models
        # Building footprint:
        self.assign_footprint(self, num_stories)
        # Clean up building footprint for illustrative example:
        for key in self.hasGeometry['Footprint']:
            if key == 'type':
                pass
            else:
                xcoord, ycoord = self.hasGeometry['Footprint'][key].exterior.xy
                new_point_list = []
                for idx in range(2, len(xcoord) - 2):
                    new_point_list.append(Point(xcoord[idx], ycoord[idx]))
                self.hasGeometry['Footprint'][key] = Polygon(new_point_list)
                xfpt, yfpt = self.hasGeometry['Footprint'][key].exterior.xy
                plt.plot(np.array(xfpt)/3.281, np.array(yfpt)/3.281, 'k')
                plt.xlabel('x [m]', fontsize=9)
                plt.ylabel('y [m]', fontsize=9)
                plt.xticks(fontsize=9)
                plt.yticks(fontsize=9)
                plt.show()
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
                for story_num in range(0, len(self.hasStorey)):
                    zcoord = self.hasStorey[story_num].hasElevation[0]
                    zs = self.create_zcoords(self.hasGeometry['Footprint'][key], zcoord)
                    if story_num == len(self.hasStorey) - 1:
                        zcoord_roof = self.hasStorey[story_num].hasElevation[-1]
                        roof_zs = self.create_zcoords(self.hasGeometry['Footprint'][key], zcoord_roof)
                    else:
                        pass
                    # Save 3D coordinates:
                    new_zpts.append(zs)
                new_zpts.append(roof_zs)
                # With new 3D coordinates for each horizontal plane, create surface geometry:
                # Set up plotting:
                fig = plt.figure()
                ax = plt.axes(projection='3d')
                for plane in range(0, len(new_zpts) - 1):
                    # Add the bottom and top planes for the Story:
                    plane_poly1 = Polygon(new_zpts[plane])
                    plane_poly2 = Polygon(new_zpts[plane + 1])
                    self.hasStorey[plane].hasGeometry['3D Geometry'][key].append(plane_poly1)
                    self.hasStorey[plane].hasGeometry['3D Geometry'][key].append(plane_poly2)
                    for zpt in range(0, len(new_zpts[plane]) - 1):
                        # Create the surface polygon:
                        surf_poly = Polygon([new_zpts[plane][zpt], new_zpts[plane + 1][zpt], new_zpts[plane + 1][zpt + 1], new_zpts[plane][zpt + 1]])
                        # Save the polygon to the storey's geometry:
                        self.hasStorey[plane].hasGeometry['3D Geometry'][key].append(surf_poly)
                        self.hasStorey[plane].hasGeometry['Surfaces'][key].append(surf_poly)
                        # Extract xs, ys, and zs and plot
                        surf_xs = []
                        surf_ys = []
                        surf_zs = []
                        for surf_points in list(surf_poly.exterior.coords):
                            surf_xs.append(surf_points[0])
                            surf_ys.append(surf_points[1])
                            surf_zs.append(surf_points[2])
                        # Plot the surfaces for the entire building to verify:
                        ax.plot(np.array(surf_xs), np.array(surf_ys), np.array(surf_zs), 'k')
                        # Make the panes transparent:
                        ax.w_xaxis.set_pane_color((1.0, 1.0, 1.0, 1.0))
                        ax.w_yaxis.set_pane_color((1.0, 1.0, 1.0, 1.0))
                        ax.w_zaxis.set_pane_color((1.0, 1.0, 1.0, 1.0))
                        # Make the grids transparent:
                        ax.xaxis._axinfo["grid"]['color'] = (1, 1, 1, 0)
                        ax.yaxis._axinfo["grid"]['color'] = (1, 1, 1, 0)
                        ax.zaxis._axinfo["grid"]['color'] = (1, 1, 1, 0)
                        # Plot labels
                        ax.set_xlabel('x')
                        ax.set_ylabel('y')
                        ax.set_zlabel('z')
                # Show the surfaces for each story:
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
                    self.hasGeometry['Surfaces'][key].append(bsurf_poly)
        # Generate a set of building elements (with default attributes) for the parcel:
        self.parcel_elements(self)
        # Update the Building's Elements:
        self.update_elements()
        # Populate instance attributes informed by national survey data:
        survey_data.run(self, ref_bldg_flag=False, parcel_flag=True)  # populate the component-level attributes using survey data
        if survey_data.isSurvey == 'CBECS':
            # Populate code-informed component-level information
            code_informed = bldg_code.FBC(self, loading_flag=False)
            code_informed.roof_attributes(code_informed.hasEdition, self, survey_data.isSurvey)
        else:
            pass

    def assign_footprint(self, parcel, num_stories):
        # Access file with region's building footprint information:
        if parcel.hasLocation['State'] == 'FL' and parcel.hasLocation['County'] == 'Bay':
            jFile = 'D:/Users/Karen/Documents/GitHub/DPBWE/Datasets/Geojson/BayCounty.geojson'
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
                print('More than 1 building footprint identified', parcel.pid, parcel.address)
                # In the future, might be able to do a match by considering the height of the parcel and it's area

        # Assign a regular footprint to any buildings without an open data footprint:
        if parcel.hasGeometry['Footprint']['type'] == 'open data':
            pass
        else:
            parcel.hasGeometry['Footprint']['type'] = 'default'
            length = (sqrt(self.hasGeometry['Total Floor Area'] / num_stories)) * (1 / (2 * sin(
                pi / 4)))  # Divide total building area by number of stories and take square root, divide by 2
            p1 = distance.distance(kilometers=length / 1000).destination((ref_pt.y, ref_pt.x), 45)
            p2 = distance.distance(kilometers=length / 1000).destination((ref_pt.y, ref_pt.x), 135)
            p3 = distance.distance(kilometers=length / 1000).destination((ref_pt.y, ref_pt.x), 225)
            p4 = distance.distance(kilometers=length / 1000).destination((ref_pt.y, ref_pt.x), 315)
            parcel.hasGeometry['Footprint']['geodesic'] = Polygon(
                [(p1.longitude, p1.latitude), (p2.longitude, p2.latitude), (p3.longitude, p3.latitude),
                 (p4.longitude, p4.latitude)])
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
        xdist = xrect[0] - xrect[3]
        ydist = yrect[0] - yrect[3]
        theta = degrees(atan2(ydist, xdist))
        if theta < 0:
            # Find the equivalent positive angle:
            theta = 360 + theta
        else:
            pass
        # Add the building's orientation
        self.hasOrientation = theta
        plt.plot(xrect, yrect)
        plt.show()


    def parcel_elements(self, parcel):
        # Generate parcel elements with (default) attributes:
        # Floor, Ceiling, and Roof Instances - These are conducted by storey to facilitate "hasElement" assignment
        # Exterior Walls - Geometries are derived considering ASCE 7 zone locations on the building footprint:
        asce7 = bldg_code.ASCE7(parcel, loading_flag=True)
        a = asce7.get_cc_zone_width(parcel)  # Determine the zone width
        zone_pts, int_poly, zone2_polys = asce7.find_cc_zone_points(parcel, a, roof_flag=True, edition=None)  # Coordinates for start/end of zone locations
        # Assume that walls span one story for now:
        for storey in range(0, len(parcel.hasStorey)):
            # Create an empty list to hold all elements:
            element_dict = {'Floor': [], 'Walls': [], 'Ceiling': [], 'Roof': []}
            # Generate floor and ceiling instance(s):
            if storey == 0:
                new_floor1 = Floor()
                new_floor1.hasElevation = parcel.hasStorey[storey].hasElevation[0]
                element_dict['Floor'].append(new_floor1)
            else:
                # Reference the prior story's top floor:
                floor1 = parcel.hasStorey[storey - 1].hasElement['Floor'][1]
                element_dict['Floor'].append(floor1)
            # Top floor:
            if storey == len(parcel.hasStorey) - 1:
                new_roof = Roof()
                # Add roof to the storey:
                parcel.hasStorey[storey].adjacentElement.update({'Roof': new_roof})
                element_dict['Roof'].append(new_roof)
            else:
                new_floor2 = Floor()
                new_floor2.hasElevation = parcel.hasStorey[storey].hasElevation[1]
                # new_floor_list.append(new_floor2)
                element_dict['Floor'].append(new_floor2)
            # Create a new ceiling for the floor:
            new_ceiling = Ceiling()
            # Add the ceiling to element_dict:
            element_dict['Ceiling'].append(new_ceiling)
            # Parcel models: Use ASCE 7 C&C zones to create a preliminary set of wall elements
            # Loop through zone_pts and assign geometries to wall elements:
            new_wall_list = []
            for ind in zone_pts.index:
                for col in range(0, len(zone_pts.loc[ind]) - 1):
                    # Create a new Wall Instance:
                    ext_wall = Wall()
                    ext_wall.isExterior = True
                    ext_wall.inLoadPath = True
                    ext_wall.hasGeometry['Height'] = parcel.hasStorey[storey].hasGeometry['Height']
                    ext_wall.hasGeometry['1D Geometry'] = LineString([zone_pts.iloc[ind, col], zone_pts.iloc[
                        ind, col + 1]])  # Line segment with start/end coordinates of wall (respetive to building origin)
                    ext_wall.hasGeometry['Length'] = ext_wall.hasGeometry['1D Geometry'].length
                    new_wall_list.append(ext_wall)
            # Add all walls to element_dict:
            element_dict['Walls'] = new_wall_list
            # Each wall shares interfaces with the walls before and after it:
            for w in range(0, len(new_wall_list) - 1):
                # Create new Interface instance
                new_interface = Interface(new_wall_list[w], new_wall_list[w + 1])
                parcel.hasStorey[storey].hasInterface.append(new_interface)
            # Add all elements to the storey's "hasElement" attribute:
            parcel.hasStorey[storey].containsElement.update({'Ceiling': element_dict['Ceiling']})
            parcel.hasStorey[storey].adjacentElement.update({'Floor': element_dict['Floor']})
            parcel.hasStorey[storey].adjacentElement.update({'Walls': element_dict['Walls']})
            # Update hasElement attribute for the storey:
            parcel.hasStorey[storey].hasElement.update(element_dict)


class Storey(Zone):
    # Sub-class of Zone
    def __init__(self):
        # Populate zone properties:
        new_zone = self
        Zone.__init__(self, new_zone)
        # Attributes outside of BOT Ontology:
        self.hasName = None
        self.hasElevation = []
        self.hasGeometry = {'3D Geometry': {'geodesic': [], 'local': []}, 'Surfaces': {'geodesic': [], 'local': []}}


class Space(Zone):
    # Sub-class of Zone
    def __init__(self, parcel_flag):
        # Populate zone properties:
        new_zone = self
        Zone.__init__(self, new_zone)
        self.hasName = None


class Interface:
    def __init__(self, first_instance, second_instance):
        # An interface is the surface where two building elements: 2 zones or 1 element + 1 zone meet
        self.isInterfaceOf = [first_instance, second_instance]
        # Attributes outside of the BOT Ontology:
        # Interfaces like connections can have a 3D Model and capacity:
        self.hasAnalysisModel = None
        self.hasFixity = None  # typ. options: fixed, pinned, roller, free
        self.hasCapacity = {'type': None, 'value': None}
        self.hasLoadingDemand = {'type': None, 'value': None}
        self.hasFailure = None
        self.hasType = None  # options here are point or plane
