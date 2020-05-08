import numpy as np
from math import sqrt, pi, cos, asin, sin, atan2, degrees
import geopandas as gpd
from shapely.geometry import Point, Polygon
import matplotlib.pyplot as plt
from assembly import RoofAssem, WallAssem, FloorAssem, CeilingAssem
from bldg_code import BldgCode
from survey_data import SurveyData

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

    def location_data(self, BIM):
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
        code_informed = BldgCode(self)
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
            jFile = 'C:/Users/Karen/Desktop/BayCounty.geojson'
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
                parcel.footprint["geometry"] = poly
                parcel.footprint["type"] = 'open data'
                #print('Found building footprint')
                #print(poly)
                # If we do find the building footprint, I would like to print it for verification:
                #x, y = poly.exterior.xy
                #plt.plot(x, y)
                #plt.show()
            else:
                pass

        # Assign a regular footprint to any buildings without an open data footprint:
        if parcel.footprint['type'] == 'open data':
            pass
        else:
            parcel.footprint['type'] = 'default'
            length = sin(pi/4)*(sqrt(self.area/self.num_stories))/2 # Divide total building area by number of stories and take square root, divide by 2
            earth_radius = 6371 * 1000  # in meters
            brng1 = 0
            brng2 = 45*pi/180
            new_lat = asin(sin(parcel.lat*pi/180)*cos(length/earth_radius)+cos(parcel.lat*pi/180)*sin(length/earth_radius)*cos(brng2))
            new_lon = parcel.lon*pi/180 + atan2(sin(brng2)*sin(length/earth_radius)*cos(parcel.lat*pi/180), cos(length/earth_radius)-sin(parcel.lat*pi/180)*sin(new_lat))
            new_lat = degrees(new_lat)
            new_lon = degrees(new_lon)
            parcel.footprint['geometry'] = Polygon([(parcel.lon + new_lon, parcel.lat + new_lat), (parcel.lon + new_lon, parcel.lat - new_lat), (parcel.lon - new_lon, parcel.lat - new_lat), (parcel.lon - new_lon, parcel.lat + new_lat)])
            x,y = parcel.footprint['geometry'].exterior.xy
            plt.plot(x,y)
            plt.show()
            a = 0

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