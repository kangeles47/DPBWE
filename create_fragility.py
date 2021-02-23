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


def add_permit_data(bldg, df_inventory, parcel_identifier, event_year, dis_permit_file_path, permit_file_path=None, length_unit='ft'):
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
            bldg.hasPermit['disaster'] = dis_permits
            # Use the permit description to determine the damage type:
            obsv_damage_type = 'roof_cover'
            df_dis_new = get_dis_permit_damage(bldg, dis_permits, df_inventory, obsv_damage_type, length_unit)
        if permit_file_path is not None:
            permit_data = df_permit.loc[df_permit['SITE_ADDR'] == parcel_identifier]
            bldg.hasPermit['not disaster'] = permit_data
            # Use the permit description to determine the replacement/retrofit condition:
            for p in permit_data:
                update_yr_of_construction(bldg, p, event_year)
    else:  # Permit number match
        # Access the parcel's list of permits:
        if dis_permit_file_path is not None:
            for p in bldg.hasPermit['disaster']:
                # Find the permit descriptions:
                dis_permits = df_dis_permit.loc[df_dis_permit['Permit Number'] == p]
                # Use the permit description to determine the damage type:
                obsv_damage_type = 'roof_cover'
                df_dis_new = get_dis_permit_damage(bldg, dis_permits, df_inventory, obsv_damage_type, length_unit)
        if permit_file_path is not None:
            for p in bldg.hasPermit['not disaster']:
                permit_data = df_permit.loc[df_permit['Permit Number'] == p]
                # Use the permit description to determine the replacement/retrofit condition:
                update_yr_of_construction(bldg, permit_data, event_year)


def update_yr_of_construction(bldg, permit_data, event_year):
    # Update the year of construction for components or building:
    if 'ROOF' in permit_data['PERMITTYPE']:
        substrings = ['CANOPY', 'GAZ', 'BOAT', 'CAR', 'CLUB', 'GARAGE', 'PORCH', 'PATIO']
        if any([substring in permit_data['DESCRIPTION'].upper() for substring in substrings]):
            pass
        else:
            if 'NEW' in permit_data['PERMITSUBTYPE'] or 'REPLACEMENT' in permit_data['PERMITSUBTYPE']:  # Figure out what to do with roof-over
                new_year = int(permit_data['ISSUED'][-4:])
                if bldg.hasElement['Roof'].hasYearBuilt < new_year < event_year:
                    bldg.hasElement['Roof'].hasYearBuilt = new_year
                else:
                    pass
    else:
        pass


def get_dis_permit_damage(bldg, df_dis_permit, df_inventory, obsv_damage_type, length_unit):
    # Allocate empty lists to gather damage information:
    if obsv_damage_type == 'roof_cover':
        rcover_damage_cat = []
        rcover_damage_percent = []
    else:
        pass
    # Loop through the disaster permits:
    for p in range(0, len(df_dis_permit['Permit Number'])):
        if obsv_damage_type == 'roof_cover':
            # First check if this building shares a parcel number:
            if df_inventory['Use Code'][p] != 'RES COMMON (000900)':
                dup_parcel = df_inventory.loc[df_inventory['Parcel ID'] == df_inventory['Parcel ID'][p]]
                dup_parcel_factor = dup_parcel['Square Footage'][p] / dup_parcel['Square Footage'].sum()
            else:
                pass
            permit_type = ast.literal_eval(df_dis_permit['Disaster Permit Type'][p])
            permit_desc = ast.literal_eval(df_dis_permit['Disaster Permit Description'][p])
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
                                roof_dcat, roof_dpercent = roof_square_damage_cat(total_area, stories, num_roof_squares, length_unit)
                                permit_cat.append(roof_dcat)
                                permit_dpercent.append(roof_dpercent)
                                break
                            else:
                                if 'SQ' in damage_desc[i]:  # Case when there is no space between quantity and roof SQ
                                    total_area = bldg.hasGeometry['Total Area']
                                    stories = len(bldg.hasStory)
                                    num_roof_squares = float(damage_desc[i][0:-2]) * dup_parcel_factor  # Remove 'SQ' from description and extract value:
                                    roof_dcat, roof_dpercent = roof_square_damage_cat(total_area, stories, num_roof_squares, length_unit)
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
        df_dis_permit['HAZUS Roof Damage Category'] = rcover_damage_cat
        df_dis_permit['Percent Roof Cover Damage'] = rcover_damage_percent
    else:
        pass
    # Clean-up roof damage categories:
    for dparcel in range(0, len(df_dis_permit['HAZUS Roof Damage Category'])):
        rcat = df_dis_permit['HAZUS Roof Damage Category'][dparcel]
        if len(rcat) == 1:
            pass
        else:
            if (df_dis_permit['Use Code'][dparcel] != 'RES COMMON (000900)') or (df_dis_permit['Use Code'][dparcel] != 'PLAT HEADI (H.)'):
                # Choose the largest damage category as this parcel's damage category:
                dcat = max(rcat)
                dcat_idx = rcat.index(dcat)
                df_dis_permit.at[dparcel, 'HAZUS Roof Damage Category'] = [dcat]
                df_dis_permit.at[dparcel, 'Percent Roof Cover Damage'] = df_dis_permit['Percent Roof Cover Damage'][dparcel][dcat_idx]
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
    df_dis_permit['Max Roof Cover Damage'] = max_percent
    df_dis_permit['Min Roof Cover Damage'] = min_percent
    df_dis_permits = df_dis_permit.drop('Percent Roof Cover Damage', axis=1)
    return df_dis_permits

def roof_square_damage_cat(total_area, stories, num_roof_squares, unit):
    try:
        total_area = float(total_area)
    except:
        total_area = float(total_area.replace(',',''))
    if float(stories) == 0:
        stories = 1
    else:
        stories = float(stories)
    floor_area = total_area/stories
    if unit == 'ft':
        roof_square = 100  # sq_ft
    elif unit == 'm':
        roof_square = 100/10.764  # sq m
    roof_dpercent = 100*(roof_square*num_roof_squares/floor_area)
    if roof_dpercent > 100:
        roof_dpercent = 100
    else:
        pass
    # Determine damage category:
    if roof_dpercent <= 2:
        roof_dcat = 0
    elif 2 < roof_dpercent <= 15:
        roof_dcat = 1
    elif 15 < roof_dpercent <= 50:
        roof_dcat = 2
    elif roof_dpercent > 50:
        roof_dcat = 3
    else:
        roof_dcat = num_roof_squares
    return roof_dcat, roof_dpercent


def roof_percent_damage_qual(cat):
    # Given the HAZUS damage category, return the percent damage to the roof cover (min/max values):
    if cat == 0:
        roof_dpercent = [0, 2]
    elif cat == 1:
        roof_dpercent = [2, 15]
    elif cat == 2:
        roof_dpercent = [15, 50]
    elif cat == 3:
        roof_dpercent = [50, 100]
    elif cat == 4:
        roof_dpercent = [50, 100]
    return roof_dpercent


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
