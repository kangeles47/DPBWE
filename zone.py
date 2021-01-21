import numpy as np
from math import sqrt, pi, sin, atan2, degrees
import geopandas as gpd
from shapely.geometry import Point, Polygon, LineString
from shapely import affinity
from scipy import spatial
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from element import Roof, Wall, Floor, Ceiling
import bldg_code
from survey_data import SurveyData
from geopy import distance
from interface import Interface
import pandas as pd
from code_pressures import PressureCalc


# The Building Topology Ontology (BOT) is a minimal ontology for describing the core topological concepts of a building.
# BOT representation (logic) is used to organize asset(s) description(s)
# BOT Documentation: https://w3c-lbd-cg.github.io/bot/#


class Zone:
    # Zones represent any 3D geometry
    # Sub-classes include Site, Building, Story, Space
    def __init__(self, new_zone):
        # Zones can be adjacent to other zones:
        self.adjacentZone = []
        # Zones can intersect:
        self.intersectsZone = []
        # Zones contain themselves and can contain other zones
        # hasBuilding, hasStory, and hasSpace are sub-properties of containsZone
        if isinstance(new_zone, Site):
            self.hasBuilding = []
        elif isinstance(new_zone, Building):
            self.hasStory = []
            self.hasSpace = []
        elif isinstance(new_zone, Story):
            self.hasSpace = []
        else:
            pass
        self.containsZone = []
        # Zones have elements (hasElement). The following are subproperties of hasElement:
        self.containsElement = {'Walls': [], 'Floor': [], 'Ceiling': [], 'Beam': [], 'Column': []}
        self.adjacentElement = {'Walls': [], 'Floor': [], 'Roof': [], 'Window': []}
        self.intersectingElement = {}  # Building elements that intersect the zone
        self.hasElement = {'Walls': [], 'Floor': [], 'Ceiling': [], 'Beam': [], 'Column': [], 'Roof': [], 'Window': []}
        self.has3DModel = None
        self.hasSimple3DModel = None
        # Adding in a hasInterface element to keep track of interface objects:
        self.hasInterface = []

    def update_zones(self):
        """"
        A function to easily update the containsZone assignment for any object within the Zone class.

        This function begins at the bottom of the Zone class hierarchy to update the containsZone attribute.
        """
        if isinstance(self, Site):
            for bldg in self.hasBuilding:
                if bldg in self.containsZone:
                    pass
                else:
                    self.containsZone.append(bldg)
                for story in bldg.hasStory:
                    if story in self.containsZone:
                        pass
                    else:
                        self.containsZone.append(story)
                    for space in story.hasSpace:
                        if space in self.containsZone:
                            pass
                        else:
                            self.containsZone.append(space)
        elif isinstance(self, Building):
            for story in self.hasStory:
                if story in self.containsZone:
                    pass
                else:
                    self.containsZone.append(story)
                for space in story.hasSpace:
                    if space in self.containsZone:
                        pass
                    else:
                        self.containsZone.append(space)
        elif isinstance(self, Story):
            for space in self.hasSpace:
                if space in self.containsZone:
                    pass
                else:
                    self.containsZone.append(space)
        else:
            print('Zone Space objects cannot contain other Zones')

    def update_elements(self):
        """
        A function to easily update the hasElement and containsElement assignment for any object within the Zone class.
        A function to easily update the adjacentElement assignment for Building objects.

        This function begins at the bottom of the Zone class hierarchy to update the Zone object's
        hasElement, containsElement, (and for Buildings) adjacentElement attributes.
        :return: Various print statement to inform the user that element(s) have already been updated (when applicable)
        """
        # All Zone classes: Update hasElement attribute first by looking at:
        # adjacentElement and containsElement attributes:
        for k in self.adjacentElement:
            if k in self.hasElement:
                for v in self.adjacentElement[k]:
                    if v in self.hasElement:
                        pass
                    else:
                        self.hasElement[k].append(v)
            else:
                # Create a list with existing and missing elements and add only unique values:
                elem_list = self.hasElement[k] + self.adjacentElement[k]
                unique_elem = set(elem_list)
                self.hasElement.update({k: list(unique_elem)})
        for k in self.containsElement:
            if k in self.hasElement:
                for v in self.containsElement[k]:
                    if v in self.hasElement:
                        pass
                    else:
                        self.hasElement[k].append(v)
            else:
                # Create a list with existing and missing elements and add only unique values:
                elem_list = self.hasElement[k] + self.containsElement[k]
                unique_elem = set(elem_list)
                self.hasElement.update({k: list(unique_elem)})
        if isinstance(self, Story):
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
                # Update the containsElement attribute:
                for k in space.containsElement:
                    if k in self.containsElement:
                        if space.containsElement[k] == self.containsElement[k]:
                            print('Story space-wise (contains) elements have already been updated')
                        else:
                            # Create a list with existing and new space's elements and choose only unique values:
                            elem_list = self.containsElement[k] + space.containsElement[k]
                            unique_elem = set(elem_list)
                            self.containsElement.update({k: list(unique_elem)})
                    else:
                        self.containsElement.update({k: space.containsElement[k]})
        elif isinstance(self, Building):
            for story in self.hasStory:
                for k in story.hasElement:
                    # Update the hasElement attribute:
                    if k in self.hasElement:
                        if story.hasElement[k] == self.hasElement[k]:
                            print('Building story-wise elements have already been updated')
                        else:
                            # Create a list with existing and new story's elements and choose only unique values:
                            elem_list = self.hasElement[k] + story.hasElement[k]
                            unique_elem = set(elem_list)
                            self.hasElement.update({k: list(unique_elem)})
                    else:
                        self.hasElement.update({k: story.hasElement[k]})
                    # Update the containsElement attribute:
                    if k in self.containsElement:
                        if story.containsElement[k] == self.containsElement[k]:
                            print('Building story-wise (contains) elements have already been updated')
                        else:
                            # Create a list with existing and new story's elements and choose only unique values:
                            elem_list = self.containsElement[k] + story.containsElement[k]
                            unique_elem = set(elem_list)
                            self.containsElement.update({k: list(unique_elem)})
                    else:
                        if k in story.containsElement:
                            self.containsElement.update({k: story.containsElement[k]})
                # Update adjacentElement attribute (exterior walls):
                if 'Walls' in self.adjacentElement:
                    # Create a list with existing and new story's elements and choose only unique values:
                    wall_list = self.adjacentElement['Walls'] + story.adjacentElement['Walls']
                    unique_walls = set(wall_list)
                    self.adjacentElement.update({'Walls': list(unique_walls)})
                else:
                    self.adjacentElement.update({'Walls': story.adjacentElement['Walls']})
            # Add the roof and bottom floor into adjacentElement if needed:
            if len(self.adjacentElement['Roof']) == 1:
                print('Roof already defined as an adjacent element for this building')
            else:
                try:
                    self.adjacentElement.update({'Roof': self.hasStory[-1].adjacentElement['Roof']})
                except IndexError:
                    pass
            # Add the bottom floor as an adjacentElement for the building:
            if len(self.adjacentElement['Floor']) == 1:
                print('Bottom floor already added as an adjacent element for this building')
            else:
                try:
                    self.adjacentElement.update({'Floor': self.hasStory[0].adjacentElement['Floor'][0]})
                except IndexError:
                    pass
        elif isinstance(self, Site):
            for bldg in self.hasBuilding:
                # Update the hasElement attribute:
                for k in bldg.hasElement:
                    if k in self.hasElement:
                        if bldg.hasElement[k] == self.hasElement[k]:
                            print('Site building-wise elements have already been updated')
                    else:
                        # Create a list with existing and new building's elements and choose only unique values:
                        elem_list = self.hasElement[k] + bldg.hasElement[k]
                        unique_elem = set(elem_list)
                        self.hasElement.update({k: list(unique_elem)})
                # Update the containsElement attribute:
                for k in bldg.containsElement:
                    if k in self.containsElement:
                        if bldg.containsElement[k] == self.containsElement[k]:
                            print('Site building-wise (contains) elements have already been updated')
                        else:
                            # Create a list with existing and new space's elements and choose only unique values:
                            elem_list = self.containsElement[k] + bldg.containsElement[k]
                            unique_elem = set(elem_list)
                            self.containsElement.update({k: list(unique_elem)})
                    else:
                        self.containsElement.update({k: bldg.containsElement[k]})

    def update_interfaces(self):
        # Simple function to easily update hasElement assignment
        try:
            for space in self.hasSpace:
                for interface in space.hasInterface:
                    if interface not in self.hasInterface:
                        self.hasInterface.append(interface)
                    else:
                        pass
        except AttributeError:
            pass
        try:
            for story in self.hasStory:
                for interface in story.hasInterface:
                    if interface not in self.hasInterface:
                        self.hasInterface.append(interface)
                    else:
                        pass
        except AttributeError:
            pass
        try:
            for bldg in self.hasBuilding:
                for interface in bldg.hasInterface:
                    if interface not in self.hasInterface:
                        self.hasInterface.append(interface)
                    else:
                        pass
        except AttributeError:
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


class Site(Zone):
    # Sub-class of Zone
    def __init__(self):
        # Populate Zone attributes:
        new_zone = self
        Zone.__init__(self, new_zone)
        # Add Site-specific attributes:
        self.hasZeroPoint = None
        self.hasRoughness = None

    def add_building(self, bldg):
        self.hasBuilding.append(bldg)
        # Sites contain all of the zones, spaces, elements, etc. within each building model:
        self.update_zones()
        self.update_elements()


class Building(Zone):
    # Sub-class of Zone
    def __init__(self):
        new_zone = self
        Zone.__init__(self, new_zone)
        # Attributes outside of BOT:
        self.hasID = None
        self.hasOccupancy = None
        self.hasYearBuilt = None
        self.hasLocation = {'Address': None, 'State': None, 'County': None, 'Geodesic': None}
        self.hasGeometry = {'Total Floor Area': None, 'Footprint': {'type': None, 'geodesic': None, 'local': None},
                            'Height': None, '3D Geometry': {'geodesic': [], 'local': []},
                            'Facade': {'geodesic': [], 'local': []}, 'TPU_surfaces': {'geodesic': [], 'local': []}}
        self.hasOrientation = None
        self.hasOutputVariable = {'repair cost': None, 'downtime': None, 'fatalities': None}
        self.hasFundamentalPeriod = {'x': None, 'y': None}
        self.hasStructuralSystem = {'type': None, 'elements': []}
        self.hasImportanceFactor = None
        edp_dict = {'peak interstory drift ratio': None, 'peak absolute velocity': None,
                    'peak absolute acceleration': None, 'wind speed': None,
                    'wind pressure': {'external': {'surfaces': [], 'values': []}, 'internal': {'surfaces': [], 'values': []}, 'total': {'surfaces': [], 'values': []}}, 'debris impact': None,
                    'axial force': None, 'shear force': None, 'bending moment': None, 'peak flexural stress': None,
                    'peak shear stress': None, 'peak flexural strain': None, 'curvature': None, 'rotation': None,
                    'elongation': None}
        self.hasCapacity = edp_dict
        self.hasDemand = edp_dict
        self.hasRiskCategory = None
        self.hasEffSeismicWeight = None
        self.hasDampingValue = None
        self.hasServiceLife = None
        self.isComm = False

    def add_parcel_data(self, pid, num_stories, occupancy, yr_built, address, area, lon, lat):
        self.hasID = pid
        # Exception for single family homes:
        if num_stories == 0:
            num_stories = int(num_stories) + 1
        else:
            num_stories = int(num_stories)
        # Create Story instances:
        for i in range(0, num_stories):
            # Buildings have Storys:
            self.hasStory.append(Story())
        # Create Interface instances to relate stories:
        for stry in range(0, len(self.hasStory) - 1):
            self.hasInterface.append(Interface([self.hasStory[stry], self.hasStory[stry + 1]]))
        # Buildings contain all of the zones, spaces, elements, etc. within each story:
        self.update_zones()
        # Attributes outside of BOT:
        self.hasGeometry['Total Floor Area'] = float(area)
        self.hasOccupancy = occupancy
        self.hasYearBuilt = int(yr_built)
        self.hasLocation['Address'] = address
        self.hasLocation['Geodesic'] = Point(lon, lat)
        # Define additional attributes regarding the building location:
        self.location_data()
        # Tag the building as "commercial" or "not commercial"
        comm_occupancies = ['profession', 'hotel', 'motel', 'financial']
        if self.hasOccupancy.lower() in comm_occupancies:
            self.isComm = True
        else:
            self.isComm = False

    def location_data(self):
        # Here is where we are going to populate any characteristics relevant to the parcel's location:
        # What we get back from the parcel data is the address and zip code:
        zipcode = int(self.hasLocation['Address'].split()[-1])
        BayCountyZipCodes = np.arange(32401, 32418)
        BayCountyZipCodes = np.append(BayCountyZipCodes, [32438, 32444, 32466])

        if zipcode in BayCountyZipCodes:
            self.hasLocation['State'] = 'FL'
            self.hasLocation['County'] = 'Bay'
        else:
            print('County and State Information not currently supported')


class Parcel(Building):  # Note here: Consider how story/floor assignments may need to change for elevated structures

    def __init__(self, pid, num_stories, occupancy, yr_built, address, area, lon, lat):
        Building.__init__(self)  # Bring in all of the attributes that are defined in the BIM class for the parcel model
        # Add parcel data:
        self.add_parcel_data(pid, num_stories, occupancy, yr_built, address, area, lon, lat)
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
                plt.plot(np.array(xfpt) / 3.281, np.array(yfpt) / 3.281, 'k')
                #if key == 'local':
                    # Rotate the footprint to create a "rotated cartesian" axis:
                 #   rect = self.hasGeometry['Footprint'][key].minimum_rotated_rectangle
                  #  spts = list(rect.exterior.coords)
                   # theta = degrees(atan2((spts[1][0] - spts[2][0]), (spts[1][1] - spts[2][1])))
                    # Rotate the the building footprint to create the TPU axis:
                    #rotated_b = affinity.rotate(Polygon(new_point_list), theta, origin='centroid')
                    #rflag = True
                    #rx, ry = rotated_b.exterior.xy
                    #plt.plot(np.array(rx) / 3.281, np.array(ry) / 3.281, color='gray', linestyle='dashed')
                    #plt.legend(['local Cartesian', 'rotated Cartesian'], prop={"size":14}, loc='upper right')
                #else:
                 #   rflag= False
                    # Uncomment to plot the footprint:
                plt.xlabel('x [m]', fontsize=14)
                plt.ylabel('y [m]', fontsize=14)
                plt.xticks(fontsize=14)
                plt.yticks(fontsize=14)
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
                #fig = plt.figure()
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
                        ax.set_xlabel('x [m]', fontsize=12)
                        ax.set_ylabel('y [m]', fontsize=12)
                        ax.set_zlabel('z [m]', fontsize=12)
                        ax.set_zlim(0, 16)
                # Show the surfaces for each story:
                ax.xaxis.set_tick_params(labelsize=12)
                ax.yaxis.set_tick_params(labelsize=12)
                ax.zaxis.set_tick_params(labelsize=12)
                #plt.show()
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
        self.parcel_elements(self, zone_flag=False)
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
            jFile = 'C:/Users/Karen/PycharmProjects/DPBWE/Datasets/Geojson/BayCounty.geojson'
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
        #plt.plot(xrect, yrect)
        #plt.show()

    def parcel_elements(self, parcel, zone_flag):
        # Generate parcel elements with (default) attributes:
        # Floor, Ceiling, and Roof Instances - These are conducted by story to facilitate "hasElement" assignment
        # Exterior Walls - Parcel approach: Geometries are derived considering ASCE 7 C&C zone locations:
        # Exterior Walls - Other approach: Geometries are derived using footprint vertices
        if zone_flag:
            asce7 = bldg_code.ASCE7(parcel, loading_flag=True)
            a = asce7.get_cc_zone_width(parcel)  # Determine the zone width
            zone_pts, int_poly, zone2_polys = asce7.find_cc_zone_points(parcel, a, roof_flag=True, edition=None)  # Coordinates for start/end of zone locations
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
                # Add roof to the story:
                parcel.hasStory[story].adjacentElement.update({'Roof': new_roof})
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
                        ext_wall.hasGeometry['Length'] = ext_wall.hasGeometry['1D Geometry'].length
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


class Story(Zone):
    # Sub-class of Zone
    def __init__(self):
        # Populate zone properties:
        new_zone = self
        Zone.__init__(self, new_zone)
        # Attributes outside of BOT Ontology:
        self.hasName = None
        self.hasElevation = []
        self.hasGeometry = {'3D Geometry': {'geodesic': [], 'local': []}, 'Facade': {'geodesic': [], 'local': []}}


class Space(Zone):
    # Sub-class of Zone
    def __init__(self):
        # Populate zone properties:
        new_zone = self
        Zone.__init__(self, new_zone)
        self.hasName = None
        self.hasGeometry = {'3D Geometry': {'geodesic': [], 'local': []}, 'Facade': {'geodesic': [], 'local': []}}
