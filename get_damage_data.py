import pandas as pd
import ast
import matplotlib.pyplot as plt
from zone import Building
from post_disaster_damage_data_source import STEER


def get_damage_data(bldg, event_year, df_inventory, steer_flag, bldg_permit_flag, find_permit_flag, crowd_sourced_flag,
                    fema_modeled_flag, fema_claims_flag, rsensing_imagery_flag, steer_file_path, permit_file_path,
                    dis_permit_file_path, crowd_sourced_file_path, fema_modeled_file_path, fema_claims_file_path,
                    rsensing_imagery_file_path):
    data_details_dict = {'damage precision': None, 'location precision': None,
                         'damage scale': {'type': None, 'global_damage_states': []}}
    damage_data_dict = {'steer': None, 'building permits': None, 'crowd-sourced': None, 'fema modeled': None,
                        'fema claims': None, 'remote-sensing/imagery': None}
    # Check if the building has a damage description for each of the user-defined data sources:
    damage_data_dict = {}
    if steer_flag:
        data_details_dict = {'damage precision': 'component', 'location precision': 'exact location',
                             'damage scale': {'type': 'HAZUS-HM', 'global_damage_states': ['No Damage', 'Minor Damage',
                                                                                           'Moderate Damage',
                                                                                           'Severe Damage',
                                                                                           'Destruction']}}
        # Need to find a way to extract damage state definitions for specific components
        parcel_identifier = bldg.hasLocation['Address']
        add_steer_data(bldg, parcel_identifier, steer_file_path, data_details_dict)
    if bldg_permit_flag:
        if find_permit_flag:
            parcel_identifier = bldg.hasLocation['Address']
        else:
            parcel_identifier = None
        add_permit_data(bldg, df_inventory, parcel_identifier, event_year, dis_permit_file_path, permit_file_path,
                        length_unit='ft')
    if crowd_sourced_flag:
        parcel_identifier = None
        add_crowd_sourced_data(bldg, parcel_identifier, crowd_sourced_file_path)
    if fema_modeled_flag:
        parcel_identifier = None
        add_fema_modeled_data(bldg, parcel_identifier, fema_modeled_file_path)
    if fema_claims_flag:
        parcel_identifier = bldg.hasLocation['Zip Code']
        add_fema_claims_data(bldg, parcel_identifier, fema_claims_file_path)
    if rsensing_imagery_flag:
        parcel_identifier = None
        add_rsensing_imagery_data(bldg, parcel_identifier, crowd_sourced_file_path)
    # Figure out which data source is the best data source for this component:
    # Start with the damage precision description:
    return damage_data_dict


def add_steer_data(self, bldg, component_type, hazard_type, steer_file_path):
    parcel_identifier = bldg.hasLocation['Address']
    # Parcel identifier should be the parcel's address in the following format (not case-sensitive):
    # 1842 BRIDGE ST Panama City BAY FL 32409 USA (number, street, city, county, state, zip, country)
    df_steer = pd.read_csv(steer_file_path)
    data_details = {'available': False, 'fidelity': None, 'component type': component_type, 'hazard type': hazard_type,
                    'value': None, 'hazard damage rating': {'wind': None, 'surge': None, 'rain': None}}
    try:
        # Check if the parcel has a StEER observation at its exact location:
        idx = df_steer.loc[df_steer['address_full'].lower() == parcel_identifier.lower()].index[0]
        # Create a new instance of this damage data source:
        steer_data = STEER()
        # Update the Location Precision attribute:
        steer_data.hasLocationPrecision['street level'] = False
        # Extract StEER damage data:
        for key in steer_data.hasHazard:
            if key in df_steer['hazards_present'].lower():
                steer_data.hasHazard[key] = True
        data_details['hazard_damage_rating']['wind'] = df_steer['wind_damage_rating'][idx]
        data_details['hazard_damage_rating']['surge'] = df_steer['surge_damage_rating'][idx]
        data_details['hazard_damage_rating']['rain'] = df_steer['rainwater_damage_rating'][idx]
        # Update building and component-level attributes:
        bldg.hasStructuralSystem = df_steer['mwfrs'][idx]
        bldg.hasElement['Roof'].hasCover = df_steer['roof_cover'][idx]
        bldg.hasElement['Roof'].hasShape[df_steer['roof_shape'][idx].lower()] = True
        bldg.hasElement['Roof'].hasPitch = df_steer['roof_slope'][idx]
        if int(df_steer['reroof_year'][idx]) > bldg.hasElement['Roof'].hasYearBuilt:
            bldg.hasElement['Roof'].hasYearBuilt = int(df_steer['reroof_year'][idx])
        else:
            pass
        # Extract component-level damage descriptions if the desired hazard is present:
        if steer_data.hasHazard[hazard_type]:
            # Extract component-level damage descriptions:
            if component_type == 'roof cover':
                # Check if there are roof-related damage descriptions:
                if df_steer['roof_cover_damage_'][idx] > 0:
                    data_details['available'] = True
                    data_details['value'] = df_steer['roof_cover_damage_'][idx]
                    # Update the damage data details:
                    steer_data.get_damage_scale('HAZUS-HM', 'roof cover', damage_states=None, values=None)
                    data_details['fidelity'] = steer_data
        else:
            pass
    except IndexError:  # No StEER entry exists for this exact location: Check General Area or does not exist
        pass
    return data_details


def add_permit_data(bldg, component_type, hazard_type, df_inventory, parcel_identifier, event_year,
                    dis_permit_file_path, permit_file_path=None,
                    length_unit='ft'):
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
            df_dis_new, data_details = get_dis_permit_damage(bldg, component_type, hazard_type, dis_permits,
                                                             df_inventory, obsv_damage_type, length_unit)
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
                df_dis_new, data_details = get_dis_permit_damage(bldg, component_type, hazard_type, dis_permits,
                                                                 df_inventory, obsv_damage_type, length_unit)
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


def get_dis_permit_damage(bldg, component_type, hazard_type, df_dis_permit, df_inventory, obsv_damage_type,
                          length_unit):
    data_details = {'available': False, 'fidelity': None, 'component type': component_type,
                    'hazard type': hazard_type,
                    'value': None, 'hazard damage rating': {'wind': None, 'surge': None, 'rain': None}}
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
                                roof_dcat, roof_dpercent = roof_square_damage_cat(total_area, stories, num_roof_squares,
                                                                                  length_unit)
                                permit_cat.append(roof_dcat)
                                permit_dpercent.append(roof_dpercent)
                                break
                            else:
                                if 'SQ' in damage_desc[i]:  # Case when there is no space between quantity and roof SQ
                                    total_area = bldg.hasGeometry['Total Area']
                                    stories = len(bldg.hasStory)
                                    num_roof_squares = float(damage_desc[i][
                                                             0:-2]) * dup_parcel_factor  # Remove 'SQ' from description and extract value:
                                    roof_dcat, roof_dpercent = roof_square_damage_cat(total_area, stories,
                                                                                      num_roof_squares, length_unit)
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
                            substrings = ['RE-ROO', 'REROOF', 'ROOF REPAIR', 'COMMERCIAL HURRICANE REPAIRS',
                                          'ROOF OVER']
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
            if (df_dis_permit['Use Code'][dparcel] != 'RES COMMON (000900)') or (
                    df_dis_permit['Use Code'][dparcel] != 'PLAT HEADI (H.)'):
                # Choose the largest damage category as this parcel's damage category:
                dcat = max(rcat)
                dcat_idx = rcat.index(dcat)
                df_dis_permit.at[dparcel, 'HAZUS Roof Damage Category'] = [dcat]
                df_dis_permit.at[dparcel, 'Percent Roof Cover Damage'] = \
                    df_dis_permit['Percent Roof Cover Damage'][dparcel][dcat_idx]
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
            except TypeError:  # Percent damage description is one value
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
    return df_dis_permits, data_details


def roof_square_damage_cat(total_area, stories, num_roof_squares, unit):
    try:
        total_area = float(total_area)
    except:
        total_area = float(total_area.replace(',', ''))
    if float(stories) == 0:
        stories = 1
    else:
        stories = float(stories)
    floor_area = total_area / stories
    if unit == 'ft':
        roof_square = 100  # sq_ft
    elif unit == 'm':
        roof_square = 100 / 10.764  # sq m
    roof_dpercent = 100 * (roof_square * num_roof_squares / floor_area)
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


def add_crowd_sourced_data(bldg, parcel_identifier, steer_file_path):
    pass


def add_fema_modeled_data(bldg, parcel_identifier, fema_modeled_file_path):
    pass


def add_fema_claims_data(bldg, parcel_identifier, fema_claims_file_path):
    pass


def add_rsensing_imagery_data(bldg, parcel_identifier, rsensing_imagery_file_path):
    pass