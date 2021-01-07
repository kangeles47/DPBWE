import pandas as pd
import ast
import math
import matplotlib.pyplot as plt
import numpy as np


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
df['Percent Roof Damage'] = damage_percent
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
            df.at[dparcel, 'Percent Roof Damage'] = df['Percent Roof Damage'][dparcel][dcat_idx]
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