import pandas as pd
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
            # Ignore any data sources that do not contain information:
            if not data_details['available']:
                pass
            else:
                data_details_list.append(data_details)
        # Step 3: Choose the best data for each bldg/component:
        # Data Quality Index:
        best_data = get_best_data(data_details_list, analysis_date)


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