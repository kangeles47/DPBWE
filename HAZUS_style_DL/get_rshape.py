import pandas as pd
from random import choices, seed


def get_rshape(file_path, address_locality, building_type, number_of_stories, roof_cover):
    df = pd.read_csv(file_path)
    df_sub = df.loc[(df['address_locality'] == address_locality) & (df['building_type'] == building_type) & (
                df['number_of_stories'] == number_of_stories)]
    df_sub = df_sub.loc[(df_sub['roof_shape'] == 'Gable') | (df_sub['roof_shape'] == 'Hip')]
    if roof_cover.lower() == 'asphalt':
        samples = df_sub.loc[(df_sub['roof_cover'] == 'Asphalt shingles (laminated)') | (
                    df_sub['roof_cover'] == 'Asphalt shingles (3-tab)')]
    else:
        print('roof cover type not supported yet')
    rshape_options = []
    rshape_weights = []
    for u in samples['roof_shape'].unique():
        rshape_options.append(u)
        new_weight = len(samples.loc[samples['roof_shape'] == u])
        rshape_weights.append(new_weight)
    rshape_choice = choices(rshape_options, rshape_weights)[0]
    return rshape_choice

file_path = 'D:/Users/Karen/Documents/GitHub/DPBWE/Datasets/StEER/HM_D2D_Building.csv'
df_inventory = pd.read_csv('D:/Users/Karen/Documents/GitHub/DPBWE/MB_Building_Inventory_Default.csv')
roof_shapes = []
seed(101)
for idx in df_inventory.index.to_list():
    shape_choice = get_rshape(file_path, 'Mexico Beach', 'Single Family', 1, 'Asphalt')
    roof_shapes.append(shape_choice)
df_inventory['rshape'] = roof_shapes
df_inventory.to_csv('MB_Building_Inventory_Default.csv', index=False)