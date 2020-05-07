from shapely.geometry import LineString, Point, Polygon
import geopandas as gpd
import pandas as pd
import numpy as np
import math
import matplotlib.pyplot as plt
from shapely.ops import split

from BIM import Parcel

class Wind:

    def __init__(self, intensity, direction):
        self.intensity = intensity #The intensity would probably need to be defined according to the type of assessment being run, the location (Call to ASCE API?)
        self.direction = direction #This would need to be user-specified
        # Given the wind speed and direction, need to identify the surrounding terrain:


class Site:

    def __init__(self, parcel, wind_direction):
        self.location = Point(parcel.lon, parcel.lat)
        # Read in parcel data:
        # 'C:/Users/Karen/PycharmProjects/DPBWE/Datasets/Parcels/CedarsCrossing.csv'
        parcel_data = pd.read_csv('C:/Users/Karen/Desktop/CedarsCrossing.csv')
        self.terrain = self.roughness_calc(parcel, wind_direction)


    def roughness_calc(self, parcel, wind_direction):
        # This function calculates a data-driven surface roughness and the corresponding fetch length:
        # (1) Find the parcel's centroid - this will be the origin for the z0 calculation:
        originz = parcel.footprint['geometry'].centroid  # Parcel footprint is a Polygon type
        xp,yp = parcel.footprint['geometry'].exterior.xy
        # (2) Create an array of fetch lengths:
        fetch = np.arange(0, 1, 0.001)  # degrees latitude/longitude
        # (3) Create an empty DataFrame to hold values of wind speed, roughness length, and fetch length:
        terrain_params = pd.DataFrame(columns=['Roughness Length', 'Fetch Length', 'Local Wind Speed'])
        # (4) For each fetch length and the given wind direction, find the roughness length:
        for f in fetch:
            # (5) Create circle with radius = fetch length:
            circ = originz.buffer(f, resolution=200)
            # (6) Create half-circle corresponding to the given wind direction (bounds):
            if wind_direction == 0 or wind_direction == 180:
                # Define boundary line:
                bline = LineString([(originz.x, originz.y + f), (originz.x, originz.y - f)])
                # Split the circle into two polygons
                circ_split = split(circ, bline)
                # Choose the first polygon to do a check and assign bounds for the wind direction:
                x1, y1 = circ_split[0].exterior.xy
                if wind_direction == 0:
                    # For 0 degrees, minimum longitude (x) in the Polygon we want should be smaller than bldg centroid x
                    if min(x1) < originz.x:
                        bounds = circ_split[0]
                    else:
                        bounds = circ_split[1]
                elif wind_direction == 180:
                    # For 180 degrees, max longitude (x) in the Polygon we want should be larger than bldg centroid x
                    if max(x1) > originz.x:
                        bounds = circ_split[0]
                    else:
                        bounds = circ_split[1]
            elif wind_direction == 90 or wind_direction == 270:
                print(wind_direction)
                # Define boundary line:
                bline = LineString([(originz.x-f, originz.y), (originz.x+f, originz.y)])
                # Split the circle into two polygons
                circ_split = split(circ, bline)
                # Choose the first polygon to do a check and assign bounds for the wind direction:
                x1, y1 = circ_split[0].exterior.xy
                if wind_direction == 90:
                    # For 90 degrees, minimum latitude (y) in the Polygon we want should be smaller than bldg centroid y
                    if min(y1) < originz.y:
                        bounds = circ_split[0]
                    else:
                        bounds = circ_split[1]
                elif wind_direction == 270:
                    # For 270 degrees, max latitude (y) in the Polygon we want should be larger than bldg centroid y
                    if max(y1) > originz.y:
                        bounds = circ_split[0]
                    else:
                        bounds = circ_split[1]
            elif wind_direction == 45 or wind_direction == 225:
                # Define boundary line:
                rad = math.pi*(1/4)
                bline = LineString([(originz.x-f*math.cos(rad), originz.y+f*math.sin(rad)), (originz.x+f*math.cos(rad), originz.y-f*math.sin(rad))])
                # Split the circle into two polygons
                circ_split = split(circ, bline)
                print(len(circ_split))
                # Choose the first polygon to do a check and assign bounds for the wind direction:
                x1, y1 = circ_split[0].exterior.xy
                if wind_direction == 45:
                    # For 45 degrees, use point in upper left-hand quadrant:
                    # Polygon we want will have a minimum longitude that is smaller than the longitude for this point
                    if min(x1) < originz.x-fetch*math.cos(rad):
                        bounds = circ_split[0]
                    else:
                        bounds = circ_split[1]
                elif wind_direction == 225:
                    # For 225 degrees, use point in lower right-hand quadrant:
                    # Polygon we want will have a maximum longitude that is larger than the longitude for this point
                    if max(x1) > originz.x+fetch*math.cos(rad):
                        bounds = circ_split[0]
                    else:
                        bounds = circ_split[1]
            elif wind_direction == 135 or 315:
                # Define boundary line:
                rad = math.pi*(1/4)
                bline = LineString([(originz.x+fetch*math.cos(rad), originz.y+fetch*math.sin(rad)), (originz.x-fetch*math.cos(rad), originz.y-fetch*math.sin(rad))])
                # Split the circle into two polygons
                circ_split = split(circ, bline)
                # Choose the first polygon to do a check and assign bounds for the wind direction:
                x1, y1 = circ_split[0].exterior.xy
                if wind_direction == 135:
                    # For 135 degrees, use point in upper right-hand quadrant:
                    # Polygon we want will have a maximum longitude that is larger than the longitude for this point
                    if max(x1) > originz.x+fetch*math.cos(rad):
                        bounds = circ_split[0]
                    else:
                        bounds = circ_split[1]
                elif wind_direction == 315:
                    # For 315 degrees, use point in lower left-hand quadrant:
                    # Polygon we want will have a minimum longitude that is smaller than the longitude for this point
                    if min(x1) < originz.x-fetch*math.cos(rad):
                        bounds = circ_split[0]
                    else:
                        bounds = circ_split[1]

            # Plot the site bounds
            xsite, ysite = bounds.exterior.xy
            plt.plot(xp, yp, xsite, ysite)
            #plt.show()

            # (6) Identify all buildings within the bounding geometry:
            # Read in parcel data:
            # 'C:/Users/Karen/PycharmProjects/DPBWE/Datasets/Parcels/CedarsCrossing.csv'
            parcel_data = pd.read_csv('C:/Users/Karen/Desktop/CedarsCrossing.csv')
            # Create an empty list to store identified buildings:
            fetch_bldgs = []
            # Create point objects for each building (longitude, latitude) & check if point is within bounding geometry:
            for row in range(0, len(parcel_data)):
                bldg_point = Point(parcel_data['Longitude'][row], parcel_data['Latitude'][row])
                if bldg_point.within(bounds):
                    # If the building is in the bounding box, create a Parcel Instance:
                    pid = parcel_data['Parcel ID'][row]
                    num_stories = parcel_data['Stories'][row]
                    occupancy = parcel_data['Use Code'][row]
                    yr_built = parcel_data['Year Built'][row]
                    address = parcel_data['Address'][row]
                    sq_ft = parcel_data['Square Footage'][row]
                    lon = parcel_data['Longitude'][row]
                    lat = parcel_data['Latitude'][row]
                    new_parcel = Parcel(pid, num_stories, occupancy, yr_built, address, sq_ft, lon, lat)
                    fetch_bldgs.append(new_parcel)
                    xparcel,yparcel = new_parcel.footprint["geometry"].exterior.xy
                    plt.plot(xparcel, yparcel)
                else:
                    pass
            # Check to see if we have any buildings:
            if len(fetch_bldgs) == 0:
                tol = 1.0  # Provide a default value for tolerance and move on to the next fetch length
            else:
                # Now that we've identified all parcels, plot for confirmation:
                plt.show()

                # (7) Buildings within bounding geometry: interested in their 1) height and 2) surface area
                # Create an empty DataFrame to hold all values:
                z_params = pd.DataFrame(columns=['Building Height', 'Surface Area'])
                # Loop through the buildings:
                for bldg in fetch_bldgs:
                    # Given wind direction, calculate surface area as follows:
                    # Create equivalent rectangle using building footprint coordinates and multiply by building height
                    # Check if an equivalent rectangle is needed:
                    xbldg,ybldg = bldg.footprint["geometry"].exterior.xy
                    if len(xbldg) != 4:
                        # Create equivalent rectangle:
                        rect = Polygon([(max(xbldg), max(ybldg)), (max(xbldg), min(ybldg)), (min(xbldg), min(ybldg), min(xbldg), max(ybldg))])
                        xbldg,ybldg = rect.exterior.xy
                    else:
                        pass
                    # Calculate the surface area for each obstruction (building):
                    if wind_direction == 0 or wind_direction == 180:
                        # For these wind directions, we want the side parallel to the longitude:
                        xd = xbldg(ybldg == max(ybldg))
                        d = Site.distance(self, xd, max(ybldg), xd, min(ybldg))
                        surf_area = parcel.h_bldg*d
                    elif wind_direction == 90 or wind_direction == 270:
                        # For these wind directions, we want the side parallel to the latitude:
                        yd = ybldg(xbldg == max(xbldg))
                        d = Site.distance(self, max(xbldg), yd, min(ybldg), yd)
                        surf_area = parcel.h_bldg*d
                    elif wind_direction == 45 or wind_direction == 135 or wind_direction == 225 or wind_direction == 315:
                        # For these wind directions, we want both sides of the rectangle:
                        xd = xbldg(ybldg == max(ybldg))
                        d1 = Site.distance(self, xd, max(ybldg), xd, min(ybldg))
                        yd = ybldg(xbldg == max(xbldg))
                        d2 = Site.distance(self, max(xbldg), yd, min(ybldg), yd)
                        surf_area = parcel.h_bldg * (d1+d2)
                    # Add new row to empty DataFrame:
                    z_params = z_params.append({'Building Height': parcel.h_bldg, 'Surface Area': surf_area}, ignore_index=True)

                # Calculate the average height of all buildings within the fetch length:
                h_avg = z_params['Building Height'].mean()
                # Calculate the total surface area for all buildings within the fetch length:
                total_surf = sum(z_params['Surface Area'])
                # Calculate the roughness length:
                z0 = 0.5*h_avg*total_surf/bounds.area()
                # Calculate the wind speed:
                vnew = Site.calc_windspeed(self, parcel.h_bldg, z0)
                # Calculate the meters distance of the fetch length:
                fdist = Site.distance(self, originz.x, originz.y, originz.x+f, originz.y)
                # Populate the DataFrame with the values for this fetch length:
                terrain_params = terrain_params.append({'Roughness Length': z0, 'Fetch Length': fdist, 'Local Wind Speed': vnew}, ignore_index=True)
                # Check the difference in the wind speed:
                if len(terrain_params['Roughness Length']) == 1:
                    pass  # pass if we only have one roughness length value
                else:
                    row = np.where(fetch == f)[0][0]
                    tol = (terrain_params['Local Wind Speed'][row] - terrain_params['Local Wind Speed'][row-1])/terrain_params['Local Wind Speed'][row]
                    print(tol)
        # Break the loop if the new fetch length provides us with the right tolerance value:
            if tol < 0.4:
                break
            else:
                pass

    def distance(self, lon1, lat1, lon2, lat2):
        # Calculate distance between two longitude, latitude points using the Haversine formula:
        earth_radius = 6371*1000  # in meters
        # Calculate differences between longitudes, latitudes (convert from decimal degrees to radians):
        dlat = math.radians(lat2) - math.radians(lat1)
        dlon = math.radians(lon2) - math.radians(lon1)

        sin_lat = math.sin(dlat / 2)
        sin_lon = math.sin(dlon / 2)

        a = (sin_lat * sin_lat) + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * (sin_lon * sin_lon)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        dist = round(earth_radius*c, 2)

        return dist


    def calc_windspeed(self, hnew, znew, vref=80.0, href=10.0, zref=0.03):
        # Note: Default reference parameters correspond to 10 meter height in open terrain
        # Calculate the shear (friction) velocity for open terrain:
        shear_ref = vref/(2.5*math.log(href/zref))
        # Shear conversion model:
        shear_ratio = (znew/zref)**0.0706
        # Calculate shear velocity for new terrain (may or may not be applicable):
        shear_new = shear_ref*shear_ratio
        # Calculate the zero-plane displacement:
        #k = 0.4 # from the log law
        #zd = h_avg - znew/k
        # Calculate new wind speed (log law for now) for different terrain and/or height:
        vnew = 2.5*shear_new*math.log(hnew/znew)
        # Need gradient heights for the given location --> can get these from wind measurement stations?
        # Power law:

        #vnew = ((hnew/znew)**alpha_new)*((href/zref)**alpha_ref)*vref
        #vratio = vnew/vref
        return vnew



# Identify the parcel:
lon = -85.62010796
lat = 30.1802
test = Parcel('14805-139-000', 1, 'SINGLE FAM', 2011, '2912 PATRICIA ANN LN PANAMA CITY 32405', 2555, lon, lat)
# Create an instance of the site class:
wind_direction = 0

# data is a DataFrame object with column label = ['geometry'] and indexes = [0: end]
# Accessing a specific Polygon object then requires: data['geometry'][index]

site = Site(test, wind_direction)
test = site.calc_windspeed(21, 0.78, 11.7, 10, 0.08)
print(test)

# Recreating plot from HAZUS-HM
heights = np.array([3, 5, 10, 20, 50, 100])
zs = np.linspace(0.001,1,1000)
for h in heights:
    lst = []
    for z in zs:
        ratio = site.calc_windspeed(h, z, 80, href=h)
        lst.append(ratio)
    plt.loglog(zs, lst)

plt.grid(True)
plt.show()