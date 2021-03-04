import pandas as pd
import numpy as np
import get_sim_bldgs
import post_disaster_damage_data_source
from OBDM.zone import Site, Building
from OBDM.element import Roof
from parcel import Parcel


def create_fragility(bldg, site, component_type, hazard_type, event_year, event_name, data_types, file_paths, damage_scale_name, analysis_date):
    # Step 1: Find similar buildings based on similarity in features, load path for the given hazard
    sim_bldgs = get_sim_bldgs.get_sim_bldgs(bldg, site, hazard_type, component_type)
    sim_bldgs.append(bldg)  # Add reference building to extract its data as well
    # Step 2: Find damage descriptions for each building
    for sim_bldg in sim_bldgs:
        data_details_list = []
        for i in range(0, len(data_types)):
            if isinstance(data_types[i], post_disaster_damage_data_source.STEER):
                data_details = data_types[i].add_steer_data(sim_bldg, component_type, hazard_type, file_paths[i])
            elif isinstance(data_types[i], post_disaster_damage_data_source.BayCountyPermits):
                length_unit = 'ft'
                data_details = data_types[i].add_disaster_permit_data(sim_bldg, component_type, hazard_type, site,
                                 file_paths[i], length_unit, damage_scale_name)
            #elif isinstance(data_types[i], post_disaster_damage_data_source.FEMA_Claims):
             #   fema_claims_details = data_types[i].add_fema_claims_data(sim_bldg, component_type, hazard_type, file_paths[i])
            # Ignore any data sources that do not contain information:
            if not data_details['available']:
                pass
            else:
                data_details_list.append(data_details)
        if len(data_details_list) > 0:
            # Step 3a: Choose the best data for each bldg/component and add to data model:
            best_data = get_best_data(data_details_list, analysis_date)  # Data Fidelity Index
            sim_bldg.hasDamageData = best_data
            sim_bldg.hasElement['Roof'][0].hasDamageData = best_data
        else:
            pass
            # Step 3b: Buildings with no other damage descriptions, use regional info:
            #if fema_claims_details['available'] == False:
             #   pass
            #else:
             #   sim_bldg.hasDamageData = fema_claims_details
              #  sim_bldg.hasElement['Roof'][0].hasDamageData = fema_claims_details
        # Step 4: Get the intensity measure or engineering demand parameter for this building:


def get_best_data(data_details_list, analysis_date):
    data_dict = {'damage precision':[], 'location precision': [], 'accuracy': [], 'currentness': []}
    for data in data_details_list:
        # Extract component/building damage descriptions:
        # Prioritize any descriptions that are at the component-level:
        # Data sources may have component & building level descriptions, if statement adds highest fidelity to data_dict
        if data['fidelity'].hasDamagePrecision['component, discrete']:
            data_dict['damage precision'].append('component, discrete')
        elif data['fidelity'].hasDamagePrecision['component, range']:
            data_dict['damage precision'].append('component, range')
        elif data['fidelity'].hasDamagePrecision['building, discrete']:
            data_dict['damage precision'].append('building, discrete')
        elif data['fidelity'].hasDamagePrecision['building, range']:
            data_dict['damage precision'].append('building, range')
        # Extract location description:
        for key in data['fidelity'].hasLocationPrecision:
            if data['fidelity'].hasLocationPrecision[key]:
                data_dict['location precision'].append(key)
        # Extract accuracy indicator:
        data_dict['accuracy'].append(data['fidelity'].hasAccuracy)
        # Extract current-ness:
        data_dict['currentness'].append(data['fidelity'].hasDate)
    # Convert to DataFrame for easier data manipulation:
    df_data = pd.DataFrame(data_dict)
    # Check for component-level damage descriptions first:
    data_fidelity_index = {'damage precision': ['component, discrete', 'component, range', 'building, discrete',
                                                'building, range'], 'location precision': ['exact location',
                                                                                           'street level', 'city/town level', 'zipcode/censusblock level'], 'accuracy': [True, False, None, None]}
    best_data = None
    for i in data_fidelity_index['location precision']:
        if best_data is not None:
            break
        else:
            for j in data_fidelity_index['damage precision']:
                if best_data is not None:
                    break
                else:
                    for k in data_fidelity_index['accuracy']:
                        if k is None:
                            pass
                        else:
                            idx = df_data.loc[(df_data['damage precision'] == j) & (df_data['location precision'] == i) & (df_data['accuracy'] == k)].index.to_list()
                            if len(idx) == 0:
                                pass
                            elif len(idx) == 1:
                                best_data = data_details_list[idx]
                                break
                            else:
                                # Choose the data source closest to either the disaster date or today's date
                                print('Multiple data sources with the same fidelity for this bldg/component')
                                best_data = data_details_list[idx]
    return best_data


def get_local_wind_speed(bldg, z, wind_speed_file_path, exposure, unit):
    df_wind_speeds = pd.read_csv(wind_speed_file_path)
    # Round the lat and lon values to two decimal places:
    df_wind_speeds['Lon'] = round(df_wind_speeds['Lon'], 2)
    df_wind_speeds['Lat'] = round(df_wind_speeds['Lat'], 2)
    # Use the parcel's geodesic location to determine its corresponding wind speed (interpolation):
    latitude = bldg.hasLocation['Geodesic'].y
    longitude = bldg.hasLocation['Geodesic'].x
    if np.sign(latitude) < 0:
        v1_idx = df_wind_speeds.loc[(df_wind_speeds['Lat'] == round(latitude, 2)) & (
                df_wind_speeds['Lon'] < round(longitude, 2))].index[0]
        v2_idx = df_wind_speeds.loc[(df_wind_speeds['Lat'] == round(latitude, 2)) & (
                df_wind_speeds['Lon'] > round(longitude, 2))].index[-1]
        # Now find the index of the two longitude values larger/smaller than parcel's longitude:
        v_basic = np.interp(longitude, [df_wind_speeds['Lon'][v1_idx], df_wind_speeds['Lon'][v2_idx]],
                            [df_wind_speeds['Vg_mph'][v1_idx], df_wind_speeds['Vg_mph'][v2_idx]])
    else:
        # Check first if there is a datapoint with lat, lon of parcel rounded two 2 decimal places:
        try:
            v_idx = df_wind_speeds.loc[(df_wind_speeds['Lat'] == round(latitude, 2)) & (
                    df_wind_speeds['Lon'] == round(longitude, 2))].index[0]
        except IndexError:
            # Choose the wind speed based off of the closest lat, lon coordinate:
            lat_idx = df_wind_speeds.loc[df_wind_speeds['Lat'] == round(latitude, 2)].index.to_list()
            new_series = abs(longitude - df_wind_speeds['Lon'][lat_idx])
            v_idx = new_series.idxmin()
        v_basic = df_wind_speeds['Vg_mph'][v_idx]
    if unit == 'metric':
        v_basic = v_basic*2.237
        ref_height = 10
        zg_c = 274.32
    else:
        ref_height = 33
        zg_c = 900
    # Populate the paramters for exposure C:
    alpha_c = 9.5
    if exposure == 'C':
        # An adjustment for height is all that is needed:
        v_site = v_basic*(z/ref_height)**(1/alpha_c)
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
        v_new = v_gradient*((z/zg)**(1/alpha))
        if bldg.hasGeometry['Height'] != ref_height:
            # Adjust for roof height:
            v_site = v_new*((z/ref_height)**(1/alpha))
        else:
            v_site = v_new
    return v_site

# Create a Site Class holding all of the data models for the parcels:
inventory = 'C:/Users/Karen/PycharmProjects/DPBWE/BayCountyCommercialParcels.csv'
df = pd.read_csv(inventory)
site = Site()
for row in range(0, len(df.index[0:5])):
    pid = df['Parcel Id'][row]
    num_stories = df['Stories'][row]
    use_code = df['Use Code'][row]
    year_built = df['Year Built'][row]
    address = df['Address'][row]
    area = df['Square Footage'][row].replace(',','')
    lon = -85.647660  # df['Longitude'][row]
    lat = 30.159210  # df['Latitude'][row]
    new_bldg = Building()
    new_bldg.add_parcel_data(pid, num_stories, use_code, year_built, address, area, lon, lat)
    #new_bldg = Parcel(pid, num_stories, use_code, year_built, address, area, lon, lat)
    new_bldg.hasElement['Roof'] = [Roof()]
    # Add additional attributes:
    new_bldg.hasElement['Roof'][0].hasCover = df['Roof Cover'][row]
    new_bldg.hasElement['Roof'][0].hasShape = 'flat'
    new_bldg.hasElement['Roof'][0].hasPitch = 0
    new_bldg.hasGeometry['Height'] = 40
    # Add permit data:
    permit_data = df['Permit Number'][row]
    if isinstance(permit_data,str):
        permit_data = permit_data.split("'")
        for idx in permit_data:
            if '-' in idx:
                if 'DIS' in idx:
                    new_bldg.hasPermitData['disaster']['number'].append(idx)
                else:
                    new_bldg.hasPermitData['other']['number'].append(idx)
            else:
                try:
                    d = int(row)
                    if 'DIS' in idx:
                        new_bldg.hasPermitData['disaster']['number'].append(idx)
                    else:
                        new_bldg.hasPermitData['other']['number'].append(idx)
                except ValueError:
                    pass
    else:
        pass
    site.hasBuilding.append(new_bldg)
site.update_zones()
site.update_elements()
# Test out data extraction with one parcel:
rcover = 'POLY TPO'
data_types = [post_disaster_damage_data_source.BayCountyPermits()]
file_paths = ['C:/Users/Karen/PycharmProjects/DPBWE/BayCountyMichael_Permits.csv']
bldg = Parcel('21084-010-000', 6, 'PROFESSION (001900)', 1987, '801 6TH ST E PANAMA CITY 32401', '70788', -85.647660, 30.159210)
bldg.hasElement['Roof'][0].hasCover = rcover
bldg.hasPermitData['disaster']['number'].append('DIS18-0003')
create_fragility(bldg, site, component_type='roof cover', hazard_type='wind', event_year=2018, event_name='Hurricane Michael', data_types=data_types, file_paths=file_paths, damage_scale_name='HAZUS-HM', analysis_date='03/04/2021')