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


def run_hm_study(inventory='D:/Users/Karen/Documents/Github/DPBWE/BC_CParcels.csv', hazard_type='wind',
                 hazard_file_path='D:/Users/Karen/Documents/Github/DPBWE/Datasets/WindFields/2018-Michael_windgrid_ver36.csv', component_type='roof cover', parcel_id='30569-100-000'):
    # Hurricane Michael case study:
    # Component type: Roof cover (built-up)
    # Hazard: Wind
    # Locality: Panama City Beach and Mexico Beach regions

    # Step 1: Create a Site Class that will hold all parcel-specific data models:
    site = Site()
    # Step 2: Populate building inventory data and create parcel-specific data models:
    df = pd.read_csv(inventory)
    for row in range(0, len(df.index)):
        # Create simple data model for each parcel and add roof and cover data:
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
    # Step 5: Populate variables with list of post-disaster damage dataset types and file paths:
    from post_disaster_damage_dataset import STEER, BayCountyPermits
    data_types = [STEER(), BayCountyPermits()]
    file_paths = ['D:/Users/Karen/Documents/Github/DPBWE/HM_D2D_Building.csv', 'D:/Users/Karen/Documents/Github/DPBWE/BayCountyMichael_Permits.csv']
    # Step 6: Run the workflow:
    execute_fragility_workflow(parcel_id, site, component_type=component_type, hazard_type=hazard_type, event_year=2018, event_name='Hurricane Michael', data_types=data_types, file_paths=file_paths, damage_scale_name='HAZUS-HM', analysis_date='03/04/2021', hazard_file_path=hazard_file_path)


def run_hi_study(inventory='C:/Users/Karen/Desktop/IrmaBuildings.csv', hazard_type='wind',
                 hazard_file_path='D:/Users/Karen/Documents/Github/DPBWE/Datasets/WindFields/ARA_Hurricane_Irma_Windspeed.csv', component_type='roof cover', parcel_id='30569-100-000'):
    # Irma case study:
    # Step 1: Create a Site Class that will hold all parcel-specific data models:
    site = Site()
    parcel_model = False
    # Step 2: Populate building inventory data and create parcel-specific data models:
    df = pd.read_csv(inventory)
    for row in range(0, len(df.index)):
        # Create simple data model for each parcel and add roof and cover data:
        new_bldg = Building()
        new_bldg.add_parcel_data(df['Parcel Id'][row], df['Stories'][row], df['Use Code'][row], df['Year Built'][row],
                                 df['Address'][row], df['Square Footage'][row], df['Longitude'][row],
                                 df['Latitude'][row], 'ft')
        # Add roof element and data:
        new_bldg.hasElement['Roof'] = [Roof()]
        new_bldg.hasElement['Roof'][0].hasCover = df['Roof Cover'][row]
        new_bldg.hasElement['Roof'][0].hasType = df['Roof Cover'][row]
        # Populate code-informed component-level information
        code_informed = FBC(new_bldg, loading_flag=False)
        code_informed.roof_attributes(code_informed.hasEdition, new_bldg, 'CBECS')
        # Add height information (if available):
        if df['Height'][row] != 0:
            new_bldg.hasGeometry['Height'] = df['Height'][row]
        else:
            new_bldg.hasGeometry['Height'] = df['Stories'][row]*4.0*3.28084  # ft
        # Step 3: Add new parcel-specific data model to the site description:
        site.hasBuilding.append(new_bldg)
    # Step 4: Update the site's zone and element information (relational attributes):
    site.update_zones()
    site.update_elements()
    # Step 5: Populate variables with list of post-disaster damage dataset types and file paths:
    from post_disaster_damage_dataset import FemaHma, FemaIahrld
    data_types = [FemaHma(), FemaIahrld()]
    file_paths = ['API', 'API']
    # Step 6: Run the workflow:
    execute_fragility_workflow(parcel_id, site, component_type=component_type, hazard_type=hazard_type,
                               event_year=2017, event_name='Hurricane Irma', data_types=data_types,
                               file_paths=file_paths, damage_scale_name='HAZUS-HM', analysis_date='05/20/2021',
                               hazard_file_path=hazard_file_path)
