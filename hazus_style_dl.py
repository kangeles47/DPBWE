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
archetypes = ['W.MUH.1.gab.null.null.1.6d.tnail.0.35', 'W.MUH.1.gab.null.null.1.6d.tnail.0.35', 'W.MUH.2.gab.null.null.1.8d.tnail.0.35', 'W.MUH.2.gab.null.null.1.8d.tnail.0.35', 'W.MUH.2.gab.null.null.1.8d.tnail.0.35', 'W.MUH.1.gab.null.null.1.8d.tnail.0.35', 'W.SF.1.hip.0.8d.tnail.no.0.15']
unique_archetypes = []
for a in archetypes:
    if a not in unique_archetypes:
        unique_archetypes.append(a)
cmp_marginals = pd.DataFrame(index=unique_archetypes, columns=['Units', 'Location', 'Direction', 'Theta_0'])
# Set up values for simple run through:
simple_vals = ['ea', 1, 1, 1]
for col in enumerate(cmp_marginals.columns):
    cmp_marginals[col[1]] = simple_vals[col[0]]
# cmp_marginals = pd.DataFrame({'Units': 'ea', 'Location': 1, 'Direction': 1, 'Theta_0': 1, 'Blocks': 1},
#                               index=['W.SF.1.gab.0.6d.strap.no.1.70'])
print(cmp_marginals)
# Load the model:
PAL.asset.load_cmp_model({'marginals': cmp_marginals})  # Note: make sure that you are not duplicating component types
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
# Note to self here: check pelicun/model --> Lines 119-122 --> work around implemented for loss ratio unit
# Check the parameters assigned to the component:
print(PAL.bldg_repair.loss_params.T)
# Run the calculation:
PAL.bldg_repair.calculate()
# Show the results:
loss_sample = PAL.bldg_repair.save_sample()
print(loss_sample.describe())