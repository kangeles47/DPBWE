import pandas as pd
import ast
import math


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
    damage_percent = 100*(roof_square*num_roof_squares/floor_area)
    # Determine damage category:
    if damage_percent <= 2:
        roof_dcat = 0
    elif 2 < damage_percent <= 15:
        roof_dcat = 1
    elif 15 < damage_percent <= 50:
        roof_dcat = 2
    elif damage_percent > 50:
        roof_dcat = 3
    else:
        roof_dcat = num_roof_squares
    return roof_dcat
# Load the parcel/permit data:
df = pd.read_csv('Bay_Parcels_Permits.csv')
# Start working through the Building Permits:
damage_cat = []
for p in range(0, len(df['Disaster Permit'])):
    permit_type = ast.literal_eval(df['Disaster Permit Type'][p])
    permit_desc = ast.literal_eval(df['Disaster Permit Description'][p])
    permit_cat = []
    for permit in range(0, len(permit_type)):
        if 'ROOF' in permit_type[permit]:
            # Conduct a loop to categorize all quantitative descriptions:
            damage_desc = permit_desc[permit].split()
            for i in range(0, len(damage_desc)):
                if damage_desc[i].isdigit():  # First check if the permit has a quantity for the damage
                    total_area = df['Square Footage'][p]
                    stories = df['Stories'][p]
                    num_roof_squares = int(damage_desc[i])
                    unit = 'ft'
                    roof_dcat = roof_square_damage_cat(total_area, stories, num_roof_squares, unit)
                    permit_cat.append(roof_dcat)
                    break
                else:
                    if 'SQ' in damage_desc[i]:  # Case when there is no space between quantity and roof SQ
                        total_area = df['Square Footage'][p]
                        stories = df['Stories'][p]
                        num_roof_squares = int(damage_desc[i][0:-2])  # Remove 'SQ' from description and extract value:
                        unit = 'ft'
                        roof_dcat = roof_square_damage_cat(total_area, stories, num_roof_squares, unit)
                        permit_cat.append(roof_dcat)
                        break
                    else:
                        pass
            # Add a dummy value for permits that have a qualitative description:
            if len(permit_cat) != permit + 1:
                permit_cat.append(0)
            else:
                pass
            # Conduct a second loop to now categorize qualitative descriptions:
            if permit_cat[permit] > 0:
                pass
            else:
                if 'RE-ROOF' in permit_desc[permit]:
                    permit_cat[permit] = 1
                elif 'REROOF' in permit_desc[permit]:
                    permit_cat[permit] = 1
                elif 'ROOF REPAIR' in permit_desc[permit]:
                    permit_cat[permit] = 1
                elif 'REPLACE' in permit_desc[permit]:
                    permit_cat[permit] = 2
                else:
                    print(permit_desc[permit])
        else:
            permit_cat.append(0)
    damage_cat.append(permit_cat)
# Integrate damage categories into the DataFrame and Roof Damage percentages:
df['HAZUS Damage Category'] = damage_cat
print('a')
