# -------------------------------------------------------------------------------
# Name:             run_fragility_case_study.py
# Purpose:          Run wind-vulnerable roof cover component case studies for Hurricane Michael and/or Hurricane Irma
#                   Provide examples of ontology-based data model and post-disaster damage dataset usage
#
# Author:           Karen Irely Angeles (kangeles@nd.edu)
# Affiliation:      Department of Civil and Environmental Engineering and Earth Sciences,
#                   University of Notre Dame, Notre Dame, IN

# Last updated:          (v1) 05/20/2021
# ------------------------------------------------------------------------------
import pandas as pd
import ast
from OBDM.zone import Site, Building
from OBDM.element import Roof
from parcel import Parcel
from bldg_code import FBC
from create_fragility import execute_fragility_workflow


def run_hm_study(inventory='D:/Users/Karen/Documents/Github/DPBWE/BC_CParcels.csv', hazard='wind', component_type='roof cover', parcel_id='30569-100-000'):
    # Hurricane Michael case study:
    # Component type: Roof cover (built-up)
    # Hazard: Wind
    # Locality: Panama City Beach and Mexico Beach regions

    # Step 1: Create a Site Class that will hold all parcel-specific data models:
    df = pd.read_csv(inventory)
    site = Site()
    parcel_model = False
    # Step 2: Create parcel-specific data models:
    for row in range(0, len(df.index)):
        # Create a new data model for parcel:
        if not parcel_model:  # Create simple model and add roof and cover data
            new_bldg = Building()
            new_bldg.add_parcel_data(df['Parcel Id'][row], df['Stories'][row], df['Use Code'][row], df['Year Built'][row],
                                 df['Address'][row], df['Square Footage'][row], df['Longitude'][row], df['Latitude'][row], 'ft')
            # Add roof element and data:
            new_bldg.hasElement['Roof'] = [Roof()]
            new_bldg.hasElement['Roof'][0].hasCover = df['Roof Cover'][row]
            new_bldg.hasElement['Roof'][0].hasType = df['Roof Cover'][row]
            # Populate code-informed component-level information
            code_informed = FBC(new_bldg, loading_flag=False)
            code_informed.roof_attributes(code_informed.hasEdition, new_bldg, 'CBECS')
            # Add height information (if available):
            new_bldg.hasGeometry['Height'] = df['Stories'][row]*4.0*3.28084  # ft
        else:  # Create full data model with 3D geometries, Parcel-informed features, full default components
            new_bldg = Parcel(df['Parcel Id'][row], df['Stories'][row], df['Use Code'][row], df['Year Built'][row],
                              df['Address'][row], df['Square Footage'][row], df['Longitude'][row], df['Latitude'][row], 'ft')
        # Parcel data for this inventory includes some permit numbers.
        # Add when available and differentiate between disaster and regular permits.
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
        # Step 3: Add new parcel-specific data model to the site description:
        site.hasBuilding.append(new_bldg)
    # Step 4: Update the site's zone and element information (relational attributes):
    site.update_zones()
    site.update_elements()

data_types = [post_disaster_damage_data_source.BayCountyPermits()]
file_paths = ['D:/Users/Karen/Documents/Github/DPBWE/BayCountyMichael_Permits.csv']
hazard_file_path = 'D:/Users/Karen/Documents/Github/DPBWE/2018-Michael_windgrid_ver36.csv'
execute_fragility_workflow(pbldg, site, component_type='roof cover', hazard_type='wind', event_year=2018, event_name='Hurricane Michael', data_types=data_types, file_paths=file_paths, damage_scale_name='HAZUS-HM', analysis_date='03/04/2021', hazard_file_path=hazard_file_path)



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