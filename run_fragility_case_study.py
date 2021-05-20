import pandas as pd
from OBDM.zone import Site, Building
from OBDM.element import Roof
from parcel import Parcel
from bldg_code import FBC
from create_fragility import execute_fragility_workflow

# Create a Site Class holding all of the data models for the parcels:
inventory = 'D:/Users/Karen/Documents/Github/DPBWE/BC_CParcels.csv'
df = pd.read_csv(inventory)
site = Site()
parcel_model = False
for row in range(0, len(df.index)):
    # Create a new data model for parcel:
    if not parcel_model:
        new_bldg = Building()
        new_bldg.add_parcel_data(df['Parcel Id'][row], df['Stories'][row], df['Use Code'][row], df['Year Built'][row],
                                 df['Address'][row], df['Square Footage'][row], df['Longitude'][row], df['Latitude'][row], 'ft')
        # Add roof element and data:
        new_bldg.hasElement['Roof'] = [Roof()]
        new_bldg.hasElement['Roof'][0].hasCover = df['Roof Cover'][row]
        new_bldg.hasElement['Roof'][0].hasType = df['Roof Cover'][row]
        # Populate code-informed component-level information
        code_informed = bldg_code.FBC(new_bldg, loading_flag=False)
        code_informed.roof_attributes(code_informed.hasEdition, new_bldg, 'CBECS')
        # Add height information (if available):
        new_bldg.hasGeometry['Height'] = df['Stories'][row]*4.0*3.28084  # ft
    else:
        new_bldg = Parcel(df['Parcel Id'][row], df['Stories'][row], df['Use Code'][row], df['Year Built'][row],
                          df['Address'][row], df['Square Footage'][row], df['Longitude'][row], df['Latitude'][row], 'ft')
    # Add permit data:
    permit_data = df['Permit Number'][row]
    if isinstance(permit_data,str):
        permit_data = ast.literal_eval(permit_data)
        for item in permit_data:
            if 'DIS' in item:
                new_bldg.hasPermitData['disaster']['number'].append(item)
            else:
                new_bldg.hasPermitData['other']['number'].append(item)
    else:
        pass
    site.hasBuilding.append(new_bldg)
site.update_zones()
site.update_elements()
# Select parcel from the site:
for bldg in site.hasBuilding:
    if bldg.hasID == '30569-100-000':
        pbldg = bldg
    else:
        pass

# Irma case study:
file_path = 'C:/Users/Karen/Desktop/IrmaBuildings.csv'
dfi = pd.read_csv(file_path)
site2 = site()
for row in range(0, len(dfi.index)):
    # Create a new data model for parcel:
    if not parcel_model:
        new_bldg = Building()
        new_bldg.add_parcel_data(dfi['Parcel Id'][row], dfi['Stories'][row], dfi['Occupancy'][row], df['Year Built'][row],
                                 df['Address'][row], df['Square Footage'][row], df['Longitude'][row], df['Latitude'][row], 'ft')
        # Add roof element and data:
        new_bldg.hasElement['Roof'] = [Roof()]
        new_bldg.hasElement['Roof'][0].hasCover = df['Roof Cover'][row]
        new_bldg.hasElement['Roof'][0].hasType = df['Roof Cover'][row]
        # Populate code-informed component-level information
        code_informed = bldg_code.FBC(new_bldg, loading_flag=False)
        code_informed.roof_attributes(code_informed.hasEdition, new_bldg, 'CBECS')
        # Add height information (if available):
        if dfi['Height'][row] != 0:
            new_bldg.hasGeometry['Height'] = dfi['Height'][row]
        else:
            new_bldg.hasGeometry['Height'] = df['Stories'][row]*4.0*3.28084  # ft
data_types = [post_disaster_damage_data_source.BayCountyPermits()]
file_paths = ['D:/Users/Karen/Documents/Github/DPBWE/BayCountyMichael_Permits.csv']
hazard_file_path = 'D:/Users/Karen/Documents/Github/DPBWE/2018-Michael_windgrid_ver36.csv'
execute_fragility_workflow(pbldg, site, component_type='roof cover', hazard_type='wind', event_year=2018, event_name='Hurricane Michael', data_types=data_types, file_paths=file_paths, damage_scale_name='HAZUS-HM', analysis_date='03/04/2021', hazard_file_path=hazard_file_path)