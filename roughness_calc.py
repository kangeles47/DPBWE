import shapely.ops as ops
from shapely.geometry import MultiLineString, LineString, Point, Polygon
import pandas as pd
import numpy as np
import math
import matplotlib.pyplot as plt
import pyproj
from functools import partial
from geopy import distance

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
        #parcel_data = pd.read_csv('C:/Users/Karen/PycharmProjects/DPBWE/ResSub.csv')
        self.terrain = self.roughness_calc(parcel, wind_direction)


    def roughness_calc(self, parcel, wind_direction):
        # This function calculates a data-driven surface roughness and the corresponding fetch length:
        parcel_data = pd.read_csv('D:/Users/Karen/Documents/GitHub/DPBWE/Datasets/Parcels/CedarsCrossing.csv')
        # (1) Find the parcel's centroid - this will be the origin for the z0 calculation:
        originz = parcel.footprint['geometry'].centroid  # Parcel footprint is a Polygon type
        xp,yp = parcel.footprint['geometry'].exterior.xy
        # (2) Create an array of fetch lengths:
        fetch = np.arange(0.0005, 1, 0.0005)  # degrees latitude/longitude
        # (3) Create an empty DataFrame to hold values of wind speed, roughness length, and fetch length:
        terrain_params = pd.DataFrame(columns=['Roughness Length', 'Fetch Length', 'Local Wind Speed'])
        # (4) For each fetch length and the given wind direction, find the roughness length:
        # Create an empty DataFrame to store identified buildings:
        fetch_bldgs = pd.DataFrame(columns=['Building ID', 'BIM'])
        for f in fetch:
            sectors = Site.get_sector(self, originz, wind_direction, f)
            # (5) Create circle with radius = fetch length:
            circ = originz.buffer(f, resolution=200)
            # (6) Create half-circle corresponding to the given wind direction (boundary):
            if wind_direction == 0 or wind_direction == 180:
                # Define boundary line1:
                rad = math.pi * (1 / 4)
                bline1 = LineString([(originz.x - f * math.cos(rad), originz.y + f * math.sin(rad)),(originz.x + f * math.cos(rad), originz.y - f * math.sin(rad))])
                # Split the circle into two polygons
                circ_split = ops.split(circ, bline1)
                # Choose the first polygon to do a check and assign boundary for the wind direction:
                x1, y1 = circ_split[0].exterior.xy
                if wind_direction == 0:
                    # For 0 degrees, use point in upper right-hand quadrant:
                    # Polygon we want will have a maximum longitude that is greater than the longitude for this point
                    if max(x1) > originz.x + f * math.cos(rad):
                        half_circ = circ_split[0]
                    else:
                        half_circ = circ_split[1]
                    # Split the half-circle to get the sector we want:
                    bline2 = LineString([(originz.x - f * math.cos(rad), originz.y - f * math.sin(rad)),(originz.x + f * math.cos(rad), originz.y + f * math.sin(rad))])
                    circ_split2 = ops.split(half_circ, bline2)
                    # Choose the first polygon to do a check and assign boundary for the wind direction:
                    x2, y2 = circ_split2[0].exterior.xy
                    # Polygon we want will have a maximum latitude that is greater than the latitude in upper RH quadrant:
                    if max(y2) > originz.y + f * math.sin(rad):
                        boundary = circ_split2[0]
                    else:
                        boundary = circ_split2[1]
                elif wind_direction == 180:
                    # For 180 degrees, use point in lower left-hand quadrant:
                    # Polygon we want will have a minimum longitude that is smaller than the longitude for this point
                    if min(x1) < originz.x - f * math.cos(rad):
                        half_circ = circ_split[0]
                    else:
                        half_circ = circ_split[1]
                    # Split the half-circle to get the sector we want:
                    bline2 = LineString([(originz.x - f * math.cos(rad), originz.y - f * math.sin(rad)), (originz.x + f * math.cos(rad), originz.y + f * math.sin(rad))])
                    circ_split2 = ops.split(half_circ, bline2)
                    # Choose the first polygon to do a check and assign boundary for the wind direction:
                    x2, y2 = circ_split2[0].exterior.xy
                    # Polygon we want will have a minimum latitude that is smaller than the latitude in lower LH quadrant:
                    if min(y2) < originz.y - f * math.sin(rad):
                        boundary = circ_split2[0]
                    else:
                        boundary = circ_split2[1]
            elif wind_direction == 90 or wind_direction == 270:
                # Define boundary line1:
                rad = math.pi * (1 / 4)
                bline1 = LineString([(originz.x - f * math.cos(rad), originz.y - f * math.sin(rad)), (originz.x + f * math.cos(rad), originz.y + f * math.sin(rad))])
                # Split the circle into two polygons
                circ_split = ops.split(circ, bline1)
                # Choose the first polygon to do a check and assign boundary for the wind direction:
                x1, y1 = circ_split[0].exterior.xy
                if wind_direction == 90:
                    # For 90 degrees, use point in upper right-hand quadrant:
                    # Polygon we want will have a maximum longitude that is larger than the longitude for this point
                    if max(x1) > originz.x + f * math.cos(rad):
                        half_circ = circ_split[0]
                    else:
                        half_circ = circ_split[1]
                    # Split the half-circle to get the sector we want:
                    bline2 = LineString([(originz.x - f * math.cos(rad), originz.y + f * math.sin(rad)), (originz.x + f * math.cos(rad), originz.y - f * math.sin(rad))])
                    circ_split2 = ops.split(half_circ, bline2)
                    # Choose the first polygon to do a check and assign boundary for the wind direction:
                    x2, y2 = circ_split2[0].exterior.xy
                    # Polygon we want will have a maximum longitude that is greater than the longitude in upper RH quadrant:
                    if max(x1) > originz.x + f * math.cos(rad):
                        boundary = circ_split2[0]
                    else:
                        boundary = circ_split2[1]
                elif wind_direction == 270:
                    # For 270 degrees, use point in upper left-hand quadrant:
                    # Polygon we want will have a minimum longitude that is smaller than the longitude for this point
                    if min(x1) < originz.x - f * math.cos(rad):
                        half_circ = circ_split[0]
                    else:
                        half_circ = circ_split[1]
                    # Split the half-circle to get the sector we want:
                    bline2 = LineString([(originz.x - f * math.cos(rad), originz.y + f * math.sin(rad)), (originz.x + f * math.cos(rad), originz.y - f * math.sin(rad))])
                    circ_split2 = ops.split(half_circ, bline2)
                    # Choose the first polygon to do a check and assign boundary for the wind direction:
                    x2, y2 = circ_split2[0].exterior.xy
                    # Polygon we want will have a minimum longitude that is smaller than the longitude in upper LH quadrant:
                    if min(x2) < originz.x - f * math.cos(rad):
                        boundary = circ_split2[0]
                    else:
                        boundary = circ_split2[1]
            elif wind_direction == 45 or wind_direction == 225:
                # Define boundary line1:
                rad = math.pi * (1 / 4)
                bline1 = LineString([(originz.x, originz.y - f), (originz.x, originz.y + f)])
                # Split the circle into two polygons
                circ_split = ops.split(circ, bline1)
                # Choose the first polygon to do a check and assign boundary for the wind direction:
                x1, y1 = circ_split[0].exterior.xy
                if wind_direction == 45:
                    # For 45 degrees, use maximum longitude:
                    if max(x1) > originz.x:
                        half_circ = circ_split[0]
                    else:
                        half_circ = circ_split[1]
                    # Split the half-circle to get the sector we want:
                    bline2 = LineString([(originz.x - f, originz.y), (originz.x + f, originz.y)])
                    circ_split2 = ops.split(half_circ, bline2)
                    # Choose the first polygon to do a check and assign boundary for the wind direction:
                    x2, y2 = circ_split2[0].exterior.xy
                    # Use maximum latitude:
                    if max(y2) > originz.y:
                        boundary = circ_split2[0]
                    else:
                        boundary = circ_split2[1]
                elif wind_direction == 225:
                    # For 225 degrees, use minimum longitude:
                    if min(x1) < originz.x:
                        half_circ = circ_split[0]
                    else:
                        half_circ = circ_split[1]
                    # Split the half-circle to get the sector we want:
                    bline2 = LineString([(originz.x - f, originz.y), (originz.x + f, originz.y)])
                    circ_split2 = ops.split(half_circ, bline2)
                    # Choose the first polygon to do a check and assign boundary for the wind direction:
                    x2, y2 = circ_split2[0].exterior.xy
                    # Use minimum latitude:
                    if min(y2) < originz.y:
                        boundary = circ_split2[0]
                    else:
                        boundary = circ_split2[1]
            elif wind_direction == 135 or 315:
                # Define boundary line1:
                rad = math.pi * (1 / 4)
                bline1 = LineString([(originz.x, originz.y - f), (originz.x, originz.y + f)])
                # Split the circle into two polygons
                circ_split = ops.split(circ, bline1)
                # Choose the first polygon to do a check and assign boundary for the wind direction:
                x1, y1 = circ_split[0].exterior.xy
                if wind_direction == 135:
                    # For 135 degrees, use maximum longitude:
                    if max(x1) > originz.x:
                        half_circ = circ_split[0]
                    else:
                        half_circ = circ_split[1]
                    # Split the half-circle to get the sector we want:
                    bline2 = LineString([(originz.x - f, originz.y), (originz.x + f, originz.y)])
                    circ_split2 = ops.split(half_circ, bline2)
                    # Choose the first polygon to do a check and assign boundary for the wind direction:
                    x2, y2 = circ_split2[0].exterior.xy
                    # Use minimum latitude:
                    if min(y2) < originz.y:
                        boundary = circ_split2[0]
                    else:
                        boundary = circ_split2[1]
                elif wind_direction == 315:
                    # For 225 degrees, use minimum longitude:
                    if min(x1) < originz.x:
                        half_circ = circ_split[0]
                    else:
                        half_circ = circ_split[1]
                    # Split the half-circle to get the sector we want:
                    bline2 = LineString([(originz.x - f, originz.y), (originz.x + f, originz.y)])
                    circ_split2 = ops.split(half_circ, bline2)
                    # Choose the first polygon to do a check and assign boundary for the wind direction:
                    x2, y2 = circ_split2[0].exterior.xy
                    # Use maximum latitude:
                    if max(y2) < originz.y:
                        boundary = circ_split2[0]
                    else:
                        boundary = circ_split2[1]
            # Plot the site boundary
            xsite, ysite = boundary.exterior.xy
            #plt.plot(xp, yp, xsite, ysite)
            #plt.show()

            # (6) Identify all buildings within the bounding geometry:
            # Create point objects for each building (longitude, latitude) & check if point is within bounding geometry:
            for row in range(0, len(parcel_data)):
                bldg_point = Point(parcel_data['Longitude'][row], parcel_data['Latitude'][row])
                # Check if the building is within the specified boundary:
                if bldg_point.within(boundary):
                    # Check that a BIM has not yet been created for the building:
                    pid = parcel_data['Parcel ID'][row]
                    if pid in fetch_bldgs["Building ID"].values:
                        pass
                    else: # Populate the remaining fields to create a Parcel Instance:
                        num_stories = parcel_data['Stories'][row]
                        occupancy = parcel_data['Use Code'][row]
                        yr_built = parcel_data['Year Built'][row]
                        address = parcel_data['Address'][row]
                        sq_ft = parcel_data['Square Footage'][row]
                        lon = parcel_data['Longitude'][row]
                        lat = parcel_data['Latitude'][row]
                        new_parcel = Parcel(pid, num_stories, occupancy, yr_built, address, sq_ft, lon, lat)
                        fetch_bldgs = fetch_bldgs.append({'Building ID': pid, 'BIM': new_parcel}, ignore_index=True)
                        xparcel,yparcel = new_parcel.footprint["geometry"].exterior.xy
                        plt.plot(xparcel, yparcel)
                else:
                    pass
            # Check to see if we have any buildings:
            print('Number of buildings captured:', len(fetch_bldgs["BIM"]))
            if len(fetch_bldgs["BIM"]) == 0:
                # Calculate the meters distance of the fetch length:
                tol = 1.0  # Provide a default value for tolerance and move on to the next fetch length
            else:
                # (7) Buildings within bounding geometry: interested in their 1) height and 2) surface area
                # Create an empty DataFrame to hold all values:
                z_params = pd.DataFrame(columns=['Building Height', 'Surface Area'])
                # Loop through the buildings:
                for bldg in fetch_bldgs["BIM"]:
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
                    # Convert into coordinates into numpy arrays:
                    xbldg = np.array(xbldg)
                    ybldg = np.array(ybldg)
                    # Calculate the surface area for each obstruction (building):
                    if wind_direction == 0 or wind_direction == 180:
                        # For these wind directions, we want the side parallel to the latitude:
                        ind_x = np.where(xbldg == max(xbldg))[0][0]
                        yd = ybldg[ind_x]
                        d = Site.dist_calc(self, max(xbldg), yd, min(ybldg), yd)
                        surf_area = parcel.h_bldg * d
                    elif wind_direction == 90 or wind_direction == 270:
                        # For these wind directions, we want the side parallel to the longitude:
                        ind_y = np.where(ybldg == max(ybldg))[0][0]
                        xd = xbldg[ind_y]
                        d = Site.dist_calc(self, xd, max(ybldg), xd, min(ybldg))
                        surf_area = parcel.h_bldg * d
                    elif wind_direction == 45 or wind_direction == 135 or wind_direction == 225 or wind_direction == 315:
                        # For these wind directions, we want both sides of the rectangle:
                        ind_y = np.where(ybldg == max(ybldg))[0][0]
                        xd = xbldg[ind_y]
                        d1 = Site.dist_calc(self, xd, max(ybldg), xd, min(ybldg))
                        ind_x = np.where(xbldg == max(xbldg))[0][0]
                        yd = ybldg[ind_x]
                        d2 = Site.dist_calc(self, max(xbldg), yd, min(ybldg), yd)
                        surf_area = parcel.h_bldg * (d1+d2)
                    # Add new row to empty DataFrame:
                    z_params = z_params.append({'Building Height': parcel.h_bldg, 'Surface Area': surf_area}, ignore_index=True)

                # Calculate the average height of all buildings within the fetch length:
                h_avg = z_params['Building Height'].mean()
                # Calculate the total surface area for all buildings within the fetch length:
                total_surf = sum(z_params['Surface Area'])
                # Calculate the site area: EPSG:4326
                # Calculate the meters distance of the fetch length:
                fdist = Site.dist_calc(self, originz.x, originz.y, originz.x + f, originz.y)
                site_area = (math.pi*fdist**2)/4
                #site_area = ops.transform(partial(pyproj.transform, pyproj.Proj(init='WGS84'), pyproj.Proj(proj='aea', lat_1 = boundary.bounds[1], lat_2 = boundary.bounds[3])), boundary)
                #print(site_area.area)

                # Calculate the roughness length:
                z0 = 0.5*h_avg*total_surf/site_area
                print('Roughness length:', z0)
                # Calculate the wind speed:
                vnew = Site.calc_windspeed(self, parcel.h_bldg, z0)
                # Calculate the meters distance of the fetch length:
                #fdist = Site.dist_calc(self, originz.x, originz.y, originz.x+f, originz.y)
                print('Fetch in meters:', fdist, "Fetch size:", f)
                # Populate the DataFrame with the values for this fetch length:
                terrain_params = terrain_params.append({'Roughness Length': z0, 'Fetch Length': fdist, 'Local Wind Speed': vnew}, ignore_index=True)
                # Check the difference in the wind speed:
                if len(terrain_params['Roughness Length']) == 1:
                    tol = 1.0  # provide a default value for the tolerance for first z0
                else:
                    tol1 = terrain_params.loc[terrain_params.index[-1], "Local Wind Speed"] # get current wind speed
                    tol2 = terrain_params.loc[terrain_params.index[-2], "Local Wind Speed"] # get previous step wind speed
                    tol = abs((tol1-tol2)/tol1)
        # Break the loop if the new fetch length provides us with the right tolerance value:
            if abs(tol) < 0.1 and z0 > 0.1:
                # Now that we've identified all parcels, plot for confirmation:
                plt.plot(xp, yp, xsite, ysite)
                plt.axis('equal')
                plt.show()
                print("fetch length:", fdist)
                print("roughness length:", z0)
                print("tolerance:", abs(tol))
                break
            else:
                pass

    def get_sector(self, originz, wind_direction, f):
        # For the given wind direction, determine the geometries for each sector
        # Create an empty list to store sector geometries ([0] = sector in -45 degrees, [1] = sector +45 degrees
        sector_geom = []
        # Begin by defining a circle with radius = current fetch:
        circ = originz.buffer(f, resolution=200)
        # To determine the sector geometries for each wind direction, divide the circle into: halves, quarters, sectors
        if wind_direction == 0 or wind_direction == 180:
            # Define boundary line1:
            rad = math.pi * (1 / 4)
            bline1 = LineString([(originz.x - f * math.cos(rad), originz.y + f * math.sin(rad)), (originz.x + f * math.cos(rad), originz.y - f * math.sin(rad))])
            # Split the circle into two polygons
            circ_split = ops.split(circ, bline1)
            # Choose the first polygon to do a check and assign boundary for the wind direction:
            x1, y1 = circ_split[0].exterior.xy
            if wind_direction == 0:
                # For 0 degrees, use point in upper right-hand quadrant:
                # Polygon we want will have a maximum longitude that is greater than the longitude for this point
                if max(x1) > originz.x + f * math.cos(rad):
                    half_circ = circ_split[0]
                else:
                    half_circ = circ_split[1]
                # Split the half-circle to get the sector we want:
                bline2 = LineString([(originz.x - f * math.cos(rad), originz.y - f * math.sin(rad)),
                                     (originz.x + f * math.cos(rad), originz.y + f * math.sin(rad))])
                circ_split2 = ops.split(half_circ, bline2)
                # Choose the first polygon to do a check and assign boundary for the wind direction:
                x2, y2 = circ_split2[0].exterior.xy
                # Polygon we want will have a maximum latitude that is greater than the latitude in upper RH quadrant:
                if max(y2) > originz.y + f * math.sin(rad):
                    boundary = circ_split2[0]
                else:
                    boundary = circ_split2[1]
            elif wind_direction == 180:
                # For 180 degrees, use point in lower left-hand quadrant:
                # Polygon we want will have a minimum longitude that is smaller than the longitude for this point
                if min(x1) < originz.x - f * math.cos(rad):
                    half_circ = circ_split[0]
                else:
                    half_circ = circ_split[1]
                # Split the half-circle to get the sector we want:
                bline2 = LineString([(originz.x - f * math.cos(rad), originz.y - f * math.sin(rad)),
                                     (originz.x + f * math.cos(rad), originz.y + f * math.sin(rad))])
                circ_split2 = ops.split(half_circ, bline2)
                # Choose the first polygon to do a check and assign boundary for the wind direction:
                x2, y2 = circ_split2[0].exterior.xy
                # Polygon we want will have a minimum latitude that is smaller than the latitude in lower LH quadrant:
                if min(y2) < originz.y - f * math.sin(rad):
                    boundary = circ_split2[0]
                else:
                    boundary = circ_split2[1]
        elif wind_direction == 90 or wind_direction == 270:
            # Define boundary line1:
            rad = math.pi * (1 / 4)
            bline1 = LineString([(originz.x - f * math.cos(rad), originz.y - f * math.sin(rad)), (originz.x + f * math.cos(rad), originz.y + f * math.sin(rad))])
            # Split the circle in half
            circ_split = ops.split(circ, bline1)
            # Choose the first polygon to do a check and choose the right half for the wind direction:
            x1, y1 = circ_split[0].exterior.xy
            if wind_direction == 90:
                # For 90 degrees, use point in upper right-hand quadrant:
                # Polygon we want will have a maximum longitude that is larger than the longitude for this point
                if max(x1) > originz.x + f * math.cos(rad):
                    half_circ = circ_split[0]
                else:
                    half_circ = circ_split[1]
                # Split the half-circle to get the quadrant we want:
                bline2 = LineString([(originz.x - f * math.cos(rad), originz.y + f * math.sin(rad)), (originz.x + f * math.cos(rad), originz.y - f * math.sin(rad))])
                circ_split2 = ops.split(half_circ, bline2)
                # Choose the first polygon to do a check and choose the right quadrant:
                x2, y2 = circ_split2[0].exterior.xy
                # Polygon we want will have a maximum longitude that is greater than the longitude in upper RH quadrant:
                if max(x1) > originz.x + f * math.cos(rad):
                    quad_circ = circ_split2[0]
                else:
                    quad_circ = circ_split2[1]
                # Split the quadrant into sectors:
                bline3 = LineString([(originz.x - f, originz.y), (originz.x + f, originz.y)])
                circ_split3 = ops.split(quad_circ, bline3)
                # Choose the first polygon to do a check and assign sector geometries:
                x3, y3 = circ_split3[0].exterior.xy
                # Polygon for first sector (smaller angle) will have maximum latitude greater than "origin":
                if max(y3) > originz.y:
                    sector_geom.append(circ_split3[0])
                    sector_geom.append(circ_split3[1])
                else:
                    sector_geom.append(circ_split3[1])
                    sector_geom.append(circ_split3[0])
            elif wind_direction == 270:
                # For 270 degrees, use point in upper left-hand quadrant:
                # Polygon we want will have a minimum longitude that is smaller than the longitude for this point
                if min(x1) < originz.x - f * math.cos(rad):
                    half_circ = circ_split[0]
                else:
                    half_circ = circ_split[1]
                # Split the half-circle to get the sector we want:
                bline2 = LineString([(originz.x - f * math.cos(rad), originz.y + f * math.sin(rad)),
                                     (originz.x + f * math.cos(rad), originz.y - f * math.sin(rad))])
                circ_split2 = ops.split(half_circ, bline2)
                # Choose the first polygon to do a check and assign boundary for the wind direction:
                x2, y2 = circ_split2[0].exterior.xy
                # Polygon we want will have a minimum longitude that is smaller than the longitude in upper LH quadrant:
                if min(x2) < originz.x - f * math.cos(rad):
                    quad_circ = circ_split2[0]
                else:
                    quad_circ = circ_split2[1]
                # Split the quadrant into sectors:
                bline3 = LineString([(originz.x - f, originz.y), (originz.x + f, originz.y)])
                circ_split3 = ops.split(quad_circ, bline3)
                # Choose the first polygon to do a check and assign sector geometries:
                x3, y3 = circ_split3[0].exterior.xy
                # Polygon for first sector (smaller angle) will have maximum latitude greater than "origin":
                if max(y3) > originz.y:
                    sector_geom.append(circ_split3[0])
                    sector_geom.append(circ_split3[1])
                else:
                    sector_geom.append(circ_split3[1])
                    sector_geom.append(circ_split3[0])
                # Plot for confirmation:
                xs, ys = sector_geom[0].exterior.xy
                xs2, ys2 = sector_geom[1].exterior.xy
                plt.plot(xs, ys, xs2, ys2)
                plt.show()
        elif wind_direction == 45 or wind_direction == 225:
            # Define boundary line1:
            rad = math.pi * (1 / 4)
            bline1 = LineString([(originz.x, originz.y - f), (originz.x, originz.y + f)])
            # Split the circle into two polygons
            circ_split = ops.split(circ, bline1)
            # Choose the first polygon to do a check and assign boundary for the wind direction:
            x1, y1 = circ_split[0].exterior.xy
            if wind_direction == 45:
                # For 45 degrees, use maximum longitude:
                if max(x1) > originz.x:
                    half_circ = circ_split[0]
                else:
                    half_circ = circ_split[1]
                # Split the half-circle to get the sector we want:
                bline2 = LineString([(originz.x - f, originz.y), (originz.x + f, originz.y)])
                circ_split2 = ops.split(half_circ, bline2)
                # Choose the first polygon to do a check and assign boundary for the wind direction:
                x2, y2 = circ_split2[0].exterior.xy
                # Use maximum latitude:
                if max(y2) > originz.y:
                    boundary = circ_split2[0]
                else:
                    boundary = circ_split2[1]
            elif wind_direction == 225:
                # For 225 degrees, use minimum longitude:
                if min(x1) < originz.x:
                    half_circ = circ_split[0]
                else:
                    half_circ = circ_split[1]
                # Split the half-circle to get the sector we want:
                bline2 = LineString([(originz.x - f, originz.y), (originz.x + f, originz.y)])
                circ_split2 = ops.split(half_circ, bline2)
                # Choose the first polygon to do a check and assign boundary for the wind direction:
                x2, y2 = circ_split2[0].exterior.xy
                # Use minimum latitude:
                if min(y2) < originz.y:
                    boundary = circ_split2[0]
                else:
                    boundary = circ_split2[1]
        elif wind_direction == 135 or 315:
            # Define boundary line1:
            rad = math.pi * (1 / 4)
            bline1 = LineString([(originz.x, originz.y - f), (originz.x, originz.y + f)])
            # Split the circle into two polygons
            circ_split = ops.split(circ, bline1)
            # Choose the first polygon to do a check and assign boundary for the wind direction:
            x1, y1 = circ_split[0].exterior.xy
            if wind_direction == 135:
                # For 135 degrees, use maximum longitude:
                if max(x1) > originz.x:
                    half_circ = circ_split[0]
                else:
                    half_circ = circ_split[1]
                # Split the half-circle to get the sector we want:
                bline2 = LineString([(originz.x - f, originz.y), (originz.x + f, originz.y)])
                circ_split2 = ops.split(half_circ, bline2)
                # Choose the first polygon to do a check and assign boundary for the wind direction:
                x2, y2 = circ_split2[0].exterior.xy
                # Use minimum latitude:
                if min(y2) < originz.y:
                    boundary = circ_split2[0]
                else:
                    boundary = circ_split2[1]
            elif wind_direction == 315:
                # For 225 degrees, use minimum longitude:
                if min(x1) < originz.x:
                    half_circ = circ_split[0]
                else:
                    half_circ = circ_split[1]
                # Split the half-circle to get the sector we want:
                bline2 = LineString([(originz.x - f, originz.y), (originz.x + f, originz.y)])
                circ_split2 = ops.split(half_circ, bline2)
                # Choose the first polygon to do a check and assign boundary for the wind direction:
                x2, y2 = circ_split2[0].exterior.xy
                # Use maximum latitude:
                if max(y2) < originz.y:
                    boundary = circ_split2[0]
                else:
                    boundary = circ_split2[1]
        # Plot the site boundary
        xsite, ysite = boundary.exterior.xy
        # plt.plot(xp, yp, xsite, ysite)
        # plt.show()
        return sector_geom

    def dist_calc(self, lon1, lat1, lon2, lat2):
        # Calculate distance between two longitude, latitude points using the Haversine formula:
        earth_radius = 6371000  # radius of Earth in meters
        phi_1 = math.radians(lat1)
        phi_2 = math.radians(lat2)

        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(lon2 - lon1)

        a = math.sin(delta_phi / 2.0) ** 2 + math.cos(phi_1) * math.cos(phi_2) * math.sin(delta_lambda / 2.0) ** 2

        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        dist = earth_radius * c  # output distance in meters
        dist = distance.distance((lat1, lon1), (lat2, lon2)).kilometers*1000

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
lon = -85.620215
lat = 30.180998
test = Parcel('14805-133-000', 1, 'SINGLE FAM', 2009, '1806  EVERITT AVE   PANAMA CITY 32405', 2103, lon, lat)
# Create an instance of the site class:
wind_direction = 270

# data is a DataFrame object with column label = ['geometry'] and indexes = [0: end]
# Accessing a specific Polygon object then requires: data['geometry'][index]

site = Site(test, wind_direction)
#test = site.calc_windspeed(21, 0.78, 11.7, 10, 0.08)
#print(test)

# Recreating plot from HAZUS-HM
#heights = np.array([3, 5, 10, 20, 50, 100])
#zs = np.linspace(0.001,1,1000)
#for h in heights:
    #lst = []
    #for z in zs:
        #ratio = site.calc_windspeed(h, z, 80, href=h)
        #lst.append(ratio)
    #plt.loglog(zs, lst)

#plt.grid(True)
#plt.show()