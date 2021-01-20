# -------------------------------------------------------------------------------
# Name:             example.py
# Purpose:          Provide a simple example familiarize users with the ontology-based data model
#
# Author:           Karen Irely Angeles (kangeles@nd.edu)
# Affiliation:      Department of Civil and Environmental Engineering and Earth Sciences,
#                   University of Notre Dame, Notre Dame, IN

# Last updated:          (v1) 01/20/2021
# ------------------------------------------------------------------------------

from zone import Building, Story, Space


def run_bldg_example():
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
    # Let's say we wanted to add a new Space object to the first Story (a lobby):
    space = Space()
    