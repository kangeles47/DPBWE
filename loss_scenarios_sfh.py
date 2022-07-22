import pandas as pd
import matplotlib.pyplot as plt
import pelicun
from HAZUS_style_DL.run_hazus_dl import inventory_data_clean, get_hazus_archetype


# 1) Asset Description:
df_inventory = pd.read_csv('D:/Users/Karen/Downloads/MB_res_clean.csv')
df_inventory = inventory_data_clean(df_inventory)

# 2) Asset Representation (HAZUS archetypes):
hazus_archetypes = []
for idx in df_inventory.index.to_list():
    BIM = df_inventory.iloc[idx].to_dict()
    bldg_config = get_hazus_archetype(BIM)
    hazus_archetypes.append(bldg_config)
# Add to DataFrame for reference
df_inventory['HAZUS_archetype'] = hazus_archetypes

# 3) Hazard 
