from shapely.geometry import Point, Polygon
import geopandas as gpd
import pandas as pd
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
        xp,yp = parcel.footprint['geometry'].exterior.xy
        # (2) Define a bounding box for a given fetch length and wind direction:
        if wind_direction == 0:
            fetch = 0.007
            # Define points for site area Polygon object (starting with a rectangle here):
            p1 = Point(originz.x, originz.y+fetch)
            p2 = Point(originz.x, originz.y-fetch)
            p3 = Point(originz.x-fetch, originz.y-fetch)
            p4 = Point(originz.x-fetch, originz.y+fetch)
            # Create Polygon object:
            site_poly = Polygon([p1, p2, p3, p4])
            x1,y1 = site_poly.exterior.xy
            plt.plot(x1, y1, xp, yp)
            #plt.show()
        elif wind_direction == 90:
            pass

        # (3) Identify all buildings within the bounding box:
        # Read in parcel data:
        parcel_data = pd.read_csv('C:/Users/Karen/PycharmProjects/DPBWE/Datasets/Parcels/CedarsCrossing.csv')
        # Create an empty list to store identified parcels:
        fetch_bldgs = []
        # Create point objects for each parcel using its longitude and latitude and check if point is within bounding box:
        for row in range(0, len(parcel_data)):
            bldg_point = Point(parcel_data['Longitude'][row], parcel_data['Latitude'][row])
            if bldg_point.within(site_poly):
                # If the building is in the bounding box, create a Parcel Instance:
                pid = parcel_data['Parcel ID'][row] # Alternatively could use parcel_data.loc[row][1], but let's not assume data is in a specific order
                num_stories = parcel_data['Stories'][row]
                occupancy = parcel_data['Use Code'][row]
                yr_built = parcel_data['Year Built'][row]
                address = parcel_data['Address'][row]
                sq_ft = parcel_data['Square Footage'][row]
                lon = parcel_data['Longitude'][row]
                lat = parcel_data['Latitude'][row]
                new_parcel = Parcel(pid, num_stories, occupancy, yr_built, address, sq_ft, lon, lat)
                fetch_bldgs.append(new_parcel)
            else:
                pass


        # (3) Identify all footprints within the bounding box:
        # Create an empty list to store footprints:
        #fetch_bldg = []
        #for row in range(0, len(data["geometry"])):
            # Use building footprint centroid for point of reference:
            #bldg_centroid = data['geometry'][row].centroid
            # Check if building footprint is within the site area polygon:
            #if bldg_centroid.within(site_poly):
                #fetch_bldg.append(data['geometry'][row])
                #xnew,ynew = data['geometry'][row].exterior.xy
                #plt.plot(xnew, ynew)
            #else:
                #pass
        plt.show()

        # (4) Buildings within bounding box: interested in their 1) height and 2) surface area
        # Create an empty DataFrame to hold all values:
        z_params = pd.DataFrame(columns=['Building Height', 'Surface Area'])

        for bldg in fetch_bldgs:
            # Given wind direction, calculate surface area as follows:
            # Create equivalent rectangle using building footprint coordinates and multiply by building height
            if wind_direction == 0 or 90 or 180 or 270:
                x2, y2 = bldg.footprint["geometry"].exterior.xy
                rect = Polygon([(max(x2), max(y2)), (max(x2), min(y2)), (min(x2), min(y2), min(x2), max(y2))])
                if wind_direction == 0 or 90:
                    surfA_parcel = parcel.h_bldg*(max(y2)-min(y2))
                else:
                    surfA_parcel = parcel.h_bldg*(max(x2)-min(x2))
            # Add new row to empty DataFrame:
            z_params = z_params.append({'Building Height': parcel.h_bldg, 'Surface Area': surfA_parcel}, ignore_index=True)

        # Calculate the average height of all parcels within the specified fetch length:
        h_avg = z_params["Building Height"].mean()


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