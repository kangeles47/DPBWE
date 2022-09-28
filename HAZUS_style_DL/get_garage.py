import pandas as pd
from random import choices, seed


def get_garage(year_built, file_path, state, num_stories):
    df_recs = pd.read_csv(file_path)
    # Goal: Get set of buildings to conduct weighted sampling:
    # Identify the census division this building is in:
    if state == 'FL':
        division = 'South Atlantic'
    else:
        print('Add rulesets for this state')
    # Identify the era of construction this building is in:
    if year_built < 1950:
        year_range = 1
    elif 1950 <= year_built < 1960:
        year_range = 2
    elif 1960 <= year_built < 1970:
        year_range = 3
    elif 1970 <= year_built < 1980:
        year_range = 4
    elif 1980 <= year_built < 1990:
        year_range = 5
    elif 1990 <= year_built < 2000:
        year_range = 6
    elif 2000 <= year_built < 2010:
        year_range = 7
    elif 2010 <= year_built < 2016:
        year_range = 8
    elif 2016 <= year_built < 2021:
        year_range = 9
    # Query samples
    samples = df_recs.loc[(df_recs['DIVISION']==division) & (df_recs['state_postal']==state) & (df_recs['STORIES']==num_stories) & (df_recs['YEARMADERANGE']==year_range)]
    if len(samples) > 0:
        garage_options = []
        garage_weights = []
        for u in samples['PRKGPLC1'].unique():
            garage_options.append(u)
            new_weight = len(samples.loc[samples['PRKGPLC1']==u])
            garage_weights.append(new_weight)
        garage_choice = int(choices(garage_options, garage_weights)[0])
    else:
        garage_choice = 0
        print(year_range)
    return garage_choice


file_path = 'D:/Users/Karen/Documents/GitHub/DPBWE/Datasets/RECS/recs2020_public_v1.csv'
df_inventory = pd.read_csv('D:/Users/Karen/Documents/GitHub/DPBWE/HAZUS_style_DL/PCB_Building_Inventory.csv')
garage_recs = []
seed(101)
for idx in df_inventory.index.to_list():
    garage_choice = get_garage(df_inventory['YearBuilt'][idx], file_path, 'FL', df_inventory['NumberOfStories'][idx])
    garage_recs.append(garage_choice)
df_inventory['garage_recs'] = garage_recs
df_inventory.to_csv('PCB_Building_Inventory.csv', index=False)
