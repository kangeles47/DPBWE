import numpy as np
from math import sqrt, pi, sin
import geopandas as gpd
from shapely.geometry import Point, Polygon, LineString
from scipy import spatial
import matplotlib.pyplot as plt
from element import Roof, Wall, Floor, Ceiling
import bldg_code
from survey_data import SurveyData
from geopy import distance
from code_capacities import get_zone_width,find_zone_points

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
        self.adjacentElement = []  # Adjacent building elements contribute to bounding the zone
        self.intersectingElement = []  # Building elements that intersect the zone
        self.hasElement = []
        self.has3DModel = None

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
        for k, v in self.containsElement:
            self.hasElement.append(v)

class Site(Zone):
    # Sub-class of Zone
    def __init__(self, bldg_list, site_num, num_sites):
        # Populate Zone attributes:
        Zone.__init__(self)
        # Sites contain one or more buildings
        # Sites contain all of the zones, spaces, elements, etc. within each building model:
        # Given the number of buildings, create instances of Building and pull attributes
        for i in range(0, len(bldg_list)):
            # Sites contain one or more buildings
            new_bldg = Building(pid, num_stories, occupancy, yr_built, address, area, lon, lat) # These attributes come from building list
            self.hasBuilding[new_bldg.hasPID] = new_bldg
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
        Zone.__init__(self)
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
        # Buildings contain all of the zones, spaces, elements, etc. within each storey:
        self.update_zones()
        self.update_elements()
        # Attributes outside of BOT:
        self.hasPID = pid
        self.hasOccupancy = occupancy
        self.hasYearBuilt = int(yr_built)
        self.hasLocation = {'Address': address, 'State': None, 'County': None, 'Geodesic': Point(lon, lat)}
        self.hasArea = float(area) # sq feet
        self.hasHeight = None  # every building has a height, fidelity will determine value
        self.hasFootprint = {'type': None, 'geometry': None}
        # BOT: Buildings have an origin (should be assigned using appropriate ontology in future use, using lon, lat for now):
        self.hasZeroPoint = Point(lon, lat)

        # Using basic building attributes, set up building metavariables:
        # 1) Tag the building as "commercial" or "not commercial"
        if self.hasOccupancy == "PROFESSION" or self.hasOccupancy == "HOTEL" or self.hasOccupancy == "MOTEL" or self.hasOccupancy == "FINANCIAL":
            self.isComm = True
        else:
            self.isComm = False

        # 2) Define additional attributes regarding the building location:
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


class Parcel(Building):

    def __init__(self, pid, num_stories, occupancy, yr_built, address, area, lon, lat):
        Building.__init__(self, pid, num_stories, occupancy, yr_built, address, area, lon, lat) #Bring in all of the attributes that are defined in the BIM class for the parcel model
        # Define building-level attributes that are specific to parcel models
        # Building footprint:
        self.assign_footprint(self, num_stories)
        # Create an instance of the BldgCode class and populate building-level code-informed attributes for the parcel:
        desc_flag = True  # Need to access a building code that will give us code-based descriptions
        if self.hasLocation['State'] == 'FL':
            code_informed = bldg_code.FBC(self, desc_flag)
        else:
            pass
        # Generate a set of building elements (with default attributes) for the parcel:
        self.parcel_elements(self)
        # Populate instance attributes informed by national survey data:
        survey_data = SurveyData()  # create an instance of the survey data class
        survey_data.run(self)  # populate the parcel information
        if survey_data.survey == 'CBECS':
            # Fill in code-informed assembly-level information
            code_informed.roof_attributes(code_informed.edition, self, survey_data.survey)
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
                parcel.hasFootprint['geometry'] = poly
                parcel.hasFootprint['type'] = 'open data'
            else:
                pass
        # If the lon, lat of the parcel does not fall within bounds of any of the footprints, assign nearest neighbor:
        if parcel.hasFootprint['type'] is None:
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
                parcel.hasFootprint['geometry'] = data['geometry'][neigh_list[1][0]]
                parcel.hasFootprint['type'] = 'open data'
            else:
                print('More than 1 building footprint identified', parcel.pid, parcel.address)
                # In the future, might be able to do a match by considering the height of the parcel and it's area


        # Assign a regular footprint to any buildings without an open data footprint:
        if parcel.hasFootprint['type'] == 'open data':
            pass
        else:
            parcel.hasFootprint['type'] = 'default'
            length = (sqrt(self.hasArea/num_stories))*(1/(2*sin(pi/4))) # Divide total building area by number of stories and take square root, divide by 2
            p1 = distance.distance(kilometers=length/1000).destination((ref_pt.y, ref_pt.x), 45)
            p2 = distance.distance(kilometers=length/1000).destination((ref_pt.y, ref_pt.x), 135)
            p3 = distance.distance(kilometers=length/1000).destination((ref_pt.y, ref_pt.x), 225)
            p4 = distance.distance(kilometers=length/1000).destination((ref_pt.y, ref_pt.x), 315)
            parcel.hasFootprint['geometry'] = Polygon([(p1.longitude, p1.latitude), (p2.longitude, p2.latitude), (p3.longitude, p3.latitude), (p4.longitude, p4.latitude)])

    def parcel_elements(self, parcel):
        # Generate parcel elements with (default) attributes:
        # Floor, Ceiling, and Roof Instances - These are conducted by storey to facilitate "hasElement" assignment
        # Exterior Walls - Geometries are derived considering zone locations on the building footprint:
        a = get_zone_width(parcel)  # Determine the zone width
        zone_pts = find_zone_points(parcel, a)  # Coordinates for start/end of zone locations
        # Assume that walls span one story for now:
        for storey in parcel.hasStorey:
            # Generate floor and ceiling instance(s):
            new_floor_list = []
            new_floor1 = Floor(parcel, storey, parcel_flag=True)
            new_floor1.hasElevation = storey.hasElevation[0]
            new_floor_list.append(new_floor1)
            new_ceiling = Ceiling(parcel, storey, parcel_flag=True)
            if storey == parcel.hasStorey[-1]:
                new_roof = [Roof(parcel, storey, parcel_flag=True)]
                # Add roof to the storey:
                storey.containsElement.update({'Roof': new_roof})
            else:
                new_floor2 = Floor(parcel, storey, parcel_flag=True)
                new_floor2.hasElevation = storey.hasElevation[1]
                new_floor_list.append(new_floor2)
            # Add elements to the storey:
            storey.containsElement.update({'Floors': new_floor_list, 'Ceiling': new_ceiling})
            # Populate relational attributes for storey:
            storey.adjacentElement.update()
            # Loop through zone_pts and assign geometries to wall elements:
            for row in zone_pts:
                # Parcel models will have three "walls" by default, corresponding to each zone on a side of the building:
                new_wall_list = []
                for col in range(0, len(row)):
                    # Create a new Wall Instance:
                    ext_wall = Wall(parcel, storey, parcel_flag=True)
                    ext_wall.isExterior = True
                    ext_wall.hasHeight = storey.hasHeight
                    ext_wall.has1DModel = LineString([row[col], row[col+1]])  # Line segment with start/end coordinates of wall (respetive to building origin)
                    ext_wall.hasLength = ext_wall.has1DModel.length
                    new_wall_list.append(ext_wall)
            # Add new exterior walls to the storey "hasElement" attribute:
            storey.containsElement.update({'Walls': new_wall_list})


class Storey(Zone):
    # Sub-class of Zone
    def __init__(self):
        Zone.__init__(self)
        # Attributes outside of BOT Ontology:
        self.hasName = None
        self.hasElevation = []
        self.hasHeight = None
        self.hasLayout = None  # Floor plan geometry


class Space(Zone):
    # Sub-class of Zone
    def __init__(self, parcel_flag):
        Zone.__init__(self)


class Interface:
    def __init__(self, first_instance, second_instance):
        # An interface is the surface where two building elements: 2 zones or 1 element + 1 zone meet
        self.interfaceOf = None
        # Attributes outside of the BOT Ontology:
        # Interfaces like connections can have a 3D Model and capacity:
        self.has3DModel = None
        self.hasCapacity = None



lon = -85.676188
lat = 30.190142
test = Parcel('12345', 4, 'Financial', 1989, '1002 23RD ST W PANAMA CITY 32405', 41134, lon, lat)