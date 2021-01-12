import pandas as pd
import ast
import matplotlib.pyplot as plt
import numpy as np
from query_parcel_info import query_parcel_info


# These sets of code are utilized in the construction of observation-informed
# fragilities for component-based damage assessment:
def build_fragility(aug_bldg_dataset, obsv_damage_type, wind_speed_file_path):
    df = pd.read_csv(aug_bldg_dataset)
    # Step 1: Find the site wind speed for each parcel:
    v_site = []
    for row in df.index:
        v_site.append(get_ARA_wind_speed(df['Lat'][row], df['Lon'][row], wind_speed_file_path))
    # Step 2: Damage occurrences at each wind speed:
    wind_speeds = np.arange(80, 180, 5)
    num_bldgs = []
    key_dict = {'roof_cover': 'Percent Roof Cover Damage'}
    for speed in wind_speeds:
        # This first set is noting what buildings experienced failure and which did not (global damage)
        # Grab the subset of the DataFrame with wind speeds < speed:
        df_subset = df.loc[df['Site Wind Speed'] <= speed]
        if len(df_subset['Parcel ID']) == 0:
            num_bldgs.append(0)
        else:
            bldg_count = 0
            for idx in df_subset.index:
                if df_subset[key_dict[obsv_damage_type]][idx][0] == 0:
                    pass
                else:
                    bldg_count = bldg_count + 1
            num_bldgs.append(bldg_count)
        # This second set is noting what buildings experienced a given percent failure for each wind speed:
        percent_failure = np.arange(0, 100, 1)
        for percent in percent_failure:
            pass

def create_aug_bldg_database(local_bldgs_path, steer_bldgs_path, obsv_damage_type, comm_flag, save_flag, find_parcel_flag, browser, url, steer_parcel_path):
    # Step 1: Convert .csv files into DataFrames for easier data manipulation:
    df_local = pd.read_csv(local_bldgs_path)
    df_steer = pd.read_csv(steer_bldgs_path)
    if find_parcel_flag:
        pass
    else:
        df_steer_parcel = pd.read_csv(steer_parcel_path)
    # Step 2: Populate observation-based damage assessment for local bldgs using permit data:
    df = get_permit_damage(df_local, obsv_damage_type)
    # Step 3: Integrate StEER data with updated local bldgs dataset:
    if comm_flag:
        # Eliminate any buildings non-engineered residential:
        sf_indices = df_steer.loc[df_steer['building_type'] == 'Single Family'].index
        df_steer = df_steer.drop(sf_indices)
    else:
        pass
    # Merge the StEER data with the augmented building dataset:
    for row in df_steer.index:
        if find_parcel_flag:
            # Query each parcel's data from the property appraiser website:
            address_flag = True
            parcel_identifier = df_steer['address'][row]
            parcel_info = query_parcel_info(browser, url, parcel_identifier, address_flag)
        else:
            # Access parcel data from the designated DataFrame:
            parcel_info = df_steer_parcel.iloc[row].to_dict()
        # Fill in remaining fields using StEER data:
        parcel_info['HAZUS Roof Damage Category'] = 'N/A'
        parcel_info['Percent Roof Cover Damage'] = df_steer['roof_cover_damage'][row]
        parcel_info['Lat'] = df_steer['latitude'][row]
        parcel_info['Lon'] = df_steer['longitude'][row]
        df = df.append(bldg_dict, ignore_index=True)
    if save_flag:
        df.to_csv('Augmented_Bldgs_Dataset.csv', index=False)
    else:
        pass
    return df


def get_permit_damage(df_local, obsv_damage_type):
    # Allocate empty lists to gather damage information:
    if obsv_damage_type == 'roof_cover':
        rcover_damage_cat = []
        rcover_damage_percent = []
    else:
        pass
    # Loop through the parcels:
    for p in range(0, len(df_local['Parcel ID'])):
        if obsv_damage_type == 'roof_cover':
            # First check if this building has a disaster permit:
            if not df_local['Disaster Permit'][p]:
                rcover_damage_cat.append([0])
                rcover_damage_percent.append([0])
            else:
                # First check if this building shares a parcel number:
                if df_local['Use Code'][p] != 'RES COMMON (000900)':
                    dup_parcel = df_local.loc[df_local['Parcel ID'] == df_local['Parcel ID'][p]]
                    dup_parcel_factor = dup_parcel['Square Footage'][p] / dup_parcel['Square Footage'].sum()
                else:
                    pass
                permit_type = ast.literal_eval(df_local['Disaster Permit Type'][p])
                permit_desc = ast.literal_eval(df_local['Disaster Permit Description'][p])
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
                                    total_area = df_local['Square Footage'][p]
                                    stories = df_local['Stories'][p]
                                    num_roof_squares = float(damage_desc[i]) * dup_parcel_factor
                                    unit = 'ft'
                                    roof_dcat, roof_dpercent = roof_square_damage_cat(total_area, stories, num_roof_squares,
                                                                              unit)
                                    permit_cat.append(roof_dcat)
                                    permit_dpercent.append(roof_dpercent)
                                    break
                                else:
                                    if 'SQ' in damage_desc[i]:  # Case when there is no space between quantity and roof SQ
                                        total_area = df_local['Square Footage'][p]
                                        stories = df_local['Stories'][p]
                                        num_roof_squares = float(damage_desc[i][
                                                         0:-2]) * dup_parcel_factor  # Remove 'SQ' from description and extract value:
                                        unit = 'ft'
                                        roof_dcat, roof_dpercent = roof_square_damage_cat(total_area, stories, num_roof_squares,
                                                                                  unit)
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
    return df_local

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


def get_ARA_wind_speed(latitude, longitude, wind_speed_file_path):
    df_wind_speeds = pd.read_excel(wind_speed_file_path)
    # Round the lat and lon values to two decimal places:
    df_wind_speeds['Lon'] = round(df_wind_speeds['Lon'], 2)
    df_wind_speeds['Lat'] = round(df_wind_speeds['Lat'], 2)
    # Use the parcel's geodesic location to determine its corresponding wind speed (interpolation):
    if np.sign(latitude) < 0:
        v1_idx = df_wind_speeds.loc[(df_wind_speeds['Lat'] == round(latitude, 2)) & (
                    df_wind_speeds['Lon'] < round(longitude, 2))].index[0]
        v2_idx = df_wind_speeds.loc[(df_wind_speeds['Lat'] == round(latitude, 2)) & (
                    df_wind_speeds['Lon'] > round(longitude, 2))].index[-1]
        # Now find the index of the two longitude values larger/smaller than parcel's longitude:
        v_site = np.interp(longitude, [df_wind_speeds['Lon'][v1_idx], df_wind_speeds['Lon'][v2_idx]],
                            [df_wind_speeds['Vg_mph'][v1_idx], df_wind_speeds['Vg_mph'][v2_idx]])
    else:
        v1_idx = df_wind_speeds.loc[(df_wind_speeds['Lat'] == round(latitude, 2)) & (
                    df_wind_speeds['Lon'] > round(longitude, 2))].index[0]
        v2_idx = df_wind_speeds.loc[(df_wind_speeds['Lat'] == round(latitude, 2)) & (
                    df_wind_speeds['Lon'] < round(longitude, 2))].index[-1]
        # Now find the index of the two longitude values larger/smaller than parcel's longitude:
        v_site = np.interp(longitude, [df_wind_speeds['Lon'][v1_idx], df_wind_speeds['Lon'][v2_idx]],
                            [df_wind_speeds['Vg_mph'][v1_idx], df_wind_speeds['Vg_mph'][v2_idx]])
    return v_site


# Load the parcel/permit data:
df = pd.read_csv('Bay_Parcels_Permits.csv')
# Start working through the Building Permits:
damage_cat = []
damage_percent = []
for p in range(0, len(df['Disaster Permit'])):
    # First check if this building shares a parcel number:
    if df['Use Code'][p] != 'RES COMMON (000900)':
        dup_parcel = df.loc[df['Parcel ID'] == df['Parcel ID'][p]]
        dup_parcel_factor = dup_parcel['Square Footage'][p] / dup_parcel['Square Footage'].sum()
    else:
        pass
    permit_type = ast.literal_eval(df['Disaster Permit Type'][p])
    permit_desc = ast.literal_eval(df['Disaster Permit Description'][p])
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
                        total_area = df['Square Footage'][p]
                        stories = df['Stories'][p]
                        num_roof_squares = float(damage_desc[i])*dup_parcel_factor
                        unit = 'ft'
                        roof_dcat, roof_dpercent = roof_square_damage_cat(total_area, stories, num_roof_squares, unit)
                        permit_cat.append(roof_dcat)
                        permit_dpercent.append(roof_dpercent)
                        break
                    else:
                        if 'SQ' in damage_desc[i]:  # Case when there is no space between quantity and roof SQ
                            total_area = df['Square Footage'][p]
                            stories = df['Stories'][p]
                            num_roof_squares = float(damage_desc[i][0:-2])*dup_parcel_factor  # Remove 'SQ' from description and extract value:
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
                    else:
                        print(permit_desc[permit])
        else:
            permit_cat.append(0)
            permit_dpercent.append(0)
    damage_cat.append(permit_cat)
    damage_percent.append(permit_dpercent)
# Integrate damage categories into the DataFrame and Roof Damage percentages:
df['HAZUS Roof Damage Category'] = damage_cat
df['Percent Roof Cover Damage'] = damage_percent
# Clean-up roof damage categories:
for dparcel in range(0, len(df['HAZUS Roof Damage Category'])):
    rcat = df['HAZUS Roof Damage Category'][dparcel]
    if len(rcat) == 1:
        pass
    else:
        if (df['Use Code'][dparcel] != 'RES COMMON (000900)') or (df['Use Code'][dparcel] != 'PLAT HEADI (H.)'):
            # Choose the largest damage category as this parcel's damage category:
            dcat = max(rcat)
            dcat_idx = rcat.index(dcat)
            df.at[dparcel, 'HAZUS Roof Damage Category'] = [dcat]
            df.at[dparcel, 'Percent Roof Cover Damage'] = df['Percent Roof Cover Damage'][dparcel][dcat_idx]
        else:
            pass
# Need to create a column of roof damage percentages
# Bring in ARA wind speeds:
df_wind_speeds = pd.read_excel('C:/Users/Karen/PycharmProjects/DPBWE/2018-Michael_windgrid_ver36.xlsx')
# Round the lat and lon values to two decimal places:
df_wind_speeds['Lon'] = round(df_wind_speeds['Lon'], 2)
df_wind_speeds['Lat'] = round(df_wind_speeds['Lat'], 2)
for parcel in df.index.to_list():
    cat = max(df['HAZUS Roof Damage Category'][parcel])
    # Use the parcel's geodesic location to determine its corresponding wind speed (interpolation):
    # Get the subsection of the DataFrame pertaining to values with lat = parcel lat:
    if np.sign(df['Latitude'][parcel]) < 0:
        v1_idx = df_wind_speeds.loc[(df_wind_speeds['Lat'] == round(df['Latitude'][parcel], 2)) & (df_wind_speeds['Lon'] < round(df['Longitude'][parcel], 2))].index[0]
        v2_idx = df_wind_speeds.loc[(df_wind_speeds['Lat'] == round(df['Latitude'][parcel], 2)) & (df_wind_speeds['Lon'] > round(df['Longitude'][parcel], 2))].index[-1]
        # Now find the index of the two longitude values larger/smaller than parcel's longitude:
        v_site = np.interp(df['Longitude'][parcel], [df_wind_speeds['Lon'][v1_idx], df_wind_speeds['Lon'][v2_idx]], [df_wind_speeds['Vg_mph'][v1_idx], df_wind_speeds['Vg_mph'][v2_idx]])
    else:
        v1_idx = df_wind_speeds.loc[(df_wind_speeds['Lat'] == round(df['Latitude'][parcel], 2)) & (df_wind_speeds['Lon'] > round(df['Longitude'][parcel], 2))].index[0]
        v2_idx = df_wind_speeds.loc[(df_wind_speeds['Lat'] == round(df['Latitude'][parcel], 2)) & (df_wind_speeds['Lon'] < round(df['Longitude'][parcel], 2))].index[-1]
        # Now find the index of the two longitude values larger/smaller than parcel's longitude:
        v_site = np.interp(df['Longitude'][parcel], [df_wind_speeds['Lon'][v1_idx], df_wind_speeds['Lon'][v2_idx]], [df_wind_speeds['Vg_mph'][v1_idx], df_wind_speeds['Vg_mph'][v2_idx]])
    plt.plot(cat, v_site)

# Lay out preliminary code to access the StEER Buildings:
# Read in the datafile:
steer_file_path = 'C:/Users/Karen/PycharmProjects/DPBWE/StEER/HM_D2D_Building.csv'
local_bldg_file_path = 'C:/Users/Karen/PycharmProjects/DPBWE/Geocode_Comm_Parcels.csv'
# Convert into .csv file into a DataFrame for easier manipulation:
df_steer = pd.read_csv(steer_file_path)
df_bldgs = pd.read_csv(local_bldg_file_path)
# Will need [latitude] and [longitude] to identify site wind speed:
# [project] == 'Hurricane Michael (2018)'
# Eliminate any buildings non-engineered residential:
sf_indices = df_steer.loc[df_steer['building_type'] == 'Single Family'].index
df_steer = df_steer.drop(sf_indices)
parcel_flag = False
# Merge the StEER data with the augmented building dataset:
# Parcel ID,Address,Use Code,Square Footage,Stories,Year Built,OccType,Exterior Walls,Roof Cover,Interior Walls,Frame Type,Floor Cover,Unit No.,Floor,Living Area,Number of Bedrooms,Number of Bathrooms,Condo Bldg,Permit Number,Disaster Permit,Disaster Permit Type,Disaster Permit Description
for row in df_steer:
    # Idea here: modify the parcel_query script so that it will look up specific addresses
    parcel_id = 'Lookup needed'
    address = df_steer['address_full'][row]
    use_code = 'Lookup needed'
    area = 'Lookup needed'
    num_stories = 'Lookup needed'
    yr_built = 'Lookup needed'
    occ_type = 'Lookup needed'
    ext_walls = 'Lookup needed'
    if parcel_flag:
        roof_cover = df_steer['roof_cover'][row]
    else:
        roof_cover = 'Lookup needed'
    int_walls = 'Lookup needed'
    frame_type = 'Lookup needed'
    floor_cover = 'Lookup needed'
    unit_no = 'Lookup needed'
    floor_num = 'Lookup needed'
    living_area = 'Lookup needed'
    num_bedrooms = 'Lookup needed'
    num_bathrooms = 'Lookup needed'
    condo_bldg = 'Lookup needed'
    permit_num = 'Lookup needed'
    dis_permit = 'Lookup needed'
    dis_permit_type = 'Lookup needed'
    dis_permit_desc = 'Lookup needed'
    hazus_rdamage_cat = 'Lookup needed'
    percent_rdamage = df_steer['roof_cover_damage'][row]
    latitude = df_steer['latitude'][row]
    longitude = df_steer['longitude'][row]
    bldg_dict = {'Parcel ID': parcel_id, 'Address': address, 'Use Code': use_code,'Square Footage': area, 'Stories': num_stories,
                 'Year Built': yr_built, 'OccType': occ_type, 'Exterior Walls': ext_walls, 'Roof Cover': roof_cover, 'Interior Walls': int_walls,
                 'Frame Type': frame_type, 'Floor Cover': floor_cover,'Unit No.': unit_no,'Floor': floor_num,'Living Area': living_area,
                 'Number of Bedrooms': num_bedrooms, 'Number of Bathrooms': num_bathrooms, 'Condo Bldg': condo_bldg, 'Permit Number': permit_num,
                 'Disaster Permit': dis_permit, 'Disaster Permit Type': dis_permit_type, 'Disaster Permit Description': dis_permit_desc,
                 'HAZUS Roof Damage Category': hazus_rdamage_cat, 'Percent Roof Cover Damage': percent_rdamage, 'Latitude': latitude, 'Longitude': longitude}
    df_bldgs = df_bldgs.append(bldg_dict, ignore_index=True)