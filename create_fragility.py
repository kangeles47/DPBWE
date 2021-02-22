import pandas as pd
import ast
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


def add_permit_data(bldg, df_inventory, parcel_identifier, dis_permit_file_path, permit_file_path=None):
    # Permit data can be leveraged to inform:
    # (1) the presence of damage (disaster permits) or
    # (2) the presence of a retrofit (e.g., re-roofing)
    # To bring in permit data, there needs to be a way to map permit number to parcel
    # E.g., the permit may be listed in the parcel's property listing or
    # the permit database may have the parcel's address
    # Load the disaster permit data:
    if dis_permit_file_path is not None:
        df_dis_permit = pd.read_csv(dis_permit_file_path)
    # Load the regular permit data:
    if permit_file_path is not None:
        df_permit = pd.read_csv(permit_file_path)
    # Find permit descriptions for the parcel:
    if parcel_identifier is not None:  # Address or parcel number match
        if dis_permit_file_path is not None:
            dis_permits = df_dis_permit.loc[df_dis_permit['SITE_ADDR'] == parcel_identifier]
        if permit_file_path is not None:
            permits = df_permit.loc[df_permit['SITE_ADDR'] == parcel_identifier]
    else:  # Permit number match
        # Access the parcel's list of permits:
        for p in bldg.hasPermit:
            # Find the permit descriptions:
            if 'DIS' in p and dis_permit_file_path is not None:
                dis_permits = df_dis_permit.loc[df_dis_permit['Permit Number'] == p]
            else:
                if 'DIS' not in p and permit_file_path is not None:
                    permits = df_permit.loc[df_permit['Permit Number'] == p]
    # Use the permit description to determine the damage type or a retrofit condition:


def get_dis_permit_damage(bldg, df_dis_permits, df_inventory, obsv_damage_type):
    # Allocate empty lists to gather damage information:
    if obsv_damage_type == 'roof_cover':
        rcover_damage_cat = []
        rcover_damage_percent = []
    else:
        pass
    # Loop through the disaster permits:
    for p in range(0, len(df_dis_permits['Permit Number'])):
        if obsv_damage_type == 'roof_cover':
            # First check if this building shares a parcel number:
            if df_inventory['Use Code'][p] != 'RES COMMON (000900)':
                dup_parcel = df_inventory.loc[df_inventory['Parcel ID'] == df_inventory['Parcel ID'][p]]
                dup_parcel_factor = dup_parcel['Square Footage'][p] / dup_parcel['Square Footage'].sum()
            else:
                pass
            permit_type = ast.literal_eval(df_dis_permits['Disaster Permit Type'][p])
            permit_desc = ast.literal_eval(df_dis_permits['Disaster Permit Description'][p])
            permit_cat = []
            permit_dpercent = []
            for permit in range(0, len(permit_type)):
                if 'ROOF' in permit_type[permit]:
                    if 'GAZ' in permit_desc[permit] or 'CANOPY' in permit_desc[permit]:
                        permit_cat.append(0)
                        permit_dpercent.append(0)
                    else:
                        # Conduct a loop to categorize all quantitative descriptions:
                        damage_desc = permit_desc[permit].split()
                        for i in range(0, len(damage_desc)):
                            if damage_desc[i].isdigit():  # First check if the permit has a quantity for the damage
                                total_area = bldg.hasGeometry['Total Area']
                                stories = len(bldg.hasStory)
                                num_roof_squares = float(damage_desc[i]) * dup_parcel_factor
                                unit = 'ft'
                                roof_dcat, roof_dpercent = roof_square_damage_cat(total_area, stories, num_roof_squares, unit)
                                permit_cat.append(roof_dcat)
                                permit_dpercent.append(roof_dpercent)
                                break
                            else:
                                if 'SQ' in damage_desc[i]:  # Case when there is no space between quantity and roof SQ
                                    total_area = bldg.hasGeometry['Total Area']
                                    stories = len(bldg.hasStory)
                                    num_roof_squares = float(damage_desc[i][0:-2]) * dup_parcel_factor  # Remove 'SQ' from description and extract value:
                                    unit = 'ft'
                                    roof_dcat, roof_dpercent = roof_square_damage_cat(total_area, stories, num_roof_squares, unit)
                                    permit_cat.append(roof_dcat)
                                    permit_dpercent.append(roof_dpercent)
                                    break
                                else:
                                    pass
                        # Add a dummy value for permits that have a qualitative description:
                        if len(permit_cat) != permit + 1:
                            permit_cat.append(0)
                            permit_dpercent.append(0)
                        else:
                            pass
                        # Conduct a second loop to now categorize qualitative descriptions:
                        if permit_cat[permit] > 0:
                            pass
                        else:
                            substrings = ['RE-ROO', 'REROOF', 'ROOF REPAIR', 'COMMERCIAL HURRICANE REPAIRS', 'ROOF OVER']
                            if any([substring in permit_desc[permit] for substring in substrings]):
                                permit_cat[permit] = 1
                                permit_dpercent[permit] = roof_percent_damage_qual(permit_cat[permit])
                            elif 'REPLACE' in permit_desc[permit]:
                                permit_cat[permit] = 2
                                permit_dpercent[permit] = roof_percent_damage_qual(permit_cat[permit])
                            elif 'WITHDRAWN' in permit_desc[permit]:
                                permit_cat[permit] = 0
                                permit_dpercent[permit] = roof_percent_damage_qual(permit_cat[permit])
                            elif 'NEW' in permit_desc[permit]:
                                permit_cat[permit] = 3
                                permit_dpercent[permit] = 100
                            else:
                                print(permit_desc[permit])
                else:
                    permit_cat.append(0)
                    permit_dpercent.append(0)
            rcover_damage_cat.append(permit_cat)
            rcover_damage_percent.append(permit_dpercent)
    else:
        pass
    # Integrate damage categories into the DataFrame:
    if obsv_damage_type == 'roof_cover':
        df_local['HAZUS Roof Damage Category'] = rcover_damage_cat
        df_local['Percent Roof Cover Damage'] = rcover_damage_percent
    else:
        pass
    # Clean-up roof damage categories:
    for dparcel in range(0, len(df_local['HAZUS Roof Damage Category'])):
        rcat = df_local['HAZUS Roof Damage Category'][dparcel]
        if len(rcat) == 1:
            pass
        else:
            if (df_local['Use Code'][dparcel] != 'RES COMMON (000900)') or (df_local['Use Code'][dparcel] != 'PLAT HEADI (H.)'):
                # Choose the largest damage category as this parcel's damage category:
                dcat = max(rcat)
                dcat_idx = rcat.index(dcat)
                df_local.at[dparcel, 'HAZUS Roof Damage Category'] = [dcat]
                df_local.at[dparcel, 'Percent Roof Cover Damage'] = df_local['Percent Roof Cover Damage'][dparcel][dcat_idx]
            else:
                pass
    # Clean up percent categories:
    max_percent = []
    min_percent = []
    for item in rcover_damage_percent:
        if len(item) == 1:
            try:
                if len(item[0]) > 1:  # Percent damage description is a range of values
                    min_percent.append(item[0][0])
                    max_percent.append(item[0][1])
            except TypeError:   # Percent damage description is one value
                min_percent.append(item[0])
                max_percent.append(item[0])
        else:
            for subitem in range(0, len(item)):
                if subitem == 0:  # Use the first index in this list to initialize values
                    try:  # Percent damage description is a range of values
                        min_item = item[subitem][0]
                        max_item = item[subitem][1]
                    except TypeError:  # Percent damage description is one value
                        min_item = item[subitem]
                        max_item = item[subitem]
                else:
                    try:
                        if item[subitem] > min_item:
                            min_item = item[subitem]
                            max_item = item[subitem]
                        else:
                            pass
                    except TypeError:
                        if item[subitem][1] > max_item:
                            min_item = item[subitem][0]
                            max_item = item[subitem][1]
                        else:
                            pass
            min_percent.append(min_item)
            max_percent.append(max_item)
    df_local['Max Roof Cover Damage'] = max_percent
    df_local['Min Roof Cover Damage'] = min_percent
    df_local = df_local.drop('Percent Roof Cover Damage', axis=1)
    return df_local


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
