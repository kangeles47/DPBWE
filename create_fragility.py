import pandas as pd
import matplotlib.pyplot as plt
from zone import Building


def add_steer_data(bldg, parcel_identifier, steer_file_path):
    # Parcel identifier should be the parcel's address in the following format (not case-sensitive):
    # 1842 BRIDGE ST Panama City BAY FL 32409 USA (number, street, city, county, state, zip, country)
    df_steer = pd.read_csv(steer_file_path)
    try:
        # Check if the parcel has a StEER observation:
        idx = df_steer.loc[df_steer['address_full'].lower() == parcel_identifier].index[0]
        # Extract StEER damage data:
        bldg.hasDamageData['hazard'] = df_steer['hazards_present'][idx]
        bldg.hasDamageData['wind damage rating'] = df_steer['wind_damage_rating'][idx]
        bldg.hasElement['Roof'].hasShape[df_steer['roof_shape'][idx].lower()] = True
        bldg.hasElement['Roof'].hasPitch = df_steer['roof_slope'][idx]
        bldg.hasStructuralSystem = df_steer['mwfrs'][idx]
        bldg.hasElement['Roof'].hasCover = df_steer['roof_cover'][idx]
        bldg.hasDamageData['roof']['cover']['StEER'] = df_steer['roof_cover_damage_'][idx]
        bldg.hasDamageData['roof']['structure']['StEER'] = df_steer['roof_structure_damage_'][idx]
        bldg.hasDamageData['roof']['substrate']['StEER'] = df_steer['roof_substrate_damage'][idx]
        if int(df_steer['reroof_year'][idx]) > bldg.hasElement['Roof'].hasYearBuilt:
            bldg.hasElement['Roof'].hasYearBuilt = int(df_steer['reroof_year'][idx])
        else:
            pass
        # Add roof damage data description to Roof Element:
        bldg.hasElement['Roof'].hasDamageData = bldg.hasDamageData['Roof']
    except IndexError:  # No StEER entry exists for this building
        pass


def find_damage_data(bldg_identifier, component_type, steer_flag, crowd_sourced_flag, fema_modeled_flag, fema_claims_flag, imagery_postp_flag, ind_recon_flag, bldg_permit_flag):
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