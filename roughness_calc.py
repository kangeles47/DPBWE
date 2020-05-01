from shapely.geometry import Point, Polygon
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
        self.location = parcel.location
        self.terrain = self.roughness_calc(parcel, footprints, wind_direction)


    def roughness_calc(self, parcel, footprints, wind_direction):
        # (1) Find the parcel's centroid - this will be the origin for the z0 calculation:
        originz = parcel.footprint['geometry'].centroid # Parcel footprint is a Polygon type
        # (2) Define a bounding box for a fetch length and wind direction:
        if wind_direction == 0:
            # Define points for the Polygon (starting with a rectangle here):
            p1 = Point(originz)
        elif wind_direction == 90:
            p1 = Point(originz)
        return originz


# Identify the parcel:
test = Parcel('12345', 4, 'Financial', 1989, '1002 23RD ST W PANAMA CITY 32405', 41134)
# Create an instance of the site class:
wind_direction = 0

site = Site(test, footprints, wind_direction)