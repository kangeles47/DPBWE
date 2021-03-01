import pandas as pd
import zone
import get_sim_bldgs
import post_disaster_damage_data_source


def create_fragility(bldg, site, component_type, hazard_type, event_year, event_name, data_types, file_paths):
    # Step 1: Find similar buildings based on similarity in features, load path for the given hazard
    sim_bldgs = get_sim_bldgs.get_sim_bldgs(bldg, site, hazard_type, component_type)
    # Step 2: Find damage descriptions for each building
    data_list = []
    for i in range(0, len(data_types)):
        if isinstance(data_types[i], post_disaster_damage_data_source.STEER):
            data_details = data_types[i].add_steer_data(bldg, component_type, hazard_type, file_paths[i])
        elif isinstance(data_types[i], post_disaster_damage_data_source.BayCountyPermits):
            data_details = data_types[i].add_permit_data(bldg, component_type, hazard_type, file_paths[i])
        data_list.append(data_details)
    # Step 3: Choose the best data source for this damage description: