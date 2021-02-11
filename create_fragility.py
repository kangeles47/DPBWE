import pandas as pd
import matplotlib.pyplot as plt


def find_damage_data(bldg_location, component_type, steer_flag, crowd_sourced_flag, fema_modeled_flag, fema_claims_flag, imagery_postp_flag, ind_recon_flag, bldg_permit_flag):
    data_details_dict = {'Damage Precision': {'type': None, 'value': None},
                         'Location Precision': None}
    damage_data_dict = {'StEER': None, 'Crowd-sourced': None, 'FEMA modeled': None, 'FEMA claims': None,
                        'Imagery Post-Processed': None, 'Independent Recon Observations': None, 'Building Permits': None}
    # Check if the building has a damage description for each of the user-defined data sources:
    damage_data_dict = {}
    if steer_flag:
        pass
        # damage_data_dict['StEER'] = {'Damage Precision': {'type: 'Component, discrete', 'value': None}, 'Location Precision': None}
    if crowd_sourced_flag:
        pass
    if fema_modeled_flag:
        pass
    if fema_claims_flag:
        pass
    if imagery_postp_flag:
        pass
    if ind_recon_flag:
        pass
    if bldg_permit_flag:
        # Check to see if the parcel has a damage building permit for this component:
        pass
    # Figure out which data source is the best data source for this component:
    # Start with the damage precision description:
    return damage_data_dict
