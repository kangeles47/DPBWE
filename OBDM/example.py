# -------------------------------------------------------------------------------
# Name:             example.py
# Purpose:          Provide a simple examples to familiarize users with the ontology-based data model
#
# Author:           Karen Irely Angeles (kangeles@nd.edu)
# Affiliation:      Department of Civil and Environmental Engineering and Earth Sciences,
#                   University of Notre Dame, Notre Dame, IN

# Last updated:          (v1) 01/20/2021
# ------------------------------------------------------------------------------

from zone import Site, Building, Story, Space
from element import Roof, Floor


def run_example1():
    # Create an instance of the Site Class:
    site = Site()
    # Add three instances of the Building Class to the Site:
    for i in range(0, 3):
        site.hasBuilding.append(Building())
    # Add four Story instances to the second building in the Site:
    for j in range(0, 4):
        site.hasBuilding[1].hasStory.append(Story())
    # Add three Space instances to the second story of the second building in the Site:
    for k in range(0, 3):
        site.hasBuilding[1].hasStory[1].hasSpace.append(Space())
    # Add relational attributes:
    site.hasBuilding[1].hasStory[1].update_zones()
    site.hasBuilding[1].update_zones()
    site.update_zones()
    return site


def run_example2():
    # Create an instance of the Building Class
    bldg = Building()  # Building object with default attributes
    # Add parcel data to the Building object:
    pid = '123-456-789'
    num_stories = 4
    occupancy = 'commercial'
    yr_built = 2021
    address = 'Number StreetName City State Zip Code'
    area = 4000
    lon = 0
    lat = 0
    bldg.add_parcel_data(pid, num_stories, occupancy, yr_built, address, area, lon, lat)
    # The add_parcel_data function created new Story objects for the Building:
    print(bldg.hasStory)
    return bldg


def run_example3():
    # Create an instance of the Building Class:
    bldg = Building()
    # Create a Roof object and add some component-level attributes:
    new_roof = Roof()
    new_roof.hasType = 'asphalt shingles'
    new_roof.hasShape['gable'] = True
    # Add the Roof to the building
    bldg.adjacentElement['Roof'].append(Roof())  # Roof bounds the building geometry
    # Create a Floor object and add some component-level attributes::
    new_floor = Floor()
    new_floor.hasType = 'two-way concrete slab'
    new_floor.hasYearBuilt = 2021
    bldg.containsElement['Floor'].append(new_floor)  # Assume this is an interior floor
    # Update the building's hasElement attribute:
    bldg.update_elements()
    return bldg


# Example 1: Introduction to Zone hierarchies and relational attributes:
site = run_example1()
# Example 2: Adding parcel data to a Building object:
bldg = run_example2()
# Example 3: Adding components to a Zone object and attributes to components
bldg2 = run_example3()
