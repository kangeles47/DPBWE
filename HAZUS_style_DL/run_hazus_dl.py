import pandas as pd
from HAZUS_style_DL.WindMetaVarRulesets import get_meta_var
from HAZUS_style_DL.WindClassRulesets import building_class
from HAZUS_style_DL.WindWSFRulesets import wsf_config
from HAZUS_style_DL.WindWMUHRulesets import wmuh_config

file_path = 'D:/Users/Karen/Documents/Github/DPBWE/Asset_Description_PC_FL.csv'
column_names = ['id', 'Latitude', 'Longitude', 'BldgID', 'Address', 'City', 'county',
                'State', 'occupancy_class', 'frame_type', 'year_built',
                'stories', 'NoUnits', 'PlanArea', 'flood_zone', 'V_ult', 'lulc', 'WindZone', 'AvgJanTemp', 'roof_shape',
                'roof_slope', 'RoofCover', 'RoofSystem', 'MeanRoofHt', 'WindowArea', 'garage_tag',
                'HazusClassW', 'AnalysisDefault', 'AnalysisAdopted', 'Modifications',
                'z0', 'structureType', 'replacementCost', 'Footprint',
                'HazardProneRegion', 'WindBorneDebris', 'SecondaryWaterResistance',
                'RoofQuality', 'RoofDeckAttachmentW', 'Shutters', 'TerrainRoughness']
df_inventory = pd.read_csv(file_path, names=column_names, header=0)
# Cleaning up some data types:
df_inventory['year_built'].apply(int)
df_inventory['lulc'].apply(int)
df_inventory['roof_shape'] = df_inventory['roof_shape'].str.lower()
# Replacing roof shape names to SimCenter naming convention:
df_inventory['roof_shape'] = df_inventory['roof_shape'].replace(['flat'], 'flt')
df_inventory['roof_shape'] = df_inventory['roof_shape'].replace(['gable'], 'gab')
# Find the HAZUS archetype for each building in the given inventory:
hazus_archetypes = []
for idx in df_inventory.index.to_list():
    BIM = df_inventory.iloc[idx].to_dict()
    # Set up additional meta-variables:
    BIM = get_meta_var(BIM)
    # Identify HAZUS building class:
    bldg_class = building_class(BIM)
    # Using HAZUS building class, find the remaining archetype variables:
    if bldg_class == 'WSF':
        bldg_config = wsf_config(BIM)
    elif bldg_class == 'WMUH':
        bldg_config = wmuh_config(BIM)
    else:
        bldg_config = 'NONE'
        # try:
        #     print('Rulesets for this building class not yet defined: ' + bldg_class)
        # except TypeError:
        #     bldg_class = 'NONE'
    if bldg_config != 'NONE':
        hazus_archetypes.append(bldg_config)
    else:
        pass
print(hazus_archetypes)
