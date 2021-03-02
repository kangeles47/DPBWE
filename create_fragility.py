import pandas as pd
import get_sim_bldgs
import post_disaster_damage_data_source
from OBDM.zone import Site, Building
from OBDM.element import Roof
from parcel import Parcel


def create_fragility(bldg, site, component_type, hazard_type, event_year, event_name, data_types, file_paths):
    # Step 1: Find similar buildings based on similarity in features, load path for the given hazard
    sim_bldgs = get_sim_bldgs.get_sim_bldgs(bldg, site, hazard_type, component_type)
    sim_bldgs.append(bldg)  # Add reference building to extract its data as well
    # Step 2: Find damage descriptions for each building
    for sim_bldg in sim_bldgs:
        data_list = []
        for i in range(0, len(data_types)):
            if isinstance(data_types[i], post_disaster_damage_data_source.STEER):
                data_details = data_types[i].add_steer_data(sim_bldg, component_type, hazard_type, file_paths[i])
            elif isinstance(data_types[i], post_disaster_damage_data_source.BayCountyPermits):
                data_details = data_types[i].add_permit_data(sim_bldg, component_type, hazard_type, file_paths[i])
        # Ignore any data sources that do not contain information:
        if not data_details['availability']:
            pass
        else:
            data_list.append(data_details)
        # Data Quality Index:

    # Step 3: Choose the best data source for this damage description:


def get_best_data(data_details_list):
    data_dict = {'component': [], 'building': []}
    for data in data_details_list:
        # Prioritize any descriptions that are at the component-level:
        if data['fidelity'].hasDamagePrecision['component, discrete'] or data['fidelity'].hasDamagePrecision['component, range']:
            data_dict['component'].append(data)
        elif data['fidelity'].hasDamagePrecision['building, discrete'] or data['fidelity'].hasDamagePrecision['building, range']:
            data_dict['building'].append(data)
    # Check for component-level descriptions:
    if len(data_dict['component']) > 0:
        pass

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
    site.hasBuilding.append(new_bldg)
site.update_zones()
site.update_elements()
# Test out data extraction with one parcel:
rcover = 'POLY TPO'
data_types = [post_disaster_damage_data_source.STEER()]
file_paths = ['C:/Users/Karen/Desktop/HM_D2D_Building.csv']
bldg = Parcel('21084-010-000', 6, 'PROFESSION (001900)', 1987, '801 6TH ST E PANAMA CITY 32401', '70788', -85.647660, 30.159210)
bldg.hasElement['Roof'][0].hasCover = rcover
create_fragility(bldg, site, component_type='roof cover', hazard_type='wind', event_year=2018, event_name='Hurricane Michael', data_types=data_types, file_paths=file_paths)