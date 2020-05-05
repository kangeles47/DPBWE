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

    def __init__(self, parcel, footprints, wind_direction):
        self.location = Point(parcel.lon, parcel.lat)
        self.terrain = self.roughness_calc(parcel, footprints, wind_direction)


    def roughness_calc(self, parcel, footprints, wind_direction):
        # (1) Find the parcel's centroid - this will be the origin for the z0 calculation:
        originz = parcel.footprint['geometry'].centroid # Parcel footprint is a Polygon type
        xp,yp = parcel.footprint['geometry'].exterior.xy
        # (2) Define a bounding box for a given fetch length and wind direction:
        fetch = 0.007
        # Create circle with radius = fetch length:
        circ = originz.buffer(fetch, resolution=200)
        # Create half-circle corresponding to the given wind direction:
        if wind_direction == 0 or wind_direction == 180:
            # Define boundary line:
            bline = LineString([(originz.x, originz.y + fetch), (originz.x, originz.y - fetch)])
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
            bline = LineString([(originz.x-fetch, originz.y), (originz.x+fetch, originz.y)])
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
            bline = LineString([(originz.x-fetch*math.cos(rad), originz.y+fetch*math.sin(rad)), (originz.x+fetch*math.cos(rad), originz.y-fetch*math.sin(rad))])
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

        # Create polygon object with the selected points:
        #site_geom = Polygon(bounds)
        xsite, ysite = bounds.exterior.xy
        plt.plot(xp, yp, xsite, ysite)
        #plt.show()

        # (3) Identify all buildings within the bounding box:
        # Read in parcel data:
        # 'C:/Users/Karen/PycharmProjects/DPBWE/Datasets/Parcels/CedarsCrossing.csv'
        parcel_data = pd.read_csv('C:/Users/Karen/Desktop/CedarsCrossing.csv')
        # Create an empty list to store identified buildings:
        fetch_bldgs = []
        # Create point objects for each building using longitude and latitude and check if point is within bounding box:
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
        # Now that we've identified all parcels, plot for confirmation:
        plt.show()

        # (4) Buildings within bounding box: interested in their 1) height and 2) surface area
        # Create an empty DataFrame to hold all values:
        z_params = pd.DataFrame(columns=['Building Height', 'Surface Area'])

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
                surf_area = parcel.h_bldg*(max(ybldg)-min(ybldg))
            elif wind_direction == 90 or wind_direction == 270:
                surf_area = parcel.h_bldg*(max(xbldg)-min(xbldg))
            elif wind_direction == 45 or wind_direction == 135 or wind_direction == 225 or wind_direction == 315:
                surf_area = parcel.h_bldg * ((max(xbldg) - min(xbldg)) + (max(ybldg)-min(ybldg)))
            # Add new row to empty DataFrame:
            z_params = z_params.append({'Building Height': parcel.h_bldg, 'Surface Area': surf_area}, ignore_index=True)

        # Calculate the average height of all buildings within the fetch length:
        h_avg = z_params['Building Height'].mean()
        # Calculate the total surface area for all buildings within the fetch length:
        total_surf = sum(z_params['Surface Area'])
        # Calculate the roughness length:
        z0 = 0.5*h_avg*total_surf/bounds.area()


# Identify the parcel:
lon = -85.676188
lat = 30.190142
test = Parcel('12345', 4, 'Financial', 1989, '1002 23RD ST W PANAMA CITY 32405', 41134, lon, lat)
# Create an instance of the site class:
wind_direction = 0
jFile = 'C:/Users/Karen/Desktop/BayCounty.geojson'
data = gpd.read_file(jFile)
# data is a DataFrame object with column label = ['geometry'] and indexes = [0: end]
# Accessing a specific Polygon object then requires: data['geometry'][index]

site = Site(test, data, wind_direction)