import geopandas as gpd
from shapely.geometry import Point, Polygon
import matplotlib.pyplot as plt

jFile = 'C:/Users/Karen/Desktop/BayCounty.geojson'
data = gpd.read_file(jFile)

# data is a DataFrame object with column label = ['geometry'] and indexes = [0: end]
# Accessing a specific Polygon object then requires: data['geometry'][index]

# Need to access Polygon geometry in order to determine if the parcel's location is within that polygon:
# Set up a lat, lon coordinates for our parcel (assume it was given to us):
lon = -85.676188
lat = 30.190142

# Create a Point object with these coordinates:
p1 = Point(lon, lat)

# Loop through dataset to find the parcel's corresponding footprint:
for row in range(0, len(data["geometry"])):
    # Check if point is within the polygon in this row:
    poly = data['geometry'][row]
    if p1.within(poly):
        footprint = poly
        print('Found building footprint')
        print(poly)
        # If we do find the building footprint, I would like to print it for verification:
        #x,y = poly.exterior.xy
        #plt.plot(x,y)
        #plt.show()
    else:
        pass

