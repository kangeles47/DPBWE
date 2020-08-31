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
from code_capacities import get_cc_zone_width, find_cc_zone_points

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
        if isinstance(self, Site):
            for bldg in self.hasBuilding:
                for k, v in bldg.containsElement:
                    self.hasElement.append(v)
        elif isinstance(self, Building):
            if len(self.hasElement) == len(self.hasStorey):  # NOTE: is there a better way to check if the building has already been updated with all storey elements? This won't work
                print('Elements in this building are already up to date')
            else:
                for storey in self.hasStorey:
                    self.hasElement.append(storey.hasElement)
        elif isinstance(self, Storey):
            self.hasElement.append(list(self.containsElement.values()))

    def update_interfaces(self):
        # Simple function to easily update hasElement assignment
        if isinstance(self, Site):
            for bldg in self.hasBuilding:
                for interface in bldg.hasInterface:
                    self.hasInterface.append(interface)
        elif isinstance(self, Building):
            for storey in self.hasStorey:
                self.hasInterface.append(storey.hasInterface)
        elif isinstance(self, Storey):
            # This one should be according to the identified spaces (if applicable)
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
            new_bldg = Building(pid, num_stories, occupancy, yr_built, address, area, lon, lat) # These attributes come from building list
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
        self.hasInterface = []


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
        # Buildings contain all of the zones, spaces, elements, etc. within each storey:
        self.update_zones()
        self.update_elements()
        #self.update_interfaces()
        # Attributes outside of BOT:
        self.hasName = pid
        self.hasOccupancy = occupancy
        self.hasYearBuilt = int(yr_built)
        self.hasLocation = {'Address': address, 'State': None, 'County': None, 'Geodesic': Point(lon, lat)}
        self.hasArea = float(area) # sq feet
        self.hasHeight = None  # every building has a height, fidelity will determine value
        self.hasFootprint = {'type': None, 'geodesic_geometry': None, 'local_geometry': None}
        self.hasZeroPoint = Point(lon, lat)
        self.hasGeometry = {'3D Geometry': {'geodesic_geometry': None, 'local_geometry': None}, 'Surfaces': None}
        self.hasOrientation = None
        self.hasFundamentalPeriod = {'x': None, 'y': None}
        self.hasStructuralSystem = {'type': None, 'elements': []}
        self.hasImportanceFactor = None
        self.hasRiskCategory = None
        self.hasEffectiveSeismicWeight = None
        self.hasDampingValue = None
        self.hasServiceLife = None
        self.hasInterface = []
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


class Parcel(Building):  # Note here: Consider how story/floor assignments may need to change for elevated structures

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
        # Now that we have the building and story heights, render the 3D geometries:
        # Extract points for the building footprint and add the base z coordinate:
        gxs, gys = self.hasFootprint['geodesic_geometry'].exterior.xy
        lxs, lys = self.hasFootprint['local_geometry'].exterior.xy
        new_gzpts = []  # Hold geodesic coords
        new_lzpts = []  # Hold local coords
        base_z = 0
        # Create z coordinates for each story:
        for story_num in range(0, len(self.hasStorey)):
            gzs = []  # Hold geodesic coords
            lzs = []  # Hold local coords
            for pt in range(0, len(gxs)):
                if self.hasStorey[story_num].hasElevation[0] == base_z:  # First story exception
                    # Define z-coordinates for bottom floor:
                    gzs.append(Point(gxs[pt], gys[pt], base_z))
                    lzs.append(Point(lxs[pt], lys[pt], base_z))
                    # Define z-coordinates for top floor:
                    gzs.append(Point(gxs[pt], gys[pt], self.hasStorey[story_num].hasElevation[-1]))
                    lzs.append(Point(lxs[pt], lys[pt], self.hasStorey[story_num].hasElevation[-1]))
                else:
                    gzs.append(Point(gxs[pt], gys[pt], self.hasStorey[story_num].hasElevation[-1]))
                    lzs.append(Point(lxs[pt], lys[pt], self.hasStorey[story_num].hasElevation[-1]))
            # Save lists of 3D geodesic and local coordinates:
            new_gzpts.append(gzs)
            new_lzpts.append(lzs)
        # With new 3D coordinates for each horizontal plane, create surface geometry:
        for plane in range(0, len(new_gzpts)):
            for zpt in range(0, len(new_gzpts[plane])):
                # Create the surface lines:
                vert_line1 = LineString([new_gzpts[plane][zpt], new_gzpts[plane+1][zpt]])
                vert_line2 = LineString([new_gzpts[plane+1][zpt+1], new_gzpts[plane][zpt+1]])
                horiz_line1 = LineString([new_gzpts[plane+1][zpt], new_gzpts[plane+1][zpt+1]])
                horiz_line2 = LineString([new_gzpts[plane][zpt+1], new_gzpts[plane][zpt]])
                # Define a new polygon:
                zpoly = Polygon([vert_line1, horiz_line1, vert_line2, horiz_line2])
                # Plot the polygon:
                coord_list = Polygon.exterior.coords

        for storey in self.hasStorey:
            self.hasGeometry['3D Geometry']['geodesic_geometry'] = None
            self.hasGeometry['3D Geometry']['local_geometry'] = None
        # Generate a set of building elements (with default attributes) for the parcel:
        self.parcel_elements(self)
        # Populate instance attributes informed by national survey data:
        survey_data = SurveyData()  # create an instance of the survey data class
        survey_data.run(self)  # populate the component-level attributes using survey data
        if survey_data.isSurvey == 'CBECS':
            # Populate code-informed component-level information
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
                parcel.hasFootprint['geodesic_geometry'] = poly
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
                parcel.hasFootprint['geodesic_geometry'] = data['geometry'][neigh_list[1][0]]
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
            parcel.hasFootprint['geodesic_geometry'] = Polygon([(p1.longitude, p1.latitude), (p2.longitude, p2.latitude), (p3.longitude, p3.latitude), (p4.longitude, p4.latitude)])
        # Given the geodesic footprint, calculate the local (x,y) coordinates for the building footprint:
        # Find the distance between exterior points and the building centroid (origin) to define a new coordinate system:
        xs, ys = parcel.hasFootprint['geodesic_geometry'].exterior.xy
        origin = parcel.hasFootprint['geodesic_geometry'].centroid
        point_list = []
        yc = []
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
        parcel.hasFootprint['local_geometry'] = xy_poly


    def parcel_elements(self, parcel):
        # Generate parcel elements with (default) attributes:
        # Floor, Ceiling, and Roof Instances - These are conducted by storey to facilitate "hasElement" assignment
        # Exterior Walls - Geometries are derived considering zone locations on the building footprint:
        a = get_cc_zone_width(parcel)  # Determine the zone width
        zone_pts, int_poly = find_cc_zone_points(parcel, a, roof_flag=True, edition=None)  # Coordinates for start/end of zone locations
        # Assume that walls span one story for now:
        for storey in parcel.hasStorey:
            # Create an empty list to hold all elements:
            element_list = []
            # Generate floor and ceiling instance(s):
            new_floor_list = []
            new_floor1 = Floor()
            new_floor1.hasElevation = storey.hasElevation[0]
            new_floor_list.append(new_floor1)
            element_list.append(new_floor1)
            new_ceiling = Ceiling()
            if storey == parcel.hasStorey[-1]:
                new_roof = Roof()
                # Add roof to the storey:
                storey.containsElement.update({'Roof': new_roof})
                element_list.append(new_roof)
            else:
                new_floor2 = Floor()
                new_floor2.hasElevation = storey.hasElevation[1]
                new_floor_list.append(new_floor2)
                element_list.append(new_floor2)
            # Loop through zone_pts and assign geometries to wall elements:
            # Parcel models will have three "walls" by default, corresponding to each zone on a side of the building:
            new_wall_list = []
            for ind in zone_pts.index:
                for col in range(0, len(zone_pts.loc[ind])-1):
                    # Create a new Wall Instance:
                    ext_wall = Wall()
                    ext_wall.isExterior = True
                    ext_wall.hasHeight = storey.hasHeight
                    ext_wall.hasGeometry['1D Geometry'] = LineString([zone_pts.iloc[ind, col], zone_pts.iloc[ind, col+1]])  # Line segment with start/end coordinates of wall (respetive to building origin)
                    ext_wall.hasLength = ext_wall.hasGeometry['1D Geometry'].length
                    new_wall_list.append(ext_wall)
            # Each wall shares interfaces with the walls before and after it:
            for w in range(0, len(new_wall_list)-1):
                # Create new Interface instance
                new_interface = Interface(new_wall_list[w], new_wall_list[w+1])
                storey.hasInterface.append(new_interface)
            # Add all elements to the storey's "hasElement" attribute:
            storey.containsElement.update({'Floors': new_floor_list, 'Ceiling': new_ceiling, 'Walls': new_wall_list})
            # Populate relational attributes for elements in this storey:
            storey.adjacentElement.append(element_list)  # Note: Ceilings do not bound storey zones; they bound spaces
            # Update hasElement attribute for the storey:
            storey.update_elements()


class Storey(Zone):
    # Sub-class of Zone
    def __init__(self):
        # Populate zone properties:
        new_zone = self
        Zone.__init__(self, new_zone)
        # Attributes outside of BOT Ontology:
        self.hasName = None
        self.hasElevation = []
        self.hasHeight = None
        self.hasGeometry = {'3D Geometry': None, '2D Geometry': None}
        # Add a placeholder for Interface objects
        self.hasInterface = []


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
