# -------------------------------------------------------------------------------
# Name:             zone.py
# Purpose:          Define Zone classes and sub-classes for the ontology-based data model
#
# Author:           Karen Irely Angeles (kangeles@nd.edu)
# Affiliation:      Department of Civil and Environmental Engineering and Earth Sciences,
#                   University of Notre Dame, Notre Dame, IN

# Last updated:          (v1) 01/20/2021
# ------------------------------------------------------------------------------

import numpy as np
from shapely.geometry import Point, Polygon
from OBDM.interface import Interface


class Zone:
    """
    Defines class attributes and methods for objects within the Zone class.

    Notes:
        Original Zone attributes according to the BOT ontology can be found at:
        https://w3c-lbd-cg.github.io/bot/#Zone
    """
    # Zones represent any 3D geometry
    # Sub-classes include Site, Building, Story, Space
    def __init__(self, new_zone):
        """
        Initializes the base attributes for objects belonging to the Zone Class.

        :param new_zone: A Site, Building, Story, or Space instance
        """
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
        # Zones have elements (hasElement). The following are sub-properties of hasElement:
        self.containsElement = {'Walls': [], 'Floor': [], 'Ceiling': [], 'Beam': [], 'Column': []}
        self.adjacentElement = {'Walls': [], 'Floor': [], 'Roof': [], 'Window': []}
        self.intersectingElement = {}  # Building elements that intersect the zone
        self.hasElement = {'Walls': [], 'Floor': [], 'Ceiling': [], 'Beam': [], 'Column': [], 'Roof': [], 'Window': []}
        self.has3DModel = None
        self.hasSimple3DModel = None
        # Attribute(s) outside BOT Ontology:
        self.hasInterface = []  # to keep track of interface objects between zones

    def update_zones(self):
        """"
        A function to easily update the containsZone assignment for any object within the Zone class.

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
                            pass
                            #print('Story space-wise elements have already been updated')
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
                            pass
                            #print('Story space-wise (contains) elements have already been updated')
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
                            pass
                            #print('Building story-wise elements have already been updated')
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
                            pass
                            #print('Building story-wise (contains) elements have already been updated')
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
                pass
                #print('Roof already defined as an adjacent element for this building')
            else:
                try:
                    self.adjacentElement.update({'Roof': self.hasStory[-1].adjacentElement['Roof']})
                except IndexError:
                    pass
            # Add the bottom floor as an adjacentElement for the building:
            if len(self.adjacentElement['Floor']) == 1:
                pass
                #print('Bottom floor already added as an adjacent element for this building')
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
                            pass
                            #print('Site building-wise elements have already been updated')
                    else:
                        # Create a list with existing and new building's elements and choose only unique values:
                        elem_list = self.hasElement[k] + bldg.hasElement[k]
                        unique_elem = set(elem_list)
                        self.hasElement.update({k: list(unique_elem)})
                # Update the containsElement attribute:
                for k in bldg.containsElement:
                    if k in self.containsElement:
                        if bldg.containsElement[k] == self.containsElement[k]:
                            pass
                            #print('Site building-wise (contains) elements have already been updated')
                        else:
                            # Create a list with existing and new space's elements and choose only unique values:
                            elem_list = self.containsElement[k] + bldg.containsElement[k]
                            unique_elem = set(elem_list)
                            self.containsElement.update({k: list(unique_elem)})
                    else:
                        self.containsElement.update({k: bldg.containsElement[k]})

    def update_interfaces(self):
        """
        A function that updates the Zone object's hasInterface attribute.
        This function begins at the bottom of the Zone class hierarchy to update the hasInterface attribute.
        """
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

    def create_zcoords(self, footprint, z):
        """
        A simple function to add z coordinates to footprint geometries with points in (x,y)
        :param footprint: A Shapely Polygon object with (x,y) coordinates
        :param z: The z value that will be added to footprint coordinates (x,y) to (x,y,z)
        :return: A list of z coordinates that can be used to create a new Shapely Polygon
        """
        # Input footprint polygon (either local or geodesic) and elevation:
        zs = []
        # Create z coordinates for the given building footprint and elevation:
        xs, ys = footprint.exterior.xy
        for pt in range(0, len(xs)):
            # Define z-coordinates for bottom floor of each story:
            zs.append(Point(xs[pt], ys[pt], z))
        return zs


class Site(Zone):
    def __init__(self):
        # Populate Zone attributes:
        new_zone = self
        Zone.__init__(self, new_zone)
        # Add Site-specific attributes:
        self.hasZeroPoint = None
        self.hasRoughness = None
        self.hasDebris = {'roof cover': None, 'roof sheathing': None, 'roof member': None}

    def site_gr_poly(self):
        """
        A simple function to generate a rectangular polygon of site's spatial extent (based on buildings lat/lon).
        Site object's hasGeometry attribute is updated with new Shapely Polygon object (geographic coordinates).

        """
        from shapely.geometry import Polygon
        # Cycle through the buildings in site to pull max, min latitude/longitude:
        min_lat, min_lon, max_lat, max_lon = None, None, None, None
        for bldg in self.hasBuilding:
            if min_lat is None:
                min_lat, max_lat = bldg.hasLocation['Geodesic'].y
                min_lon, max_lon = bldg.hasLocation['Geodesic'].x
            else:
                # Latitude check:
                if bldg.hasLocation['Geodesic'].y < min_lat:
                    min_lat = bldg.hasLocation['Geodesic'].y
                elif bldg.hasLocation['Geodesic'].y > max_lat:
                    max_lat = bldg.hasLocation['Geodesic'].y
                else:
                    pass
                # Longitude check:
                if bldg.hasLocation['Geodesic'].x < min_lon:
                    min_lon = bldg.hasLocation['Geodesic'].x
                elif bldg.hasLocation['Geodesic'].x > max_lon:
                    max_lon = bldg.hasLocation['Geodesic'].x
                else:
                    pass
        # Create Polygon with final lat, lon coordinates:
        site_rpoly = Polygon([(min_lon, min_lat), (max_lon, min_lat), (max_lat, max_lon), (min_lon, max_lat)])
        self.hasGeometry['Geodesic Rectangle'] = site_rpoly


class Building(Zone):
    def __init__(self):
        new_zone = self
        Zone.__init__(self, new_zone)
        # Attributes outside of BOT:
        self.hasID = None
        self.hasOccupancy = None
        self.hasYearBuilt = None
        self.hasLocation = {'Address': None, 'Street Number': None, 'City': None, 'Zip Code': None, 'State': None, 'County': None, 'Geodesic': None}
        self.hasGeometry = {'Total Floor Area': None, 'Footprint': {'type': None, 'geodesic': None, 'local': None},
                            'Height': None, '3D Geometry': {'geodesic': [], 'local': []},
                            'Facade': {'geodesic': [], 'local': []}, 'Length Unit': None}
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
        self.hasPermitData = {'disaster': {'number': [], 'description': [], 'permit type': []}, 'other': {'number': [], 'description': [], 'permit type': []}}
        self.hasDamageData = {'roof cover': None, 'roof structure': None, 'cladding': None, 'glazing': None}

    def add_parcel_data(self, pid, num_stories, occupancy, yr_built, address, area, lon, lat, length_unit, loc_flag):
        """
        A simple function to update Building attributes with parcel data and instantiate Story objects

        :param pid: A string containing a unique identifier for the building (e.g., parcel identification number)
        :param num_stories: A number denoting the total number of stories in the building
        :param occupancy: A string describing the building's occupancy class
        :param yr_built: A number describing the building's year of construction
        :param address: A string with the building's address
        :param area: A number providing the building's total floor area
        :param lon: A number providing the building's longitude location
        :param lat: A number providing the building's latitude location
        :param length_unit: A string denoting the input base unit for geometry: 'ft', 'm'
        :param loc_flag: Boolean, True if you want additional location data to be populated
        """
        self.hasID = pid
        # Exception for single family homes and condos:
        if num_stories == 0 or 'COND' in occupancy:
            num_stories = 1
        else:
            num_stories = int(num_stories)
        # Create Story instances:
        for i in range(0, num_stories):
            # Buildings have Stories:
            self.hasStory.append(Story())
        # Create Interface instances to relate stories:
        for stry in range(0, len(self.hasStory) - 1):
            self.hasInterface.append(Interface([self.hasStory[stry], self.hasStory[stry + 1]]))
        self.update_zones()  # Add the stories as zones for this building:
        self.hasGeometry['Total Floor Area'] = float(area)
        self.hasGeometry['Length Unit'] = length_unit
        self.hasOccupancy = occupancy.upper()
        self.hasYearBuilt = int(yr_built)
        self.hasLocation['Address'] = address.upper()
        self.hasLocation['Geodesic'] = Point(lon, lat)
        if loc_flag:
            self.get_location_data()
        else:
            pass
            # Tag the building as "commercial" or "not commercial"
        comm_occupancies = ['PROFESS', 'HOTEL', 'MOTEL', 'FINANCIAL', 'COMMERCIAL', 'HOSP', 'MIXED',
                            'MUNICIPAL', 'OFFICE', 'CONDO', 'COUNT', 'FEDERAL', 'STORE', 'REST', 'COMMON',
                            'PRIVATE', 'SCH', 'SUPERMAR', 'CAMPS', 'COMMUNITY']  # example occupancies
        for substring in self.hasOccupancy.upper().split():
            if any([occ in substring for occ in comm_occupancies]):
                self.isComm = True
                break
            else:
                self.isComm = False

    def get_location_data(self):
        """
        A simple function to extract additional information related to the bldg's location.
        This function currently adds State and County information to the data model of parcels in FL's Bay County.
        :return:
        """
        # Here is where we are going to populate any characteristics relevant to the parcel's location:
        # What we get back from the parcel data is the address and zip code:
        zipcode = int(self.hasLocation['Address'].split()[-1])
        self.hasLocation['Zip Code'] = str(zipcode).strip()
        BayCountyZipCodes = np.arange(32401, 32418)
        BayCountyZipCodes = np.append(BayCountyZipCodes, [32438, 32444, 32456, 32466])
        MonroeCountyZipCodes = np.array([33040, 33037, 33050, 33042, 33070, 33043, 33036, 33041, 33045, 33051, 33001, 33052, 33044])
        CollierCountyZipCodes = np.array([34138, 34137, 34139, 34116, 34140, 34142, 34145, 34114, 34117, 34119, 34120, 34101, 34102, 34103, 34104, 34105, 34109, 34110, 34112, 34113, 34141, 34108])
        FloridaZipCodes = np.concatenate((BayCountyZipCodes, MonroeCountyZipCodes, CollierCountyZipCodes))
        if zipcode in FloridaZipCodes:
            self.hasLocation['State'] = 'FL'
            if zipcode in BayCountyZipCodes:
                cities = ['PANAMA CITY BEACH, PANAMA CITY, MEXICO BEACH, LYNN HAVEN, FOUNTAIN, YOUNGSTOWN']
                self.hasLocation['County'] = 'Bay'
                if 'PANAMA CITY BEACH' in self.hasLocation['Address']:
                    city = 'PANAMA CITY BEACH'
                elif 'PANAMA CITY' in self.hasLocation['Address']:
                    city = 'PANAMA CITY'
                elif 'MEXICO BEACH' in self.hasLocation['Address']:
                    city = 'MEXICO BEACH'
                else:
                    city = ''
            elif zipcode in MonroeCountyZipCodes:
                self.hasLocation['County'] = 'Monroe'
                if 'KEY WEST' in self.hasLocation['Address']:
                    city = 'KEY WEST'
                else:
                    city = ''
            elif zipcode in CollierCountyZipCodes:
                self.hasLocation['County'] = 'Collier'
                if 'MARCO' in self.hasLocation['Address']:
                    city = 'MARCO ISLAND'
                else:
                    city = ''
        else:
            print('County/City/State Information not currently supported')
            city = ''
        if len(city) > 0:
            address_split = self.hasLocation['Address'].split(' ' + city)
            self.hasLocation['Street Number'] = address_split[0].strip()
            self.hasLocation['City'] = city


class Story(Zone):
    def __init__(self):
        # Populate zone properties:
        new_zone = self
        Zone.__init__(self, new_zone)
        # Attributes outside of BOT Ontology:
        self.hasName = None
        self.hasElevation = []
        self.hasGeometry = {'3D Geometry': {'geodesic': [], 'local': []}, 'Facade': {'geodesic': [], 'local': []}}


class Space(Zone):
    def __init__(self):
        # Populate zone properties:
        new_zone = self
        Zone.__init__(self, new_zone)
        self.hasName = None
        self.hasGeometry = {'3D Geometry': {'geodesic': [], 'local': []}, 'Facade': {'geodesic': [], 'local': []}}
