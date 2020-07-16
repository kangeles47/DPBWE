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
    def __init__(self, zone_name):
        self.containsZone = []
        self.containsZone.append(zone_name)
        self.has3DModel = None

class Site(Zone):
    # Sub-class of Zone
    def __init__(self, bldg_list, site_num, num_sites):
        # Zone Name for the Site:
        zone_name = 'Site' + str(site_num)
        # Populate Zone attributes:
        Zone.__init__(self, zone_name)
        # Sites contain one or more buildings:
        self.hasBuilding = {}
        # Sites contain all of the zones, spaces, elements, etc. within each building model:
        self.hasStorey = {}
        self.hasSpace = {}
        self.containsElement = {}
        # Given the number of buildings, create instances of Building and pull attributes
        for i in range(0, len(bldg_list)):
            bldg_name = 'Building' + str(i)
            self.hasBuilding[bldg_name] = Building(bldg_name, pid, num_stories, occupancy, yr_built, address, area, lon, lat) # These attributes come from building list
            self.containsZone.append(Building.containsZone)
            self.hasStorey.update(Building.hasStorey)
            self.hasSpace.update(Building.hasSpace)
            self.containsElement.update(Building.containsElement)
        # Sites can be adjacent to/intersect with other sites (which are also zones)
        if num_sites > 0:
            self.adjacentZone = None
            self.intersectsZone = None
        else:
            pass

class Building(Zone):
    # Sub-class of Zone
    def __init__(self, bldg_name, pid, num_stories, occupancy, yr_built, address, area, lon, lat):
        # Zone Name for the Building:
        zone_name = bldg_name
        Zone.__init__(self, zone_name)
        # Buildings have Storeys:
        self.hasStorey = {}
        # Buildings contain all of the zones, spaces, elements, etc. within each storey:
        self.hasSpace = {}
        self.containsElement = {}
        # Given the number of stories, create instances of Storey and pull attributes:
        # Exception for single family homes:
        if num_stories == 0:
            num_stories = int(num_stories) + 1
        else:
            num_stories = int(num_stories)
        # Create Storey instances:
        for i in range(0, num_stories):
            storey_name = 'Storey' + str(i)
            self.hasStorey[storey_name] = Storey(storey_name)
            self.containsZone.update(Storey.containsZone)
            self.hasSpace.update(Storey.hasSpace)
            self.containsElement.update(Storey.containsElement)
        # Buildings can be adjacent to other buildings
        self.adjacentZone = None
        # Attributes outside of BOT:
        self.hasPID = pid
        self.hasOccupancy = occupancy
        self.hasYearBuilt = int(yr_built)
        self.hasLocation = {'Address': address, 'State': None, 'County': None, 'Geodesic': Point(lon, lat)}
        self.hasArea = float(area) # sq feet
        self.hasHeight = None  # every building has a height, fidelity will determine value
        self.hasWalls = []
        self.hasRoof = None
        self.hasFloors = []
        self.hasStruct_sys = []
        self.hasCeilings = []
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

    def __init__(self, bldg_name, pid, num_stories, occupancy, yr_built, address, area, lon, lat):
        Building.__init__(self, bldg_name, pid, num_stories, occupancy, yr_built, address, area, lon, lat) #Bring in all of the attributes that are defined in the BIM class for the parcel model
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
                parcel.footprint['geometry'] = poly
                parcel.footprint['type'] = 'open data'
            else:
                pass
        # If the lon, lat of the parcel does not fall within bounds of any of the footprints, assign nearest neighbor:
        if parcel.footprint['type'] is None:
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
                parcel.footprint['geometry'] = data['geometry'][neigh_list[1][0]]
                parcel.footprint['type'] = 'open data'
            else:
                print('More than 1 building footprint identified', parcel.pid, parcel.address)
                # In the future, might be able to do a match by considering the height of the parcel and it's area


        # Assign a regular footprint to any buildings without an open data footprint:
        if parcel.footprint['type'] == 'open data':
            pass
        else:
            parcel.footprint['type'] = 'default'
            length = (sqrt(self.hasArea/num_stories))*(1/(2*sin(pi/4))) # Divide total building area by number of stories and take square root, divide by 2
            p1 = distance.distance(kilometers=length/1000).destination((ref_pt.y, ref_pt.x), 45)
            p2 = distance.distance(kilometers=length/1000).destination((ref_pt.y, ref_pt.x), 135)
            p3 = distance.distance(kilometers=length/1000).destination((ref_pt.y, ref_pt.x), 225)
            p4 = distance.distance(kilometers=length/1000).destination((ref_pt.y, ref_pt.x), 315)
            parcel.footprint['geometry'] = Polygon([(p1.longitude, p1.latitude), (p2.longitude, p2.latitude), (p3.longitude, p3.latitude), (p4.longitude, p4.latitude)])

    def parcel_elem(self, parcel):
        # Generate parcel elements with (default) attributes:
        # Exterior Walls - Geometries are derived considering zone locations on the building footprint:
        a = get_zone_width(parcel)  # Determine the zone width
        zone_pts = find_zone_points(parcel, a)  # Coordinates for start/end of zone locations
        # Assume that walls span one story for now:
        for storey in parcel.hasStorey:
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
            storey.hasElement.update({'Walls': new_wall_list})
        # Roof Element
        parcel.hasStorey[-1] = Roof(parcel, storey, parcel_flag=True)


        #Generate floor and ceiling instances:
        if len(parcel.floors) == 0 and len(parcel.ceilings) == 0:
            # Create placeholders: This will give one list per story
            for num in range(0, parcel.num_stories - 1):
                empty_floor = []
                empty_ceiling = []
                parcel.floors.append(empty_floor)
                parcel.ceilings.append(empty_ceiling)

            for idx in range(0, len(parcel.floors)): #for every list
                new_floor = FloorAssem(parcel)
                new_ceiling = CeilingAssem(parcel)
                parcel.floors[idx].append(new_floor) #Add a floor instance to each placeholder
                parcel.ceilings[idx].append(new_ceiling) #Add a ceiling instance to each placeholder

class Storey(Zone):
    # Sub-class of Zone
    def __init__(self, storey_name):
        # Zone Name for the Storey:
        zone_name = storey_name
        Zone.__init__(self, zone_name)
        # Base set of elements:
        self.containsElement = {}
        # Storeys can be adjacent to other storeys
        self.adjacentZone = None
        self.adjacentElement = None
        # Storeys contain zones, spaces, elements, etc.:
        self.hasSpace = {}
        # Attributes outside of BOT Ontology:
        self.hasHeight = None
        self.hasLayout = None  # Floor plan geometry

class Space(Zone):
    # Sub-class of Zone
    def __init__(self, parcel_flag):
        # Zone Name for the Space:
        zone_name = space_name
        Zone.__init__(self, zone_name)
        # Spaces contain elements:
        self.containsElement = None
        # Spaces can be adjacent to other spaces/elements
        self.adjacentZone = None
        self.adjacentElement = None

class Interface:
    def __init__(self, first_instance, second_instance):
        # An interface is the surface where two building elements: 2 zones or 1 element + 1 zone meet
        self.interfaceOf = None
        # Attributes outside of the BOT Ontology:
        # Interfaces like connections can have a 3D Model and capacity:
        self.has3DModel = None
        self.hasCapacity = None



#lon = -85.676188
#lat = 30.190142
#test = Parcel('12345', 4, 'Financial', 1989, '1002 23RD ST W PANAMA CITY 32405', 41134, lon, lat)