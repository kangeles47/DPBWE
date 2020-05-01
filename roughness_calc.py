from shapely.geometry import Point, Polygon
import geopandas as gpd
import numpy as np
import matplotlib.pyplot as plt
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
        x1,y1 = parcel.footprint['geometry'].exterior.xy
        # (2) Define a bounding box for a given fetch length and wind direction:
        if wind_direction == 0:
            fetch = 0.001
            # Define points for site area Polygon object (starting with a rectangle here):
            p1 = Point(originz.x, originz.y+fetch)
            p2 = Point(originz.x, originz.y-fetch)
            p3 = Point(originz.x-fetch, originz.y-fetch)
            p4 = Point(originz.x-fetch, originz.y+fetch)
            # Create Polygon object:
            site_poly = Polygon([p1, p2, p3, p4])
            x,y = site_poly.exterior.xy
            plt.plot(x, y, x1, y1)
            plt.show()
        elif wind_direction == 90:
            pass

        # (3) Identify all footprints within the bounding box:
        # Create an empty list to store footprints:
        fetch_bldg = []
        for row in range(0, len(data["geometry"])):
            # Use building footprint centroid for point of reference:
            bldg_centroid = data['geometry'][row].centroid
            # Check if building footprint is within the site area polygon:
            if bldg_centroid.within(site_poly):
                fetch_bldg.append(data['geometry'][row])
            else:
                pass

        return originz


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