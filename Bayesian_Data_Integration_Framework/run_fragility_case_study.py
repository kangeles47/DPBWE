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
from bldg_code import FBC, TX
from Bayesian_Data_Integration_Framework.create_fragility import execute_fragility_workflow
from Bayesian_Data_Integration_Framework.post_disaster_damage_dataset import STEER, BayCountyPermits, FemaHma, FemaIahrld


def run_hm_study(inventory='C:/Users/Karen/Desktop/MB_res.csv', hazard_type='wind',
                 hazard_file_path='C:/Users/Karen/PycharmProjects/DPBWE/Datasets/WindFields/2018-Michael_windgrid_ver36.csv',
                 component_type='roof cover', parcel_id='04973-808-000', sfh_flag=True, rpermit_flag=True):
    # Hurricane Michael case study:
    # Component type: Roof cover (built-up)
    # Hazard: Wind
    # Whole inventory: 'C:/Users/Karen/Desktop/MB_PCB.csv'
    # Commercial inventory: 'C:/Users/Karen/Desktop/MichaelBuildings.csv'
    # LR commercial case study: 18145-000-000
    # Mexico Beach Inventory: 'C:/Users/Karen/Desktop/MB_res.csv'
    # residential, mexico beach: 04973-808-000
    # Panama City Beach inventory:
    # 'C:/Users/Karen/Desktop/PCB_full_res.csv'
    # '38333-050-301'
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
        if df['Stories'][row] >= 2:
            pass
        else:
            # Create simple data model for each parcel and add roof and cover data:
            new_bldg = Building()
            new_bldg.add_parcel_data(df['Parcel Id'][row], df['Stories'][row], df['Use Code'][row], df['Year Built'][row],
                                     df['Address'][row], df['Square Footage'][row], df['Longitude'][row], df['Latitude'][row], 'ft', loc_flag=True)
            # Add roof element and data:
            new_roof = Roof()
            new_roof.hasCover = df['Roof Cover'][row]
            new_roof.hasType = df['Roof Cover'][row]
            new_bldg.hasStory[-1].adjacentElement['Roof'] = [new_roof]
            new_bldg.hasStory[-1].update_elements()
            new_bldg.update_zones()
            new_bldg.update_elements()
            if rpermit_flag:
                try:
                    if len(df['Permit Issued Date'][row]) > 0:
                        pdesc = df['Permit Description'][row][2:-2].split("'")
                        pyear = df['Permit Issued Date'][row][2:-2].split("'")
                        year = df['Year Built'][row]
                        for p in range(0, len(pdesc)):
                            if 'REROOF' in pdesc[p] or 'RERF' in pdesc[p] or 'ROOF' in pdesc[p]:
                                new_year = int(pyear[p][:4])
                                if year < new_year < 2018:
                                    year = new_year
                            else:
                                pass
                        new_bldg.adjacentElement['Roof'][0].hasYearBuilt = year
                        new_bldg.hasYearBuilt = year
                except TypeError:
                    new_bldg.adjacentElement['Roof'][0].hasYearBuilt = new_bldg.hasYearBuilt
            else:
                pass
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
            permit_description = df['Permit Type'][row]
            if isinstance(permit_data,str):
                permit_data = ast.literal_eval(permit_data)
                for item in permit_data:
                    if 'DIS' in item:
                        new_bldg.hasPermitData['disaster']['number'].append(item)
                    else:
                        new_bldg.hasPermitData['other']['number'].append(item)
                        new_bldg.hasPermitData['other']['permit type'].append(permit_description)
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
    file_paths = [steer_file_path, 'C:/Users/Karen/PycharmProjects/DPBWE/PostdisasterDatasets'
                                   '/BayCountyMichael_Permits.csv']
    # Step 7: Run the workflow:
    execute_fragility_workflow(bldg, site, component_type=component_type, hazard_type=hazard_type, event_year=2018, event_name='Hurricane Michael', data_types=data_types, file_paths=file_paths,
                               damage_scale_name='HAZUS-HM', analysis_date='03/04/2021', hazard_file_path=hazard_file_path, sfh_flag=True)


def run_hi_study(inventory='C:/Users/Karen/Desktop/IrmaBuildings.csv', hazard_type='wind',
                 hazard_file_path='C:/Users/Karen/PycharmProjects/DPBWE/Datasets/WindFields/ARA_Hurricane_Irma_Windspeed_v12.csv',
                 component_type='roof cover', parcel_id='57360360006'):
    # Make sure StEER data is ready for parsing:
    steer_obj = STEER()
    steer_file_path = 'C:/Users/Karen/PycharmProjects/DPBWE/Datasets/StEER/HI-DA.csv'
    # Make sure the StEER data is ready for querying:
    steer_obj.add_query_column(steer_file_path)
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
                                 df['Latitude'][row], 'ft', loc_flag=True)
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
        code_informed.roof_attributes(code_informed.hasEdition, new_bldg)
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
    data_types = [STEER(), FemaHma(), FemaIahrld()]
    file_paths = [steer_file_path, 'C:/Users/Karen/PycharmProjects/DPBWE/PostdisasterDatasets/HMA_Irma.csv',
                  'C:/Users/Karen/Desktop/PycharmProjects/DPBWE/PostdisasterDatasets/Irma_IAHR_LD_V1.csv']
    # Step 7: Run the workflow:
    execute_fragility_workflow(bldg, site, component_type=component_type, hazard_type=hazard_type,
                               event_year=2017, event_name='Hurricane Irma', data_types=data_types,
                               file_paths=file_paths, damage_scale_name='HAZUS-HM', analysis_date='05/20/2021',
                               hazard_file_path=hazard_file_path, sfh_flag=False)


def run_hh_study(inventory='C:/Users/Karen/Desktop/HH_NSF_CMMI1759996_BuildingAssessments.csv', hazard_type='wind',
                 hazard_file_path='C:/Users/Karen/PycharmProjects/DPBWE/Datasets/WindFields'
                                  '/ARA_Hurricane_Harvey_Windspeed_v26.csv',
                 component_type='roof cover', parcel_id='12d068d3-5948-4d6f-9204-e04942773081', sfh_flag=True):
    # Irma case study:
    # Step 1: Create a Site Class that will hold all parcel-specific data models:
    site = Site()
    # Since building inventory is from StEER dataset, let's populate query column (if needed) to grab bldg attributes:
    steer_obj = STEER()
    # Make sure the StEER data is ready for querying:
    steer_obj.add_query_column(inventory)
    # Step 2: Populate building inventory data and create parcel-specific data models:
    df = pd.read_csv(inventory)
    inland_areas = ['NUECES', 'TIVOLI', 'TAFT', 'SINTON', 'REFUGIO']
    for row in range(0, len(df.index)):
        use_code = df['assessment_type'][row]
        if sfh_flag:
            if 'Single' in use_code:
                if any([i in df['address_locality'][row].upper() for i in inland_areas]):
                    pass
                else:
                    try:
                        roof_cover = df['roof_cover'][row].upper()  # skip any empty roof cover entries
                        # Create simple data model for each parcel and add roof and cover data:
                        new_bldg = Building()
                        new_bldg.add_parcel_data(df['fulcrum_id'][row], df['number_of_stories'][row], df['assessment_type'][row], df['year_built'][row],
                                                 df['address_query'][row], 0, df['longitude'][row],
                                                 df['latitude'][row], 'ft', loc_flag=False)
                        new_bldg.hasLocation['State'] = 'TX'
                        new_bldg.hasLocation['Street Number'] = df['address_sub_thoroughfare'][row] + ' ' + df['address_thoroughfare'][row]
                        new_bldg.hasLocation['City'] = df['address_locality'][row]
                        new_bldg.hasLocation['County'] = df['address_sub_admin_area'][row]
                        new_bldg.hasLocation['Zip Code'] = df['address_postal_code'][row]
                        # Add roof element and data:
                        new_roof = Roof()
                        if 'ASPHALT' in roof_cover and 'SEAM' not in roof_cover:
                            new_roof.hasCover = 'ASPHALT SHINGLES'
                            new_roof.hasType = 'ASPHALT SHINGLES'
                        else:
                            new_roof.hasCover = roof_cover
                            new_roof.hasType = roof_cover
                        new_bldg.hasStory[-1].adjacentElement['Roof'] = [new_roof]
                        new_bldg.hasStory[-1].update_elements()
                        new_bldg.update_zones()
                        new_bldg.update_elements()
                        # Populate code-informed component-level information
                        code_informed = TX(new_bldg, loading_flag=False)
                        code_informed.roof_attributes(new_bldg)
                        # Add height information:
                        new_bldg.hasGeometry['Height'] = df['number_of_stories'][row]*4.0*3.28084  # ft
                        # Step 3: Add new parcel-specific data model to the site description:
                        site.hasBuilding.append(new_bldg)
                    except AttributeError:
                        pass
            else:
                pass
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
    data_types = [STEER(), FemaIahrld()]
    file_paths = [inventory, 'API']
    # Step 7: Run the workflow:
    execute_fragility_workflow(bldg, site, component_type=component_type, hazard_type=hazard_type,
                               event_year=2017, event_name='Hurricane Harvey', data_types=data_types,
                               file_paths=file_paths, damage_scale_name='HAZUS-HM', analysis_date='09/16/2021',
                               hazard_file_path=hazard_file_path, sfh_flag=True)

run_hm_study()
