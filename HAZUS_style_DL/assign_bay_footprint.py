import geopandas as gpd
import numpy as np
import pandas as pd
from shapely.geometry import Point
from scipy import spatial
from math import sqrt, sin, pi
from geopy import distance


def assign_bay_footprint(lon, lat, plan_area):
    # Access file with region's building footprint information:
    jFile = 'D:/Users/Karen/Documents/GitHub/DPBWE/Datasets/Geojson/MexicoBeachFL.geojson'
    data = gpd.read_file(jFile)
    # data is a DataFrame object with column label = ['geometry'] and indexes = [0: end]
    # Accessing a specific Polygon object then requires: data['geometry'][index]

    # Need to access Polygon geometry in order to determine if the parcel's location is within that polygon:
    # Create a Point object with the parcel's lon, lat coordinates:
    ref_pt = Point(lon, lat)

    # Set up data holder:
    geom_dict = {"geometry": {"coordinates": [], "type": "Polygon"}, "properties": {}, "type": "Feature"}
    coord_list = []
    # Loop through dataset to find the parcel's corresponding footprint:
    for row in range(0, len(data['geometry'])):
        # Check if point is within the polygon in this row:
        poly = data['geometry'][row]
        if ref_pt.within(poly) or ref_pt.intersects(poly):
            footprint = poly
            xf, yf = footprint.exterior.xy
            for i in range(0, len(xf)):
                new_cpair = [xf[i], yf[i]]
                coord_list.append(new_cpair)
            geom_dict["geometry"]["coordinates"].append(coord_list)
            break
        else:
            pass
    # If the lon, lat of the parcel does not fall within bounds of any of the footprints, assign nearest neighbor:
    if len(coord_list) == 0:
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
            nneighbor_footprint = data['geometry'][neigh_list[1][0]]
            xn, yn = nneighbor_footprint.exterior.xy
            for i in range(0, len(xn)):
                new_cpair = [xn[i], yn[i]]
                coord_list.append(new_cpair)
            geom_dict["geometry"]["coordinates"].append(coord_list)
        else:
            # Create proxy footprint:
            length = (sqrt(plan_area)) * (1 / (2 * sin(
                pi / 4)))  # Divide total building area by number of stories and take square root, divide by 2
            p1 = distance.distance(miles=length / 5280).destination((ref_pt.y, ref_pt.x), 45)
            p2 = distance.distance(miles=length / 5280).destination((ref_pt.y, ref_pt.x), 135)
            p3 = distance.distance(miles=length / 5280).destination((ref_pt.y, ref_pt.x), 225)
            p4 = distance.distance(miles=length / 5280).destination((ref_pt.y, ref_pt.x), 315)
            coord_list = [[p1.longitude, p1.latitude], [p2.longitude, p2.latitude], [p3.longitude, p3.latitude],
                 [p4.longitude, p4.latitude]]
            geom_dict["geometry"]["coordinates"].append(coord_list)
            # In the future, might be able to do a match by considering the height of the parcel and it's area
    else:
        pass

    return geom_dict


# df = pd.read_csv('D:/Users/Karen/Documents/GitHub/DPBWE/HAZUS_style_DL/MB_Building_inventory.csv')
# glist = []
# for i in df.index.to_list():
#     gi = assign_bay_footprint(df['Longitude'][i], df['Latitude'][i], df['PlanArea'][i])
#     glist.append(gi)