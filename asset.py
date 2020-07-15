import numpy as np
from math import sqrt, pi, sin
import geopandas as gpd
from shapely.geometry import Point, Polygon
from scipy import spatial
import matplotlib.pyplot as plt
from assembly import RoofAssem, WallAssem, FloorAssem, CeilingAssem
import bldg_code
from survey_data import SurveyData
from geopy import distance

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
            self.hasBuilding[bldg_name] = Building(bldg_name, pid, num_stories, occupancy, yr_built, address, area, lon, lat)
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
            self.hasStorey[storey_name] = Storey(element_lst, storey_name)
            self.containsZone.update(Storey.containsZone)
            self.hasSpace.update(Storey.hasSpace)
            self.containsElement.update(Storey.containsElement)
        # Buildings can be adjacent to other buildings
        self.adjacentZone = None
        # Attribute outside of BOT: Building Footprint:
        self.footprint = None  # Maybe add to has3DModel attribute
        # BOT: Buildings have an origin (should be assigned using appropriate ontology in future use):
        self.hasZeroPoint = Point(lon, lat)
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

        # Using basic building attributes, set up building metavariables:
        # 1) Tag the building as "commercial" or "not commercial"
        if self.occupancy == "PROFESSION" or self.occupancy == "HOTEL" or self.occupancy == "MOTEL" or self.occupancy == "FINANCIAL":
            self.is_comm = True
        else:
            self.is_comm = False

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

class Storey(Zone):
    # Sub-class of Zone
    def __init__(self, element_lst, storey_name):
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

class Element:
    def __init__(self, storey, parcel_flag):
        # Element type:
        self.type = None
        # Elements can have subelements:
        self.hasSubElement = None
        # Elements can be adjacent to other elements
        self.adjacentZone = None
        # Elements can be modeled as well:
        self.has3DModel = None

class Interface:
    def __init__(self, first_instance, second_instance):
        # An interface is the surface where two building elements: 2 zones or 1 element + 1 zone meet
        self.interfaceOf = None
        # Attributes outside of the BOT Ontology:
        # Interfaces like connections can have a 3D Model and capacity:
        self.has3DModel = None
        self.hasCapacity = None


class BIM:

    # Here we might have to write some sort of function that parses the .JSON file from the SimCenter BIM Model

    def __init__(self, pid, num_stories, occupancy, yr_built, address, area, lon, lat):
        self.pid = pid
        # Exception for single family homes:
        if num_stories == 0:
            self.num_stories = int(num_stories) + 1
        else:
            self.num_stories = int(num_stories)
        self.occupancy = occupancy
        self.yr_built = int(yr_built)
        self.address = address
        self.lon = float(lon)
        self.lat = float(lat)
        self.area = float(area)/10.764 # sq feet to sq meters
        self.h_bldg = None  # every building has a height, fidelity will determine value
        self.walls = []
        self.roof = None
        self.floors = []
        self.struct_sys = []
        self.ceilings = []
        self.footprint = {'type': None, 'geometry': None}

        # Using basic building attributes, set up building metavariables:
        # 1) Tag the building as "commercial" or "not commercial"
        if self.occupancy == "PROFESSION" or self.occupancy == "HOTEL" or self.occupancy == "MOTEL" or self.occupancy == "FINANCIAL":
            self.is_comm = True
        else:
            self.is_comm = False

        # 2) Define additional attributes regarding the building location:
        self.location_data(self)

    def location_data(self, Building):
        # Here is where we are going to populate any characteristics relevant to the parcel's location:
        # What we get back from the parcel data is the address and zip code:
        zipcode = int(BIM.address.split()[-1])
        BayCountyZipCodes = np.arange(32401, 32418)
        BayCountyZipCodes = np.append(BayCountyZipCodes, [32438, 32444, 32466])

        if zipcode in BayCountyZipCodes:
            BIM.state = 'FL'
            BIM.county = 'Bay'
        else:
            print('County and State Information not currently supported')

# Now that we have defined the BIM superclass, it is time to define the Parcel subclass (we want all of our parcels to inherit the basic attributes outlined above)

class Parcel(BIM):

    def __init__(self, pid, num_stories, occupancy, yr_built, address, area, lon, lat):
        BIM.__init__(self, pid, num_stories, occupancy, yr_built, address, area, lon, lat) #Bring in all of the attributes that are defined in the BIM class for the parcel model
        # Define building-level attributes that are specific to parcel models
        # Building footprint:
        self.assign_footprint(self)
        # Create an instance of the BldgCode class and populate building-level code-informed attributes for the parcel:
        desc_flag = True  # Need to access a building code that will give us code-based descriptions
        if self.state == 'FL':
            code_informed = bldg_code.FBC(self, desc_flag)
        else:
            pass
        # Generate a preliminary set of assemblies:
        self.prelim_assem(self)
        # Populate instance attributes informed by national survey data:
        survey_data = SurveyData()  # create an instance of the survey data class
        survey_data.run(self)  # populate the parcel information
        if survey_data.survey == 'CBECS':
            # Fill in code-informed assembly-level information
            code_informed.roof_attributes(code_informed.edition, self, survey_data.survey)
        else:
            pass

    def assign_footprint(self, parcel):
        # Access file with region's building footprint information:
        if parcel.state == 'FL' and parcel.county == 'Bay':
            jFile = 'D:/Users/Karen/Documents/GitHub/DPBWE/Datasets/Geojson/BayCounty.geojson'
        else:
            print('Footprints for this region currently not supported')

        data = gpd.read_file(jFile)
        # data is a DataFrame object with column label = ['geometry'] and indexes = [0: end]
        # Accessing a specific Polygon object then requires: data['geometry'][index]

        # Need to access Polygon geometry in order to determine if the parcel's location is within that polygon:
        # Create a Point object with the parcel's lon, lat coordinates:
        p1 = Point(parcel.lon, parcel.lat)

        # Loop through dataset to find the parcel's corresponding footprint:
        for row in range(0, len(data["geometry"])):
            # Check if point is within the polygon in this row:
            poly = data['geometry'][row]
            if p1.within(poly):
                parcel.footprint['geometry'] = poly
                parcel.footprint['type'] = 'open data'
            else:
                pass
        # If the lon, lat of the parcel does not fall within bounds of any of the footprints, assign nearest neighbor:
        if parcel.footprint["type"] is None:
            # Populate the KD tree using the centroids of the building footprints:
            centroids = data['geometry'].apply(lambda ind: [ind.centroid.x, ind.centroid.y]).tolist()
            kdtree = spatial.KDTree(centroids)
            # Set up an array of (small) longitude, latitude radii:
            radii = np.arange(0.0001, 0.01, 0.0001)
            # Find the nearest neighbors within the radius (increase until neighbors are present):
            neigh_list = []
            for rad in radii:
                neigh_list.append(kdtree.query_ball_point([parcel.lon, parcel.lat], r=rad))
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
            length = (sqrt(self.area/self.num_stories))*(1/(2*sin(pi/4))) # Divide total building area by number of stories and take square root, divide by 2
            p1 = distance.distance(kilometers=length/1000).destination((parcel.lat, parcel.lon), 45)
            p2 = distance.distance(kilometers=length/1000).destination((parcel.lat, parcel.lon), 135)
            p3 = distance.distance(kilometers=length/1000).destination((parcel.lat, parcel.lon), 225)
            p4 = distance.distance(kilometers=length/1000).destination((parcel.lat, parcel.lon), 315)
            parcel.footprint['geometry'] = Polygon([(p1.longitude, p1.latitude), (p2.longitude, p2.latitude), (p3.longitude, p3.latitude), (p4.longitude, p4.latitude)])
            x,y = parcel.footprint['geometry'].exterior.xy
            #fig, ax = plt.subplots()
            #ax.plot(x,y)
            #plt.plot(x,y)
            #ax.axis('equal')
            #plt.show()
            #a = 0

    def prelim_assem(self, parcel):
        #IF statements here may be unnecessary but keeping them for now
        # Generate preliminary instances of walls - 4 for every floor
        if len(parcel.walls) == 0 and parcel.footprint['type'] == 'regular':
            # Create placeholders: This will give one list per story
            for number in range(0, parcel.num_stories-1):
                empty = []
                parcel.walls.append(empty)

            # Assign one wall for each side on each story:
            for lst in range(0,4):  # four sides
                for index in range(0, len(parcel.walls)): #for every list (story)
                    ext_wall = WallAssem(parcel)
                    ext_wall.is_exterior = 1
                    ext_wall.height = parcel.h_story[0]
                    ext_wall.base_floor = index
                    ext_wall.top_floor = index+1
                    ext_wall.location = lst+1 # adding 1 since Python indexing starts at 0
                    if lst % 2 == 0:
                        ext_wall.length = parcel.footprint['geometry']['breadth']
                    else:
                        ext_wall.length = parcel.footprint['geometry']['depth']
                    # Add the wall to its corresponding list:
                    parcel.walls[index].append(ext_wall) # Add a wall instance to each placeholder

        # Generate roof instance
        if parcel.roof == None:
            # Create a roof instance for the parcel:
            parcel.roof = RoofAssem(parcel)
        else:
            print('A roof is already defined for this parcel')

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

#lon = -85.676188
#lat = 30.190142
#test = Parcel('12345', 4, 'Financial', 1989, '1002 23RD ST W PANAMA CITY 32405', 41134, lon, lat)