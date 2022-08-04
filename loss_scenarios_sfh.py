import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pelicun.assessment import Assessment
from HAZUS_style_DL.run_hazus_dl import inventory_data_clean, get_hazus_archetype


def get_wind_speed(bldg_lon, bldg_lat, wind_speed_file_path, exposure, unit):
    df_wind_speeds = pd.read_csv(wind_speed_file_path)
    # Round the lat and lon values to two decimal places:
    df_wind_speeds['Lon'] = round(df_wind_speeds['Lon'], 2)
    df_wind_speeds['Lat'] = round(df_wind_speeds['Lat'], 2)
    # Use the parcel's geodesic location to determine its corresponding wind speed (interpolation):
    if np.sign(bldg_lat) < 0:
        v1_idx = df_wind_speeds.loc[(df_wind_speeds['Lat'] == round(bldg_lat, 2)) & (
                df_wind_speeds['Lon'] < round(bldg_lon, 2))].index[0]
        v2_idx = df_wind_speeds.loc[(df_wind_speeds['Lat'] == round(bldg_lat, 2)) & (
                df_wind_speeds['Lon'] > round(bldg_lon, 2))].index[-1]
        # Now find the index of the two longitude values larger/smaller than parcel's longitude:
        v_basic = np.interp(bldg_lon, [df_wind_speeds['Lon'][v1_idx], df_wind_speeds['Lon'][v2_idx]],
                            [df_wind_speeds['Vg_mph'][v1_idx], df_wind_speeds['Vg_mph'][v2_idx]])
    else:
        # Check first if there is a datapoint with lat, lon of parcel rounded two 2 decimal places:
        try:
            v_idx = df_wind_speeds.loc[(df_wind_speeds['Lat'] == round(bldg_lat, 2)) & (
                    df_wind_speeds['Lon'] == round(bldg_lon, 2))].index[0]
        except IndexError:
            # Choose the wind speed based off of the closest lat, lon coordinate:
            lat_idx = df_wind_speeds.loc[df_wind_speeds['Lat'] == round(bldg_lat, 2)].index.to_list()
            new_series = abs(bldg_lon - df_wind_speeds['Lon'][lat_idx])
            v_idx = new_series.idxmin()
        v_basic = df_wind_speeds['Vg_mph'][v_idx]
    if unit == 'metric':
        v_basic = v_basic*2.237
        ref_height = 10
        zg_c = 274.32
    else:
        ref_height = 33
        zg_c = 900
    # Populate the remaining parameters for exposure C:
    alpha_c = 9.5
    # Calculate the local wind speed at height z given the exposure category:
    if exposure == 'C':
        v_local = v_basic
        # An adjustment for height is all that is needed:
        #v_local = v_basic*(z/ref_height)**(1/alpha_c)
    else:
        # Power law - calculate the wind speed at gradient height for exposure C:
        v_gradient = v_basic / ((ref_height / zg_c) ** (1 / alpha_c))
        if exposure == 'B':
            alpha = 7.0
            if unit == 'metric':
                zg = 365.76
            else:
                zg = 1200
        elif exposure == 'D':
            alpha = 11.5
            if unit == 'metric':
                zg = 213.35
            else:
                zg = 900
        # Calculate the wind speed for the specified exposure, at its reference height:
        v_new = v_gradient*((ref_height/zg)**(1/alpha))
        v_local = v_new
        #f z != ref_height:
         #   # Adjust for roof height:
          #  v_local = v_new*((z/ref_height)**(1/alpha))
        #else:
         #   v_local = v_new
    return round(v_local)

# 1) Asset Description:
# column_names = ['parcel_id', 'address', 'occupancy_class', 'square_footage', 'stories', 'year_built', 'exterior_walls',
#                 'roof_cover', 'interior_walls', 'frame_type', 'floor_cover', 'permit_number', 'permit_issue_date',
#                 'permit_type', 'permit_description', 'permit_amount', 'latitude', 'longitude', 'roof_shape', 'lulc',
#                 'V_ult', 'county', 'flood_zone', 'garage_tag', 'roof_slope', 'avg_jan_temp']
# Note: V_ult is designated considering year_built for each parcel.
# We use V_ult = 133 for year_built > 2010
# We use basic wind speed = 129 mph for year_built <= 2010 --> V_ult = 129/sqrt(0.6)
# Note: Flood zone will need to be verified, particularly for parcels with year_built >= 2007
# Assuming no attached garage for all parcels given that difficult to discern from parcel data alone and does not affect
# roof cover performance
# Roof slope designation is based off of minimum slope for asphalt shingles in the Bay County: 2:12 slope
# We could also randomly sample values between 2:12 and 4:12 to assign swr? Not important to roof cover performance?
# Review garage-informed shutter designations with Tracy.

# Will affect final building loss ratio. Discuss with Tracy.
# Food for thought: BUILDING loss ratios in HAZUS --> would require multiplying final loss ration by whatever % we deem
# the roof cover to account for?
# As long as I apply logic to quantify losses in the same way for all approaches, I can at least get a relative idea of
# the effects of changing stuff in the workflow...
                # ['Latitude', 'Longitude', 'BldgID', 'Address', 'City', 'county',
                # 'State', 'occupancy_class', 'frame_type', 'year_built',
                # 'stories', 'NoUnits', 'PlanArea', 'flood_zone', 'V_ult', 'lulc', 'WindZone', 'AvgJanTemp', 'roof_shape',
                # 'roof_slope', 'RoofCover', 'RoofSystem', 'MeanRoofHt', 'window_area', 'garage_tag',
                # 'HazusClassW', 'AnalysisDefault', 'AnalysisAdopted', 'Modifications',
                # 'z0', 'structureType', 'replacementCost', 'Footprint',
                # 'HazardProneRegion', 'WindBorneDebris', 'SecondaryWaterResistance',
                # 'RoofQuality', 'RoofDeckAttachmentW', 'Shutters', 'TerrainRoughness']
df_inventory = pd.read_csv('D:/Users/Karen/Documents/Github/DPBWE/MB_shingle_samples.csv', keep_default_na=False)
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

# 3) pelicun assessment:
# 3a) Initialize assessment:
sample_size = 1000
PAL = Assessment({
    "PrintLog": True,
    "Seed": 415,
    "NonDirectionalMultipliers": {'ALL': 1.0}})
# 3b) Set up asset representation:
cmp_marginals = pd.DataFrame(index=hazus_archetypes, columns=['Units', 'Location', 'Direction', 'Theta_0'])
cmp_marginals['Units'] = 'ea'
cmp_marginals['Location'] = df_inventory.index.to_list()
cmp_marginals['Direction'] = 1
cmp_marginals['Theta_0'] = 1
PAL.asset.load_cmp_model({'marginals': cmp_marginals})

# Generate the component quantity samples (in this case identical):
PAL.asset.generate_cmp_sample(sample_size)
# Show to component quantity samples:
PAL.asset.save_cmp_sample().describe()

# Step 3: Define the demand:
wind_speed_file_path = 'D:/Users/Karen/Documents/Github/DPBWE/Datasets/WindFields/2018-Michael_windgrid_ver36.csv'
exposure = 'C'
unit = 'mph'
idx_list = []
wind_speed_list = []
for bldg in df_inventory.index.to_list():
    idx_list.append('PWS-' + str(bldg) + '-1')
    wind_speed = get_wind_speed(df_inventory['longitude'][bldg], df_inventory['latitude'][bldg], wind_speed_file_path, exposure, unit)
    wind_speed_list.append(wind_speed)
# Define the demand distribution:
raw_demand = pd.DataFrame({'Units': ['mph'], 'Theta_0': wind_speed_list}, index=idx_list).T
# Load the demand into the Assessment object:
PAL.demand.load_sample(raw_demand)
# Resample to get the desired amount of realizations:
# Using empirical here to sample with replacement: (?)
PAL.demand.calibrate_model({'ALL': {'DistributionFamily': 'empirical'}})
# Generate the demand samples:
PAL.demand.generate_sample({'SampleSize': sample_size})
# Show the demand sample:
PAL.demand.save_sample().describe()

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
# Length of loss sample is = sample_size
# Each index, e.g., loss_sample.iloc[0] summarizes D/L values for that realization
# Aggregate losses per realization in sample_size:
PAL.bldg_repair.aggregate_losses()
# Summary of results:
# Can access specific archetype by: loss_sample['COST'][archetype]
# archetype grouped by location --> .groupby('loc', axis=1): locs per damage state, all realizations

print(loss_sample.groupby(['loc'], axis=1).sum())  # loss ratio per realization per location (across ds)
# Uncomment to see summary statistics per location, all realizations (segmented by damage state):
df_mean_loc = loss_sample.groupby(['loc'], axis=1).sum().describe()
# Can access location-specific mean: df_mean_los['0']

# 4) Component fragilities:
# Need to feed in HAZUS fragilities for roof cover into pelicun:
# Going to need some sort of mapping mechanism to match archetypes to fragilities

# 5) Damage assessment:

# 6) Loss assessment:


# 7) Output results for plotting, summary tables:
