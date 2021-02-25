from bldg_code import ASCE7


def get_sim_bldgs(bldg, site, hazard_type, component_type):
    sim_bldgs = []
    if hazard_type == 'wind':
        if component_type == 'roof cover':
            # Find buildings in the regional inventory that have the same or similar roof cover type:
            for compare_bldg in site.hasBuilding:
                # Start by checking if this building has a similar or same roof cover:
                rcover_flag = check_sim_rcover(bldg, compare_bldg)
                # Check if this building has a similar load path:
                if rcover_flag:
                    lpath_flag = check_sim_lpath_rcover(bldg, compare_bldg)
                    if lpath_flag:
                        sim_bldgs.append(compare_bldg)
                    else:
                        pass
                else:
                    pass
        elif component_type == 'roof structure':
            pass
    elif hazard_type == 'surge':
        pass
    elif hazard_type == 'wind-borne debris':
        pass
    elif hazard_type == 'rain':
        pass
    return sim_bldgs


def check_sim_rcover(bldg, compare_bldg):
    if bldg.hasElement['Roof'].hasCover == compare_bldg.hasElement['Roof'].hasCover:
        rcover_flag = True
    else:
        # Check if the roof cover types have similar characteristics:
        rcover_flag = False
    return rcover_flag


def check_sim_lpath_rcover(bldg, compare_bldg):
    bldg_list = [bldg, compare_bldg]
    rcover_case = []
    for b in bldg_list:
        asce7 = ASCE7(b, loading_flag=True)
        rcover_case.append(asce7.get_rcover_case(b))
    if rcover_case.count(rcover_case[0]) == 2:
        lpath_flag = True
    else:
        lpath_flag = False
    return lpath_flag