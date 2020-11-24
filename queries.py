from asset import Site, Building



def get_bldgs_at_dist(site, ref_bldg, dist):
    # Query 1: Hazard Analysis:
    # Given that Building A is within Site A, what buildings are within X distance from Building A?
    # Begin by defining a circle with radius = dist around ref_bldg:
    origin = ref_bldg.hasLocation['Geodesic']
    circ = origin.buffer(dist, resolution=200)
    # Create an empty list to hold any qualifying bldg:
    bldg_list = []
    for bldg in site.hasBuilding:
        bldg_location = bldg.hasLocation['Geodesic']
        # Check if the building is within the specified boundary:
        if bldg_location.within(circ):
            bldg_list.append(bldg)
        else:
            pass
    return bldg_list