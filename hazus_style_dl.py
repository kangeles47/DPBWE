# import helpful packages for numerical analysis
import sys

import numpy as np

import pandas as pd
idx = pd.IndexSlice
pd.options.display.max_rows = 30

import pprint

# and for plotting
# from plotly import graph_objects as go
# from plotly.subplots import make_subplots
# import plotly.express as px

# and import pelicun classes and methods
from pelicun.base import set_options, convert_to_MultiIndex
from pelicun.assessment import Assessment

from WindWSFRulesets import wsf_config
from WindWMUHRulesets import wmuh_config

# Create sample BIM dictionaries just to get the workflow running:
wsf_bim = {'year_built': 2002, 'roof_shape': 'gable', 'hvhz': False, 'roof_slope': 2/12, 'avg_jan_temp': 'above',
           'V_ult': 132, 'HPR': True, 'garage_tag': -1, 'stories': 1, 'terrain': 3, 'WBD': True}
bldg_config = wsf_config(wsf_bim)
a=0

# Step 1: Initialize a pelicun Assessment
sample_size = 1000
PAL = Assessment({
    "PrintLog": True,
    "Seed": 415,
    "NonDirectionalMultipliers": {'ALL': 1.0}})

# Step 2: Define the demand:
wind_speed = 150
# Define the demand distribution:
raw_demand = pd.DataFrame({'Units': ['mph'], 1: wind_speed}, index=['PWS-1-1']).T
# Load the demand into the Assessment object:
PAL.demand.load_sample(raw_demand)
# Resample to get the desired amount of realizations:
# Using empirical here to sample with replacement: (?)
PAL.demand.calibrate_model({'ALL': {'DistributionFamily': 'empirical'}})
# Generate the demand samples:
PAL.demand.generate_sample({'SampleSize': sample_size})
# Show the demand sample:
PAL.demand.save_sample().describe()

# Step 3: Asset Description
cmp_marginals = pd.DataFrame({'Units': 'ea', 'Location': 1, 'Direction': 1, 'Theta_0': 1, 'Blocks': 1},
                             index=['W.SF.1.gab.0.6d.strap.no.1.70'])
print(cmp_marginals)
# Load the model:
PAL.asset.load_cmp_model({'marginals': cmp_marginals})
# Generate the component quantity samples (in this case identical):
PAL.asset.generate_cmp_sample(sample_size)
# Show to component quantity samples:
PAL.asset.save_cmp_sample().describe()

# Step 4: Damage Model and Assessment:
PAL.damage.load_damage_model(['PelicunDefault/fragility_DB_SimCenter_HAZUS_HU.csv',])
# Check the parameters assigned to the components (defaults):
PAL.damage.damage_params.T.dropna()
# Run the damage calculation:
PAL.damage.calculate()  # originally had fed in sample_size here
# Show the results:
dmg_sample = PAL.damage.save_sample()
print(dmg_sample.describe())

# Step 5: Loss ratios:
# In the following line, we tell pelicun that we are using damage as the way to get the associated loss ratio:
drivers = [f'DMG-{cmp}' for cmp in cmp_marginals.index.unique()]
# Loss models are chosen according to their respective building archetype:
loss_models = cmp_marginals.index.unique()
# Assemble a DataFrame with the mapping information:
loss_map = pd.DataFrame(loss_models, columns=['BldgRepair'], index=drivers)
print(loss_map)
# Load hurricane loss model and map to pelicun:
PAL.bldg_repair.load_model(['PelicunDefault/bldg_repair_DB_SimCenter_HAZUS_HU.csv',], loss_map)
# Check the parameters assigned to the component:
print(PAL.bldg_repair.loss_params.T)
# Run the calculation:
PAL.bldg_repair.calculate(sample_size)
# Show the results:
loss_sample = PAL.bldg_repair.save_sample()
print(loss_sample)

# BIM = dict(
#     occupancy_class=str(oc),
#     bldg_type=BIM_in['BuildingType'],
#     year_built=int(yearbuilt),
#     # double check with Tracey for format - (NumberStories0 is 4-digit code)
#     # (NumberStories1 is image-processed story number)
#     stories=int(nstories),
#     area=float(area),
#     flood_zone=floodzone_fema,
#     V_ult=float(BIM_in['DesignWindSpeed']),
#     avg_jan_temp=ap_ajt[BIM_in.get('AverageJanuaryTemperature', 'Below')],
#     roof_shape=ap_RoofType[BIM_in['RoofShape']],
#     roof_slope=float(BIM_in.get('RoofSlope', 0.25)),  # default 0.25
#     sheathing_t=float(BIM_in.get('SheathingThick', 1.0)),  # default 1.0
#     roof_system=str(ap_RoofSyste[roof_system]),  # only valid for masonry structures
#     garage_tag=float(BIM_in.get('Garage', -1.0)),
#     lulc=BIM_in.get('LULC', -1),
#     z0=float(BIM_in.get('RoughnessLength', -1)),  # if the z0 is already in the input file
#     Terrain=BIM_in.get('Terrain', -1),
#     mean_roof_height=float(BIM_in.get('MeanRoofHeight', 15.0)),  # default 15
#     design_level=str(ap_DesignLevel[design_level]),  # default engineered
#     no_units=int(nunits),
#     window_area=float(BIM_in.get('WindowArea', 0.20)),
#     first_floor_ht1=float(BIM_in.get('FirstFloorHeight', 10.0)),
#     split_level=bool(ap_SplitLevel[BIM_in.get('SplitLevel', 0)]),  # dfault: no
#     fdtn_type=int(foundation),  # default: pile
#     city=BIM_in.get('City', 'NA'),
#     wind_zone=str(BIM_in.get('WindZone', 'I'))
# )

# # Hurricane-Prone Region (HPR)
# # Areas vulnerable to hurricane, defined as the U.S. Atlantic Ocean and
# # Gulf of Mexico coasts where the ultimate design wind speed, V_ult is
# # greater than a pre-defined limit.
# if wsf_bim['year_built'] >= 2016:
#     # The limit is 115 mph in IRC 2015
#     HPR = wsf_bim['V_ult'] > 115.0
# else:
#     # The limit is 90 mph in IRC 2009 and earlier versions
#     HPR = wsf_bim['V_ult'] > 90.0
#
# # Wind Borne Debris
# # Areas within hurricane-prone regions are affected by debris if one of
# # the following two conditions holds:
# # (1) Within 1 mile (1.61 km) of the coastal mean high water line where
# # the ultimate design wind speed is greater than flood_lim.
# # (2) In areas where the ultimate design wind speed is greater than
# # general_lim
# # The flood_lim and general_lim limits depend on the year of construction
# if BIM['year_built'] >= 2016:
#     # In IRC 2015:
#     flood_lim = 130.0  # mph
#     general_lim = 140.0  # mph
# else:
#     # In IRC 2009 and earlier versions
#     flood_lim = 110.0  # mph
#     general_lim = 120.0  # mph
# # Areas within hurricane-prone regions located in accordance with
# # one of the following:
# # (1) Within 1 mile (1.61 km) of the coastal mean high water line
# # where the ultimate design wind speed is 130 mph (58m/s) or greater.
# # (2) In areas where the ultimate design wind speed is 140 mph (63.5m/s)
# # or greater. (Definitions: Chapter 2, 2015 NJ Residential Code)
# if not HPR:
#     WBD = False
# else:
#     WBD = ((((BIM['flood_zone'] >= 6101) and (BIM['flood_zone'] <= 6109)) and
#             BIM['V_ult'] >= flood_lim) or (BIM['V_ult'] >= general_lim))
#
# # Terrain
# # open (0.03) = 3
# # light suburban (0.15) = 15
# # suburban (0.35) = 35
# # light trees (0.70) = 70
# # trees (1.00) = 100
# # Mapped to Land Use Categories in NJ (see https://www.state.nj.us/dep/gis/
# # digidownload/metadata/lulc02/anderson2002.html) by T. Wu group
# # (see internal report on roughness calculations, Table 4).
# # These are mapped to Hazus defintions as follows:
# # Open Water (5400s) with zo=0.01 and barren land (7600) with zo=0.04 assume Open
# # Open Space Developed, Low Intensity Developed, Medium Intensity Developed
# # (1110-1140) assumed zo=0.35-0.4 assume Suburban
# # High Intensity Developed (1600) with zo=0.6 assume Lt. Tree
# # Forests of all classes (4100-4300) assumed zo=0.6 assume Lt. Tree
# # Shrub (4400) with zo=0.06 assume Open
# # Grasslands, pastures and agricultural areas (2000 series) with
# # zo=0.1-0.15 assume Lt. Suburban
# # Woody Wetlands (6250) with zo=0.3 assume suburban
# # Emergent Herbaceous Wetlands (6240) with zo=0.03 assume Open
# # Note: HAZUS category of trees (1.00) does not apply to any LU/LC in NJ
# terrain = 15  # Default in Reorganized Rulesets - WIND
# if (BIM['z0'] > 0):
#     terrain = int(100 * BIM['z0'])
# elif (BIM['lulc'] > 0):
#     if (BIM['flood_zone'].startswith('V') or BIM['flood_zone'] in ['A', 'AE', 'A1-30', 'AR', 'A99']):
#         terrain = 3
#     elif ((BIM['lulc'] >= 5000) and (BIM['lulc'] <= 5999)):
#         terrain = 3  # Open
#     elif ((BIM['lulc'] == 4400) or (BIM['lulc'] == 6240)) or (BIM['lulc'] == 7600):
#         terrain = 3  # Open
#     elif ((BIM['lulc'] >= 2000) and (BIM['lulc'] <= 2999)):
#         terrain = 15  # Light suburban
#     elif ((BIM['lulc'] >= 1110) and (BIM['lulc'] <= 1140)) or ((BIM['lulc'] >= 6250) and (BIM['lulc'] <= 6252)):
#         terrain = 35  # Suburban
#     elif ((BIM['lulc'] >= 4100) and (BIM['lulc'] <= 4300)) or (BIM['lulc'] == 1600):
#         terrain = 70  # light trees
# elif (BIM['Terrain'] > 0):
#     if (BIM['flood_zone'].startswith('V') or BIM['flood_zone'] in ['A', 'AE', 'A1-30', 'AR', 'A99']):
#         terrain = 3
#     elif ((BIM['Terrain'] >= 50) and (BIM['Terrain'] <= 59)):
#         terrain = 3  # Open
#     elif ((BIM['Terrain'] == 44) or (BIM['Terrain'] == 62)) or (BIM['Terrain'] == 76):
#         terrain = 3  # Open
#     elif ((BIM['Terrain'] >= 20) and (BIM['Terrain'] <= 29)):
#         terrain = 15  # Light suburban
#     elif (BIM['Terrain'] == 11) or (BIM['Terrain'] == 61):
#         terrain = 35  # Suburban
#     elif ((BIM['Terrain'] >= 41) and (BIM['Terrain'] <= 43)) or (BIM['Terrain'] in [16, 17]):
#         terrain = 70  # light trees
#
# BIM.update(dict(
#     # Nominal Design Wind Speed
#     # Former term was “Basic Wind Speed”; it is now the “Nominal Design
#     # Wind Speed (V_asd). Unit: mph."
#     V_asd=np.sqrt(0.6 * BIM['V_ult']),