import pandas as pd
import matplotlib.pyplot as plt
import pelicun
from HAZUS_style_DL.run_hazus_dl import inventory_data_clean, get_hazus_archetype


# 1) Asset Description:
column_names = ['parcel_id', 'address', 'occupancy_class', 'square_footage', 'stories', 'year_built', 'exterior_walls',
                'roof_cover', 'interior_walls', 'frame_type', 'floor_cover', 'permit_number', 'permit_issue_date',
                'permit_type', 'permit_description', 'permit_amount', 'latitude', 'longitude', 'roof_shape', 'lulc',
                'V_ult', 'county']
# Note: V_ult is designated considering year_built for each parcel.
# We use V_ult = 133 for year_built > 2010
# We use basic wind speed = 129 mph for year_built <= 2010 --> V_ult = 129/sqrt(0.6)
                # ['Latitude', 'Longitude', 'BldgID', 'Address', 'City', 'county',
                # 'State', 'occupancy_class', 'frame_type', 'year_built',
                # 'stories', 'NoUnits', 'PlanArea', 'flood_zone', 'V_ult', 'lulc', 'WindZone', 'AvgJanTemp', 'roof_shape',
                # 'roof_slope', 'RoofCover', 'RoofSystem', 'MeanRoofHt', 'window_area', 'garage_tag',
                # 'HazusClassW', 'AnalysisDefault', 'AnalysisAdopted', 'Modifications',
                # 'z0', 'structureType', 'replacementCost', 'Footprint',
                # 'HazardProneRegion', 'WindBorneDebris', 'SecondaryWaterResistance',
                # 'RoofQuality', 'RoofDeckAttachmentW', 'Shutters', 'TerrainRoughness']
df_inventory = pd.read_csv('D:/Users/Karen/Documents/Github/DPBWE/MB_shingle_samples.csv', names=column_names, header=0)
# Clean up data types if needed:
df_inventory = inventory_data_clean(df_inventory)
# 2) Asset Representation (HAZUS archetypes):
hazus_archetypes = []
for idx in df_inventory.index.to_list():
    BIM = df_inventory.iloc[idx].to_dict()
    bldg_config = get_hazus_archetype(BIM)
    hazus_archetypes.append(bldg_config)
# Add to DataFrame for reference
df_inventory['HAZUS_archetype'] = hazus_archetypes
# Use HAZUS archetype list to figure out what fragilities are needed:
print(df_inventory['HAZUS_archetype'].unique())

# 3) Demand
# Need to figure out how to input unique demand for each building under consideration:
# Refer to Hurricane Laura example in the Live Expert tips video

# 4) Component fragilities:
# Need to feed in HAZUS fragilities for roof cover into pelicun:
# Going to need some sort of mapping mechanism to match archetypes to fragilities

# 5) Damage assessment:

# 6) Loss assessment:


# 7) Output results for plotting, summary tables:
