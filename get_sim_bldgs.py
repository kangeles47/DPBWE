from bldg_code import ASCE7


def get_sim_bldgs(bldg, site, hazard_type, component_type, event_year, sfh_flag):
    sim_bldgs = []
    if hazard_type == 'wind':
        if component_type == 'roof cover':
            # Calculate height range for the case study structure:
            hlower = ((bldg.hasGeometry['Height']) - (bldg.hasGeometry['Height']/len(bldg.hasStory)))
            if sfh_flag:  # Exception for single family homes: Do not look at two-story structures
                hupper = ((bldg.hasGeometry['Height']) + 0.5*(bldg.hasGeometry['Height']/len(bldg.hasStory)))
            else:
                hupper = ((bldg.hasGeometry['Height']) + (bldg.hasGeometry['Height'] / len(bldg.hasStory)))
            # Find buildings in the regional inventory that have the same or similar roof cover type:
            for compare_bldg in site.hasBuilding:
                # Skip buildings constructed after the year of the event:
                if compare_bldg.hasYearBuilt >= 2016 or compare_bldg.hasYearBuilt > event_year:
                    pass
                #elif compare_bldg.hasYearBuilt <= 2001:
                 #   pass
                else:
                    # Check if this building has a similar or same roof cover:
                    rcover_flag = check_sim_rcover(bldg, compare_bldg)
                    if rcover_flag:
                        # Check if this building is within one-story height of case study (similitude params):
                        if hlower <= compare_bldg.hasGeometry['Height'] <= hupper:
                            # Check if this building has a similar load path:
                            lpath_flag = check_sim_lpath_rcover(bldg, compare_bldg)
                            if lpath_flag:
                                sim_bldgs.append(compare_bldg)
                            else:
                                pass
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
    # Pass through any buildings that do not have roof cover info:
    if isinstance(compare_bldg.hasElement['Roof'][0].hasCover, str):
        if bldg.hasElement['Roof'][0].hasCover == compare_bldg.hasElement['Roof'][0].hasCover:
            rcover_flag = True
        else:
            rcover_flag = False
            # Split the roof cover string and check for similarities:
            #rcover_type = bldg.hasElement['Roof'][0].hasCover.split()
            #for i in rcover_type:
             #   if i in compare_bldg.hasElement['Roof'][0].hasCover:
              #      rcover_flag = True
               #     break
                #else:
                 #   rcover_flag = False
    else:
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