# -------------------------------------------------------------------------------
# Name:             zone.py
# Purpose:          Define Zone classes and sub-classes for the ontology-based data model
#
# Author:           Karen Irely Angeles kangeles@nd.edu
# Affiliation:      Department of Civil and Environmental Engineering and Earth Sciences,
#                   University of Notre Dame, Notre Dame, IN

# Created:          (v1) 01/20/2021
# ------------------------------------------------------------------------------

from shapely.geometry import Point, Polygon
from interface import Interface


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
        self.containsElement = {}
        self.adjacentElement = {}  # Adjacent building elements contribute to bounding the zone
        self.intersectingElement = {}  # Building elements that intersect the zone
        self.hasElement = {}
        self.has3DModel = None
        self.hasSimple3DModel = None
        # Adding in a hasInterface element to keep track of interface objects:
        self.hasInterface = []

    def update_zones(self):
        # Simple function to easily update containsZone assignment
        try:
            for bldg in self.hasBuilding:
                if bldg in self.containsZone:
                    pass
                else:
                    self.containsZone.append(bldg)
        except AttributeError:
            pass
        try:
            for story in self.hasStory:
                if story in self.containsZone:
                    pass
                else:
                    self.containsZone.append(story)
        except AttributeError:
            pass
        try:
            for space in self.hasSpace:
                if space in self.containsZone:
                    pass
                else:
                    self.containsZone.append(space)
        except AttributeError:
            pass

    def update_elements(self):
        # Simple function to easily update hasElement assignment
        if isinstance(self, Site):
            for bldg in self.hasBuilding:
                for k, v in bldg.hasElement:
                    self.hasElement.append(v)
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
                        else:
                            pass
                # Update adjacentElement attribute (exterior walls):
                if 'Walls' in self.adjacentElement:
                    # Create a list with existing and new story's elements and choose only unique values:
                    wall_list = self.adjacentElement['Walls'] + story.adjacentElement['Walls']
                    unique_walls = set(wall_list)
                    self.adjacentElement.update({'Walls': list(unique_walls)})
                else:
                    self.adjacentElement.update({'Walls': story.adjacentElement['Walls']})
            # Add the roof as an adjacentElement for the building:
            if 'Roof' in self.adjacentElement:
                print('Roof already defined as an adjacent element for this building')
            else:
                self.adjacentElement.update({'Roof': self.hasStory[-1].adjacentElement['Roof']})
            # Add the bottom floor as an adjacentElement for the building:
            if 'Floor' in self.adjacentElement:
                print('Bottom floor already added as an adjacent element for this building')
            else:
                self.adjacentElement.update({'Floor': self.hasStory[0].adjacentElement['Floor'][0]})
        elif isinstance(self, Story):
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
            for story in self.hasStory:
                for interface in story.hasInterface:
                    if interface not in self.hasInterface:
                        self.hasInterface.append(interface)
                    else:
                        pass
        elif isinstance(self, Story):
            for space in self.hasSpace:
                for interface in space.hasInterface:
                    if interface not in self.hasInterface:
                        self.hasInterface.append(interface)
                    else:
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
                    'wind pressure': {'external': {'surfaces': [], 'values': []},
                                      'internal': {'surfaces': [], 'values': []},
                                      'total': {'surfaces': [], 'values': []}}, 'debris impact': None,
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
        # Tag the building as "commercial" or "not commercial"
        comm_occupancies = ['profession', 'hotel', 'motel', 'financial']  # example occupancies
        if self.hasOccupancy.lower() in comm_occupancies:
            self.isComm = True
        else:
            self.isComm = False


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
    def __init__(self, parcel_flag):
        # Populate zone properties:
        new_zone = self
        Zone.__init__(self, new_zone)
        self.hasName = None
        self.hasGeometry = {'3D Geometry': {'geodesic': [], 'local': []}, 'Facade': {'geodesic': [], 'local': []}}
