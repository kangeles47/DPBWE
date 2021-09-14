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
from bldg_code import FBC
from create_fragility import execute_fragility_workflow
from post_disaster_damage_dataset import STEER, BayCountyPermits


def run_hm_study(inventory='C:/Users/Karen/Desktop/MB_res.csv', hazard_type='wind',
                 hazard_file_path='C:/Users/Karen/PycharmProjects/DPBWE/Datasets/WindFields/2018-Michael_windgrid_ver36.csv', component_type='roof cover', parcel_id='04973-150-000'):
    # Hurricane Michael case study:
    # Component type: Roof cover (built-up)
    # Hazard: Wind
    # Commercial inventory: 'C:/Users/Karen/Desktop/MichaelBuildings.csv'
    # LR commercial case study: 18145-000-000
    # Mexico Beach Inventory: 'C:/Users/Karen/Desktop/MB_res_clean.csv'
    # residential, mexico beach: 04973-150-000
    # Locality: Panama City Beach and Mexico Beach regions
    # '30569-100-000' original parcel number for 6 story guy
    # Step 1: Create a Site Class that will hold all parcel-specific data models:
    site = Site()
    # Step 2: Populate building inventory data and create parcel-specific data models:
    df = pd.read_csv(inventory)
    # We will also be tapping into the StEER dataset for additional building attributes:
    steer_obj = STEER()
    steer_file_path = 'C:/Users/Karen/PycharmProjects/DPBWE/Datasets/StEER/HM_D2D_Building.csv'
    # Make sure the StEER data is ready for querying:
    steer_obj.add_query_column(steer_file_path)
    for row in range(0, len(df.index)):
        # Create simple data model for each parcel and add roof and cover data:
        new_bldg = Building()
        new_bldg.add_parcel_data(df['Parcel Id'][row], df['Stories'][row], df['Use Code'][row], df['Year Built'][row],
                                 df['Address'][row], df['Square Footage'][row], df['Longitude'][row], df['Latitude'][row], 'ft')
        # Add roof element and data:
        new_roof = Roof()
        new_roof.hasCover = df['Roof Cover'][row]
        new_roof.hasType = df['Roof Cover'][row]
        # try:
        #     if len(df['Issued'][row]) > 0:
        #         pdesc = df['Description'][row][2:-2].split("'")
        #         pyear = df['Issued'][row][2:-2].split("'")
        #         year = 0
        #         for p in range(0, len(pdesc)):
        #             if 'REROOF' in pdesc[p] or 'RERF' in pdesc[p] or 'ROOF' in pdesc[p]:
        #                 new_year = int(pyear[p][:4])
        #                 if new_year > year:
        #                     year = new_year
        #             else:
        #                 pass
        #         new_roof.hasYearBuilt = year
        #         new_bldg.hasYearBuilt = year
        # except TypeError:
        #     new_roof.hasYearBuilt = new_bldg.hasYearBuilt
        new_bldg.hasStory[-1].adjacentElement['Roof'] = [new_roof]
        new_bldg.hasStory[-1].update_elements()
        new_bldg.update_zones()
        new_bldg.update_elements()
        # Bring in additional attributes from StEER:
        parcel_identifier = steer_obj.get_parcel_identifer(new_bldg)
        steer_obj.add_steer_bldg_data(new_bldg, parcel_identifier, steer_file_path)
        # Populate code-informed component-level information
        code_informed = FBC(new_bldg, loading_flag=False)
        code_informed.roof_attributes(code_informed.hasEdition, new_bldg)
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
    # Step 5: Extract the case study parcel's data model:
    for b in site.hasBuilding:
        if b.hasID == parcel_id:
            bldg = b
        else:
            pass
    # Step 6: Populate variables with list of post-disaster damage dataset types and file paths:
    data_types = [STEER(), BayCountyPermits()]
    file_paths = [steer_file_path, 'C:/Users/Karen/PycharmProjects/DPBWE/BayCountyMichael_Permits.csv']
    # Step 7: Run the workflow:
    execute_fragility_workflow(bldg, site, component_type=component_type, hazard_type=hazard_type, event_year=2018, event_name='Hurricane Michael', data_types=data_types, file_paths=file_paths, damage_scale_name='HAZUS-HM', analysis_date='03/04/2021', hazard_file_path=hazard_file_path)


def run_hi_study(inventory='C:/Users/Karen/Desktop/IrmaBuildings.csv', hazard_type='wind',
                 hazard_file_path='C:/Users/Karen/PycharmProjects/DPBWE/Datasets/WindFields/ARA_Hurricane_Irma_Windspeed_v12.csv', component_type='roof cover', parcel_id='57360360006'):
    # Irma case study:
    # Step 1: Create a Site Class that will hold all parcel-specific data models:
    site = Site()
    # Step 2: Populate building inventory data and create parcel-specific data models:
    df = pd.read_csv(inventory)
    for row in range(0, len(df.index)):
        # Create simple data model for each parcel and add roof and cover data:
        new_bldg = Building()
        new_bldg.add_parcel_data(df['Parcel Id'][row], df['Stories'][row], df['Use Code'][row], df['Year Built'][row],
                                 df['Address'][row], df['Square Footage'][row], df['Longitude'][row],
                                 df['Latitude'][row], 'ft')
        # Add roof element and data:
        new_roof = Roof()
        new_roof.hasCover = df['Roof Cover'][row]
        new_roof.hasType = df['Roof Cover'][row]
        new_bldg.hasStory[-1].adjacentElement['Roof'] = [new_roof]
        new_bldg.hasStory[-1].update_elements()
        new_bldg.update_zones()
        new_bldg.update_elements()
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
    # Step 5: Extract the case study parcel's data model:
    for b in site.hasBuilding:
        if b.hasID == parcel_id:
            bldg = b
        else:
            pass
    # Step 6: Populate variables with list of post-disaster damage dataset types and file paths:
    from post_disaster_damage_dataset import STEER, FemaHma, FemaIahrld
    data_types = [STEER(), FemaHma(), FemaIahrld()]
    file_paths = ['C:/Users/Karen/PycharmProjects/DPBWE/Datasets/StEER/HI-DA.csv', 'C:/Users/Karen/Desktop/HMA_Irma.csv', 'C:/Users/Karen/Desktop/Irma_IAHR_LD_V1.csv']
    # Step 7: Run the workflow:
    execute_fragility_workflow(bldg, site, component_type=component_type, hazard_type=hazard_type,
                               event_year=2017, event_name='Hurricane Irma', data_types=data_types,
                               file_paths=file_paths, damage_scale_name='HAZUS-HM', analysis_date='05/20/2021',
                               hazard_file_path=hazard_file_path)

run_hm_study()