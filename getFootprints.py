import wget
import zipfile
import json
from shapely.geometry import Point, Polygon


# download original Florida footprints
url = 'https://usbuildingdata.blob.core.windows.net/usbuildings-v1-1/Florida.zip'
zipFile = wget.download(url)

# unzip it and you'll get the geojson file
with zipfile.ZipFile(zipFile, 'r') as zip_ref:
    zip_ref.extractall('.')

# the name of the unzipped file is
jFile = 'Florida.geojson'


# if you want to pick up all buildings in a region you are interested, continue to do the following:


# define a region of interest using log and lat
# for Bay County case studies, choosing the following reference points (ccw): Frank Brown Park, Lynn Haven, Callaway, St. Andrews State Park (water)
boundaryPts = [[-85.873214, 30.224994],[-85.648318, 30.243202],[-85.574411, 30.142640],[-85.758186, 30.135363]]
boundary = Polygon(boundaryPts)


# pick up buildings withing the defined boundary
features = []
with open(jFile) as BuildingFootPrintsFile:

    bldgFootPrints = json.load(BuildingFootPrintsFile)
    bldgFootPrintsFeatures = bldgFootPrints["features"]
    bldgFootPrintsFeatures =  bldgFootPrintsFeatures[0:]
    
    for bfpf in bldgFootPrintsFeatures:
        pts = bfpf['geometry']['coordinates'][0]
        if Point(pts[0]).within(boundary):
            features.append(bfpf)


# Now you have those shapes in features, you can do something with it
# or you can put them in a new geojson file like this:
bldgFootPrints['features'] = features
with open('BayCounty.geojson', 'w') as outfile:
    json.dump(bldgFootPrints, outfile)