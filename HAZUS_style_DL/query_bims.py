import json
import pandas as pd


def query_bim(file_name):
    # Opening JSON file
    f = open(file_name)

    # returns JSON object as
    # a dictionary
    data = json.load(f)

    # Query Hazus archetype:
    bldg_config = list(data['DamageAndLoss']['Components'].keys())[0]

    # Closing file
    f.close()

    return bldg_config


dir_path = 'D:/Users/Karen/Documents/R2D/LocalWorkDir/tmp.SimCenter/Results/'
config_list = []
for i in range(1, 2073):
    bim_name = str(i) + '-BIM_ap.json'
    bldg_config = query_bim(dir_path + str(i) + '/' + bim_name)
    config_list.append(bldg_config)
df = pd.read_csv('D:/Users/Karen/Documents/GitHub/DPBWE/HAZUS_style_DL/PCB_Building_Inventory_default.csv')
df['HazusGBM'] = config_list
df.to_csv('D:/Users/Karen/Documents/GitHub/DPBWE/HAZUS_style_DL/PCB_Building_Inventory_default.csv', index=False)
a = 0
df1 = pd.read_csv('D:/Users/Karen/Documents/R2D/LocalWorkDir/tmp.SimCenter/Results/1/BIM.csv')
for i in range(2, 2073):
    df2 = pd.read_csv('D:/Users/Karen/Documents/R2D/LocalWorkDir/tmp.SimCenter/Results/' + str(i) + '/BIM.csv')
    df1 = pd.concat([df1, df2])
df1.to_csv('D:/Users/Karen/Documents/GitHub/DPBWE/HAZUS_style_DL/PCB_Default_Full.csv', index=False)