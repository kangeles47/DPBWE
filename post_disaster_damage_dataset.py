import pandas as pd
from numpy import isnan
import requests
import matplotlib.pyplot as plt


class PostDisasterDamageDataset:

    def __init__(self):
        self.hasDamagePrecision = {'component, discrete': False, 'component, range': False, 'building, discrete': False,
                                   'building, range': False}
        self.hasLocationPrecision = {'exact location': False, 'street level': False, 'city/town level': False,
                                     'zipcode/censusblock level': False}
        self.hasAccuracy = False
        self.hasCurrentness = False
        self.hasReliability = False
        self.hasDate = '00/00/0000'
        self.hasDamageScale = {'type': '', 'global damage states': {'number': [], 'description': [], 'value': []},
                               'component damage states': {'number': [], 'description': [], 'value': []}}
        self.hasHazard = {'wind': False, 'tree': False, 'rain': False, 'wind-borne debris': False, 'flood': False,
                          'surge': False}
        self.hasType = {'field observations': False, 'permit data': False, 'crowdsourced': False,
                        'remote sensing/imagery': False, 'fema modeled assessment': False, 'fema claims data': False}
        self.hasEventName = ''
        self.hasEventYear = '00/00/0000'
        self.hasEventLocation = {'city': '', 'county': '', 'state': '', 'country': ''}

    def get_damage_scale(self, damage_scale_name, component_type, global_flag, component_flag):
        if damage_scale_name == 'HAZUS-HM':
            self.hasDamageScale['type'] = 'HAZUS-HM'
            if global_flag:
                global_ds_nums = [0, 1, 2, 3, 4]
                global_ds_desc = ['No Damage', 'Minor Damage', 'Moderate Damage', 'Severe Damage', 'Destruction']
                global_ds_vals = None
            if component_flag:
                comp_ds_nums = [0, 1, 2, 3, 4]
                comp_ds_desc = ['No Damage', 'Minor Damage', 'Moderate Damage', 'Severe Damage', 'Destruction']
                if component_type == 'roof cover':
                    comp_ds_vals = [[0, 2], [2, 15], [15, 50], [50, 100], [50, 100]]
                else:
                    print('Component damage values not supported for ' + damage_scale_name + 'and ' + component_type)
        elif damage_scale_name == 'WF':
            self.hasDamageScale['type'] = 'WF'
            if global_flag:
                global_ds_nums = [0, 1, 2, 3, 4, 5, 6]
                global_ds_desc = ['No Damage', 'Minor Damage', 'Moderate Damage', 'Severe Damage', 'Very Severe Damage',
                                  'Partial Collapse', 'Collapse']
                global_ds_vals = []
            if component_flag:
                comp_ds_nums = [0, 1, 2, 3, 4, 5, 6]
                comp_ds_desc = ['No Damage', 'Minor Damage', 'Moderate Damage', 'Severe Damage', 'Very Severe Damage',
                                'Partial Collapse', 'Collapse']
                if component_type == 'roof cover':
                    comp_ds_vals = [[0, 2], [2, 15], [15, 50], [50, 100], [50, 100], [50, 100], [50, 100]]
                else:
                    print('Component damage values not supported for ' + damage_scale_name + 'and ' + component_type)
        elif damage_scale_name == 'FEMA Geospatial':
            self.hasDamageScale['type'] = 'FEMA Geospatial'
            if global_flag:
                global_ds_nums = [0, 1, 2, 3, 4]
                global_ds_desc = ['No Damage', 'Minor Damage', 'Major/Severe Damage', 'Destroyed']
                global_ds_vals = []
            if component_flag:
                comp_ds_nums = []
                comp_ds_desc = []
                comp_ds_vals = []
                print('Component damage scale info not available for ' + damage_scale_name)
        elif damage_scale_name == 'FEMA HMA':
            self.hasDamageScale['type'] = 'FEMA HMA'
            global_ds_nums = [0, 1, 2]
            global_ds_desc = ['Damage <= 49%', 'Damage >=50%', 'Total Loss']
            global_ds_vals = [[0 - 49], [50, 99], 100]
            if component_flag:
                if 'roof' in component_type:
                    comp_ds_nums = [0, 1, 2]
                    comp_ds_desc = ['Damage <= 49%', 'Damage >=50%', 'Total Loss']
                    comp_ds_vals = [[0, 49], [50, 99], 100]
                else:
                    print('Component damage values not supported for ' + damage_scale_name + 'and ' + component_type)
        elif damage_scale_name == 'FEMA IHARLD':
            self.hasDamageScale['type'] = 'FEMA IHARLD'
            global_ds_nums = [0, 1]
            global_ds_desc = ['No Damage', 'Damage']
            global_ds_vals = []
            if component_flag:
                if 'roof' in component_type:
                    comp_ds_nums = [0, 1]
                    comp_ds_desc = ['No Damage', 'Damage']
                    comp_ds_vals = [0, [0, 100]]
                else:
                    print('Component damage values not supported for ' + damage_scale_name + 'and ' + component_type)
        else:
            print('Please select a damage scale for this dataset')
        # Add damage state and damage values to dataset for specified damage scale + component_type:
        if global_flag:
            self.hasDamageScale['global damage states']['number'] = global_ds_nums
            self.hasDamageScale['global damage states']['description'] = global_ds_desc
            self.hasDamageScale['global damage states']['value'] = global_ds_vals
        if component_flag:
            self.hasDamageScale['component damage states']['number'] = comp_ds_nums
            self.hasDamageScale['component damage states']['description'] = comp_ds_desc
            self.hasDamageScale['component damage states']['value'] = comp_ds_vals


class STEER(PostDisasterDamageDataset):
    def __init__(self):
        PostDisasterDamageDataset.__init__(self)
        self.hasDamagePrecision['component, discrete'] = True
        self.hasDamagePrecision['building, range'] = True
        self.hasLocationPrecision['exact location'] = True
        self.hasLocationPrecision['street level'] = True
        self.hasAccuracy = True
        self.hasType['field observations'] = True

    def add_query_column(self, steer_file_path):
        df_steer = pd.read_csv(steer_file_path)
        if 'address_query' in df_steer.columns:
            pass
        else:
            # Create a new column to make address queries:
            query_col = []
            for row in range(0, len(df_steer)):
                try:
                    sp = df_steer['address_full'][row].split()
                    new_address = ''
                    for s in sp[:-2]:
                        new_address = new_address + s.upper() + ' '
                    query_col.append(new_address.strip())
                except AttributeError:
                    query_col.append('NONE')
            df_steer['address_query'] = query_col
            df_steer.to_csv(steer_file_path, index=False)

    def get_parcel_identifer(self, bldg):
        parcel_identifier = bldg.hasLocation['Street Number'] + ' ' + bldg.hasLocation['City'] + ' ' + bldg.hasLocation[
            'County'] + ' ' + bldg.hasLocation['State']
        parcel_identifier = parcel_identifier.upper()  # Data clean-up
        return parcel_identifier

    def add_steer_bldg_data(self, bldg, parcel_identifier, steer_file_path):
        # Step 1: Load the StEER Dataset:
        df_steer = pd.read_csv(steer_file_path)
        # Step 2: Use the parcel identifier to populate additional building and component attributes:
        idx = df_steer.loc[df_steer['address_query'] == parcel_identifier].index
        if len(idx) > 0:
            idx = idx[0]
            # First check if we need to add roof shape info:
            try:
                steer_roof_shape = df_steer['roof_shape'][idx].lower()
                for key in bldg.adjacentElement['Roof'][0].hasShape:
                    if not bldg.adjacentElement['Roof'][0].hasShape:
                        if key == steer_roof_shape:
                            bldg.adjacentElement['Roof'][0].hasShape[key] = True
                        elif key == 'complex' and 'complex' in steer_roof_shape:
                            bldg.adjacentElement['Roof'][0].hasShape[key] = True
                        elif key == 'complex' and ',' in steer_roof_shape:
                            bldg.adjacentElement['Roof'][0].hasShape[key] = True
                        else:
                            pass
                    else:
                        pass
            except AttributeError:
                pass
            # Now check if we need to add any year built information:
            from numpy import nan
            if bldg.hasYearBuilt == nan or bldg.hasYearBuilt == 0:
                bldg.hasYearBuilt = df_steer['year_built'][idx]
            else:
                pass
        else:
            pass

    def add_steer_data(self, bldg, component_type, hazard_type, steer_file_path):
        """
        A function to search for StEER damage observations for the specified building.

        :param bldg: Parcel or Building object with complete hasLocation attribute.
        :param component_type: String specifying the component type.
        :param hazard_type: String specifying the hazard type.
        :param steer_file_path: File path to the event's StEER dataset.
        :return: data_details: Dictionary with information about data availability, dataset fidelity,
                               the component type, hazard type, and damage description.
        """
        # Step 1: Load the StEER Dataset:
        df_steer = pd.read_csv(steer_file_path)
        # Step 2: Define the parcel identifier:
        # Parcel identifier should be the parcel's address in the following format (not case-sensitive):
        # 1842 BRIDGE ST Panama City BAY FL 32409 USA (number, street, city, county, state, zip, country)
        parcel_identifier = self.get_parcel_identifer(bldg)
        # Step 3: # Set up data_details dictionary:
        data_details = {'available': False, 'fidelity': self, 'component type': component_type,
                        'hazard type': hazard_type, 'value': None}
        # Step 4: Look for damage observation for the given component and hazard type:
        try:
            # Check if the parcel has a StEER observation at its exact location:
            idx = df_steer.loc[df_steer['address_query'] == parcel_identifier].index[0]
            self.hasDate = df_steer['date'][idx]
            # Update the Location Precision attribute:
            self.hasLocationPrecision['street level'] = False
            # Update damage dataset hazard info:
            for key in self.hasHazard:
                if key in df_steer['hazards_present'][idx].lower():
                    self.hasHazard[key] = True
            # Extract component-level damage descriptions if the desired hazard is present:
            if self.hasHazard[hazard_type]:
                if component_type == 'roof cover':
                    # Check if there are roof-related damage descriptions:
                    if not isnan(df_steer['roof_cover_damage_'][idx]):
                        data_details['available'] = True
                        # Update dataset object damage scale:
                        self.get_damage_scale('HAZUS-HM', 'roof cover', global_flag=True, component_flag=True)
                        try:  # Case where data is either reported as string percent (10%) versus number (10)
                            val = int(df_steer['roof_cover_damage_'][idx].split('%')[0])
                            data_details['value'] = val
                        except AttributeError:
                            data_details['value'] = df_steer['roof_cover_damage_'][idx]
            else:
                pass
        except IndexError:  # No StEER entry exists for this exact location: Check General Area or does not exist
            pass
        return data_details


class BayCountyPermits(PostDisasterDamageDataset):
    def __init__(self):
        PostDisasterDamageDataset.__init__(self)
        self.hasDamagePrecision['component, discrete'] = True
        self.hasDamagePrecision['component, range'] = True
        self.hasLocationPrecision['exact location'] = True
        self.hasAccuracy = False
        self.hasType['permit data'] = True

    def add_mb_disaster_res_permit_data(self, bldg, component_type, hazard_type, damage_scale_name):
        # Check if this building is in Mexico Beach:
        if bldg.hasLocation['City'].upper() == 'MEXICO BEACH':
            # Step 1: Activate the damage scale information that will be used:
            self.get_damage_scale(damage_scale_name, component_type, global_flag=True, component_flag=True)
            # Step 2: Populate data_details dictionary:
            if component_type == 'roof cover':
                data_details_list = []
                # Look for roof and demo-related information:
                for p in range(0, len(bldg.hasPermitData['other']['number'])):
                    data_details = {'available': False, 'fidelity': self, 'component type': component_type,
                                    'hazard type': hazard_type,
                                    'value': None, 'hazard damage rating': {'wind': None, 'surge': None, 'rain': None}}
                    if 'MB' in bldg.hasPermitData['other']['number'][p]:
                        # Check damage scale information:
                        if damage_scale_name == 'HAZUS-HM' and hazard_type == 'wind':
                            # Check if this is a roof-related permit:
                            if 'ROOF' in bldg.hasPermitData['other']['permit type'][p] or 'RERF' in bldg.hasPermitData['other']['permit type'][p] or 'DEM' in bldg.hasPermitData['other']['permit type'][p]:
                                self.hasDamagePrecision['component, range'] = True
                                self.hasDamagePrecision['component, discrete'] = False
                                data_details['available'] = True
                                if 'RERF' in bldg.hasPermitData['other']['permit type'][p]:
                                    data_details['hazard damage rating']['wind'] = self.hasDamageScale['component damage states']['number'][1]
                                    data_details['value'] = self.hasDamageScale['component damage states']['value'][1]
                                elif 'ROOF' in bldg.hasPermitData['other']['permit type'][p]:
                                    data_details['hazard damage rating']['wind'] = self.hasDamageScale['component damage states']['number'][2]
                                    data_details['value'] = self.hasDamageScale['component damage states']['value'][2]
                                else:
                                    data_details['hazard damage rating']['wind'] = self.hasDamageScale['component damage states']['number'][3]
                                    data_details['value'] = self.hasDamageScale['component damage states']['value'][3]
                        else:
                            pass
                    data_details_list.append(data_details)
                # In some cases, there may be multiple permits available. Choose worse damage:
                if len(data_details_list) > 0:
                    max_damage = 0
                    max_damage_idx = 0
                    for d in range(0, len(data_details_list)):
                        if data_details_list[d]['available']:
                            if data_details_list[d]['hazard damage rating']['wind'] > max_damage:
                                max_damage = data_details_list[d]['hazard damage rating']['wind']
                                max_damage_idx = d
                        else:
                            pass
                    final_data_details = data_details_list[max_damage_idx]
                else:
                    final_data_details = {'available': False, 'fidelity': self, 'component type': component_type,
                                            'hazard type': hazard_type,
                                            'value': None, 'hazard damage rating': {'wind': None, 'surge': None, 'rain': None}}
        else:
            pass
        return final_data_details


    def add_disaster_permit_data(self, bldg, component_type, hazard_type, site,
                                 permit_file_path, length_unit, damage_scale_name):
        """
        A function to find damage descriptions from disaster building permits for buildings in Florida's Bay County.

        :param bldg: Parcel or Building object with ['Street Number'] key filled in hasLocation attribute.
        :param component_type: String specifying the component type.
        :param hazard_type: String specifying the hazard type.
        :param site: Site object with hasBuilding attribute = list of parcel data models for the inventory.
        :param permit_file_path: String specifying the file path to the disaster permits.
        :param length_unit: String specifying the length unit of measurement for the analysis (e.g., 'ft', 'm').
        :param damage_scale_name: String specifying the name of the damage scale that will be used to conduct
                                  semantic translation of damage descriptions.
        :return: data_details: Dictionary with information about data availability, dataset fidelity,
                               the component type, hazard type, and damage description.
        """
        # Step 1: Activate the damage scale information that will be used:
        self.get_damage_scale(damage_scale_name, component_type, global_flag=True, component_flag=True)
        # Step 2: Load the disaster permit data:
        df = pd.read_csv(permit_file_path, encoding='unicode_escape')
        # Step 3: Find disaster permit descriptions for the parcel:
        if len(bldg.hasPermitData['disaster']['number']) > 0:  # case when permit number was included in parcel data
            for p in bldg.hasPermitData['disaster']['number']:
                idx = df.loc[df['PERMITNUMBER'] == p].index[0]
                bldg.hasPermitData['disaster']['description'].append(df['DESCRIPTION'][idx].upper())
                bldg.hasPermitData['disaster']['permit type'].append(df['PERMITSUBTYPE'][idx].upper())
                if '/' not in df['ISSUED'][idx]:
                    if 'DIS18' in df['PERMITNUMBER'][idx].upper():
                        self.hasDate = '10/16/2018'
                    elif 'DIS19' in df['PERMITNUMBER'][idx].upper():
                        self.hasDate = '00/00/2019'
                    elif 'DIS20' in df['PERMITNUMBER'][idx].upper():
                        self.hasDate = '00/00/2020'
                else:
                    self.hasDate = df['ISSUED'][idx]
        else:  # case when we need to search for the permit in the dataset
            # Find the disaster permit descriptions using the parcel identifier
            parcel_identifier = bldg.hasLocation['Street Number'].upper()
            try:
                idx = df.loc[df['SITE_ADDR'] == parcel_identifier].index.to_list()
                for i in idx:
                    bldg.hasPermitData['disaster']['number'].append(df['PERMITNUMBER'][i].upper())
                    bldg.hasPermitData['disaster']['description'].append(df['DESCRIPTION'][i].upper())
                    bldg.hasPermitData['disaster']['permit type'].append(df['PERMITSUBTYPE'][i].upper())
                    if '/' not in df['ISSUED'][i]:  # DataFrame ordered chronologically: recent permit -> hasDate
                        if 'DIS18' in df['PERMITNUMBER'][i].upper():
                            self.hasDate = '10/16/2018'
                        elif 'DIS19' in df['PERMITNUMBER'][i].upper():
                            self.hasDate = '00/00/2019'
                        elif 'DIS20' in df['PERMITNUMBER'][i].upper():
                            self.hasDate = '00/00/2020'
                        elif 'DIS21' in df['PERMITNUMBER'][i].upper():
                            self.hasDate = '00/00/2021'
                    else:
                        self.hasDate = df['ISSUED'][i]
            except IndexError:
                pass  # No disaster permits available for this parcel
        # Step 4: Conduct semantic translations of permit descriptions for the component and hazard types:
        if len(bldg.hasPermitData['disaster']['number']) > 0:
            data_details = self.get_dis_permit_damage(bldg, component_type, hazard_type, site, length_unit)
        else:
            data_details = {'available': False, 'fidelity': self, 'component type': component_type,
                            'hazard type': hazard_type, 'value': None}
        return data_details

    def get_dis_permit_damage(self, bldg, component_type, hazard_type, site, length_unit):
        """
        A function to conduct the semantic translation of permit descriptions.

        :param bldg: Parcel or Building object with total floor area information.
        :param component_type: String specifying the component type.
        :param hazard_type: String specifying the hazard type.
        :param site: Site object with hasBuilding attribute = list of parcel data models for the inventory.
        :param length_unit: String specifying the length unit of measurement for the analysis (e.g., 'ft', 'm').
        :return: data_details: Dictionary with information about data availability, dataset fidelity,
                               the component type, hazard type, and damage description.
        """
        # Step 1: Populate data_details dictionary:
        data_details = {'available': False, 'fidelity': self, 'component type': component_type,
                        'hazard type': hazard_type,
                        'value': None, 'hazard damage rating': {'wind': None, 'surge': None, 'rain': None}}
        # Step 2: Loop through permit descriptions and conduct semantic translations:
        # Allocate empty lists to gather damage information:
        if component_type == 'roof cover' and hazard_type == 'wind':
            # Loop through the bldg's disaster permits:
            count = 0  # dummy variable to flag multiple roof permits in a parcel
            for p in range(0, len(bldg.hasPermitData['disaster']['number'])):
                if 'ROOF' in bldg.hasPermitData['disaster']['permit type'][p]:
                    # Reset area and area_factor:
                    area_factor, bldg_count = 0, 0
                    # First check to make sure this is a building-related roof permit:
                    if 'GAZ' in bldg.hasPermitData['disaster']['description'][p] or 'CANOP' in \
                            bldg.hasPermitData['disaster']['description'][p]:
                        pass
                    else:
                        # Note that there is a roof permit (at least one):
                        count += 1
                        rcover_damage_cat = None  # reset damage category for each new permit
                        # Check if parcel shares a parcel number ( > 1 buildings in lot):
                        for b in site.hasBuilding:
                            if (b.hasID == bldg.hasID or (
                                    b.hasLocation['Address'] == bldg.hasLocation['Address'])) and (
                                    'COND' not in b.hasOccupancy):
                                bldg_count += 1
                            else:
                                pass
                        if bldg_count > 1:
                            area_factor = bldg.hasGeometry['Total Floor Area'] / (
                                        bldg_count - 1)  # Used for quantitative desc
                        else:
                            area_factor = 1
                        # Now check if this is a quantitative roof permit description: i.e., tells us # of roof squares
                        desc = bldg.hasPermitData['disaster']['description'][p].split()
                        for i in range(0, len(desc)):
                            if desc[i].isdigit():
                                # Calculate the number of roof squares and percent roof cover damage:
                                num_roof_squares = float(desc[i]) * area_factor
                                rcover_damage_percent = self.rcover_damage_percent(bldg.hasGeometry['Total Floor Area'],
                                                                                   len(bldg.hasStory),
                                                                                   num_roof_squares, length_unit)
                                rcover_damage_cat = self.rcover_damage_cat(rcover_damage_percent)
                                break
                            else:
                                if 'SQ' in desc[i]:  # Case when there is no space between quantity and roof SQ
                                    num_roof_squares = float(desc[i][0:-2]) * area_factor
                                    rcover_damage_percent = self.rcover_damage_percent(
                                        bldg.hasGeometry['Total Floor Area'],
                                        len(bldg.hasStory),
                                        num_roof_squares, length_unit)
                                    rcover_damage_cat = self.rcover_damage_cat(rcover_damage_percent)
                                    break
                                else:
                                    pass
                        if rcover_damage_cat is None:
                            pass
                        else:
                            if count == 1:
                                data_details['value'] = rcover_damage_percent
                                data_details['hazard damage rating']['wind'] = rcover_damage_cat
                                self.hasDamagePrecision['component, range'] = False
                                self.hasDamagePrecision['component, discrete'] = True
                                data_details['available'] = True
                            elif count > 1:
                                if isinstance(data_details['value'], list):
                                    data_details['value'] = rcover_damage_percent
                                    data_details['hazard damage rating']['wind'] = rcover_damage_cat
                                    self.hasDamagePrecision['component, range'] = False
                                    self.hasDamagePrecision['component, discrete'] = True
                                else:
                                    if rcover_damage_percent > data_details['value']:
                                        data_details['value'] = rcover_damage_percent
                                        data_details['hazard damage rating']['wind'] = rcover_damage_cat
                                        self.hasDamagePrecision['component, range'] = False
                                        self.hasDamagePrecision['component, discrete'] = True
                            else:
                                pass
                                # If no quantitative descriptions available, then translate the qualitative description:
                        if data_details['value'] is None:
                            desc = bldg.hasPermitData['disaster']['description'][p]
                            rcover_damage_cat, rcover_damage_percent = self.rcover_percent_damage_qual(desc)
                            data_details['value'] = rcover_damage_percent
                            data_details['hazard damage rating']['wind'] = rcover_damage_cat
                            data_details['available'] = True
                            self.hasDamagePrecision['component, discrete'] = False
                            self.hasDamagePrecision['component, range'] = True
                        else:
                            if count > 1 and self.hasDamagePrecision['component, discrete'] == False:
                                desc = bldg.hasPermitData['disaster']['description'][p]
                                rcover_damage_cat, rcover_damage_percent = self.rcover_percent_damage_qual(desc)
                                if rcover_damage_cat > data_details['hazard damage rating']['wind']:
                                    data_details['hazard damage rating']['wind'] = rcover_damage_cat
                                    data_details['value'] = rcover_damage_percent
                                    self.hasDamagePrecision['component, discrete'] = False
                                    self.hasDamagePrecision['component, range'] = True
                            else:
                                pass
                elif 'DEM' in bldg.hasPermitData['disaster']['permit type'][p]:
                    if self.hasDamageScale['type'] == 'HAZUS-HM':
                        data_details['value'] = self.hasDamageScale['component damage states']['value'][3]
                        data_details['hazard damage rating']['wind'] = self.hasDamageScale['component damage states']['number'][3]
                        self.hasDamagePrecision['component, range'] = True
                        self.hasDamagePrecision['component, discrete'] = False
                        data_details['available'] = True
                else:
                    pass
        else:
            pass
        return data_details

    def rcover_damage_percent(self, total_area, stories, num_roof_squares, length_unit):
        """
        A function to translate roof square quantities into percentages of roof cover damage.

        :param total_area: The total floor area of the building.
        :param stories: The number of stories in the building.
        :param num_roof_squares: The number of roof squares specified in the permit description.
        :param length_unit: The length unit of measurement.
        :return: rcover_damage_percent: The percent of roof cover damage: roof square area/footprint area * 100
        """
        try:
            total_area = float(total_area)
        except:
            total_area = float(total_area.replace(',', ''))
        if float(stories) == 0:
            stories = 1
        else:
            stories = float(stories)
        floor_area = total_area / stories
        if length_unit == 'ft':
            roof_square = 100  # sq_ft
        elif length_unit == 'm':
            roof_square = 100 / 10.764  # sq m
        rcover_damage_percent = 100 * (roof_square * num_roof_squares / floor_area)
        if rcover_damage_percent > 100:
            rcover_damage_percent = 100
        else:
            pass
        return rcover_damage_percent

    def rcover_percent_damage_qual(self, desc):
        """
        A function to translate qualitative roof damage descriptions into a range of roof cover damage percentages
        using the specified damage scale.

        :param desc: The qualitative damage description.
        :return: rcover_damage_cat: The damage category (or measure) the roof cover damage description was translated to.
                 rcover_damage_percent: A list with two values: lower and upper percentages of roof cover damage.
        """
        substrings = ['RE-ROO', 'REROOF', 'ROOF REPAIR', 'COMMERCIAL HURRICANE REPAIRS',
                      'ROOF OVER', 'HURRICANE REPAIRS', 'ROOFOVER', 'HURRICANE RESIDENTIAL',
                      'HURRICANE REPAIR', 'REPAIR ROOF', 'OVER', 'REOOF']
        if self.hasDamageScale['type'] == 'HAZUS-HM':
            if any([substring in desc for substring in substrings]):
                rcover_damage_percent = [2, 15]
                rcover_damage_cat = self.rcover_damage_cat(rcover_damage_percent)
            elif 'REPLAC' in desc or 'REPALC' in desc:
                rcover_damage_percent = [15, 50]
                rcover_damage_cat = self.rcover_damage_cat(rcover_damage_percent)
            elif 'WITHDRAWN' in desc or 'UNAUTHORIZED' in desc:
                rcover_damage_percent = [0, 2]
                rcover_damage_cat = self.rcover_damage_cat(rcover_damage_percent)
            elif 'NEW' in desc:
                rcover_damage_percent = [50, 100]
                rcover_damage_cat = self.rcover_damage_cat(rcover_damage_percent)
            else:
                if 'ROOF' in desc or 'RESIDENTIAL' in desc:
                    # Assume damage state 1 (at least minor damage):
                    rcover_damage_percent = [2, 15]
                    rcover_damage_cat = self.rcover_damage_cat(rcover_damage_percent)
                else:
                    print('New roof permit qualitative damage description:' + desc)
                    # Assume lowest damage state (no damage):
                    rcover_damage_percent = [0, 2]
                    rcover_damage_cat = self.rcover_damage_cat(rcover_damage_percent)
        return rcover_damage_cat, rcover_damage_percent

    def rcover_damage_cat(self, rcover_damage):
        if isinstance(rcover_damage, list):
            if self.hasDamageScale['type'] == 'HAZUS-HM':
                if rcover_damage[0] == 0 and rcover_damage[1] == 2:
                    rcover_damage_cat = 0
                elif rcover_damage[0] == 2 and rcover_damage[1] == 15:
                    rcover_damage_cat = 1
                elif rcover_damage[0] == 15 and rcover_damage[1] == 50:
                    rcover_damage_cat = 2
                elif rcover_damage[0] == 50:
                    rcover_damage_cat = 3
            else:
                pass
        else:
            if self.hasDamageScale['type'] == 'HAZUS-HM':
                # Determine damage category based on percent damage:
                if rcover_damage <= 2:
                    rcover_damage_cat = 0
                elif 2 < rcover_damage <= 15:
                    rcover_damage_cat = 1
                elif 15 < rcover_damage <= 50:
                    rcover_damage_cat = 2
                elif rcover_damage > 50:
                    rcover_damage_cat = 3
                else:
                    pass
            else:
                pass
        return rcover_damage_cat

    def update_yr_of_construction(self, bldg, component_type, permit_data, event_year):
        # Update the year of construction for components or building:
        if 'ROOF' in permit_data['PERMITTYPE']:
            substrings = ['CANOPY', 'GAZ', 'BOAT', 'CAR', 'CLUB', 'GARAGE', 'PORCH', 'PATIO']
            if any([substring in permit_data['DESCRIPTION'].upper() for substring in substrings]):
                pass
            else:
                if 'NEW' in permit_data['PERMITSUBTYPE'] or 'REPLACEMENT' in permit_data[
                    'PERMITSUBTYPE']:  # Figure out what to do with roof-over
                    new_year = int(permit_data['ISSUED'][-4:])
                    if bldg.hasElement['Roof'].hasYearBuilt < new_year < event_year:
                        bldg.hasElement['Roof'].hasYearBuilt = new_year
                    else:
                        pass
        else:
            pass


class FemaIahrld(PostDisasterDamageDataset):
    def __init__(self):
        PostDisasterDamageDataset.__init__(self)
        self.hasDamagePrecision['component, discrete'] = False
        self.hasDamagePrecision['component, range'] = True
        self.hasLocationPrecision['zipcode/censusblock level'] = True
        self.hasAccuracy = True
        self.hasType['fema claims data'] = True

    def pull_fema_iahrld_data(self, event_name):
        """
        Function to query Individual Assistance Housing Registrants Large Disaster dataset from OpenFEMA and convert to
        DataFrame.

        :param event_name: String specifying the name of the disaster event
        :return: df_fema: A pandas DataFrame with the data for event_name
        """
        self.hasEventName = event_name
        api_endpoint = 'https://www.fema.gov/api/open/v1/IndividualAssistanceHousingRegistrantsLargeDisasters'
        if event_name == 'Hurricane Michael':
            disasterNumber = '4399'
        elif event_name == 'Hurricane Irma':
            disasterNumber = '4337'
        else:
            pass
        query = api_endpoint + '?$filter=disasterNumber eq ' + disasterNumber
        # Query data from API and convert to JSON to then convert to pandas DataFrame:
        JSONContent = requests.get(query).json()
        if len(JSONContent['IndividualAssistanceHousingRegistrantsLargeDisasters']) > 0:
            # Set up headers for pandas columns (i.e., key values in new_dict)
            new_dict = {}
            for key in JSONContent['IndividualAssistanceHousingRegistrantsLargeDisasters'][0]:
                new_dict[key] = []
            # Populate the data for each key:
            for row in JSONContent['IndividualAssistanceHousingRegistrantsLargeDisasters']:
                for key in row:
                    new_data = row[key]
                    try:  # String clean-up
                        new_data = new_data.upper()
                    except AttributeError:
                        pass
                    new_dict[key].append(new_data)
            # Convert to DataFrame:
            df_fema = pd.DataFrame(new_dict)
        else:
            df_fema = pd.DataFrame()
        return df_fema

    def add_fema_iahrld_data(self, bldg, component_type, hazard_type, damage_scale_name, df_fema):
        """

        :param bldg: Parcel or Building object with hasOccupancy attribute filled.
        :param component_type: String specifying the component type.
        :param hazard_type: String specifying the hazard type.
        :param site: Site object with hasBuildings attribute = list of parcel data models.
        :param length_unit: String specifying the length unit for the analysis (e.g. 'ft', 'm').
        :param damage_scale_name: String specifying the name of the damage scale that will be used for the semantic
                                  translation of data fields to component damage observations.
        :param df_fema: DataFrame with data from the Individual Assistance Housing Registrants Large Disaster
                        dataset for a given event.
        :return: data_details: Dictionary with information about data availability, dataset fidelity,
                               the component type, hazard type, and damage description.
                 df_sub: DataFrame with all available observations and their component-level damage
        """
        # Step 1: Populate data_details dictionary:
        # Step 2: Find the appropriate occupancy tag for this building:
        res_type = ''
        if bldg.isComm:
            # Global occupancy codes:
            if 'CONDO' in bldg.hasOccupancy.upper() and 'STOR' not in bldg.hasOccupancy.upper():
                res_type = 'CONDO'
            # Check if we need county-specific occupancy codes:
            if len(res_type) > 0:
                pass
            else:
                if bldg.hasLocation['County'].upper() == 'BAY':
                    if 'COMMON' in bldg.hasOccupancy.upper():
                        res_type = 'CONDO'
        else:  # Residential occupancy codes
            # Global occupancy codes:
            if 'SINGLE' in bldg.hasOccupancy.upper():
                res_type = 'HOUSE/DUPLEX'
            elif 'MOBILE' in bldg.hasOccupancy.upper():
                res_type = 'MOBILE HOME'
            elif 'APART' in bldg.hasOccupancy.upper() or 'MULTI' in bldg.hasOccupancy.upper():
                res_type = 'APARTMENT'
            elif 'AGED' in bldg.hasOccupancy.upper() or 'CONVEL' in bldg.hasOccupancy.upper():
                res_type = 'ASSISTED LIVING FACILITY'
            else:
                pass
            # Check if we need county-specific occupancy codes:
            if len(res_type) > 0:
                pass
            else:
                if bldg.hasLocation['County'].upper() == 'BAY':
                    pass
                elif bldg.hasLocation['County'].upper() == 'COLLIER':
                    pass
                elif bldg.hasLocation['County'].upper() == 'MONROE':
                    pass
                else:
                    pass
        # Step 3: Search the DataFrame for similar buildings:
        res_types = ['APARTMENT', 'HOUSE/DUPLEX', 'TOWNHOUSE', 'MOBILE HOME', 'CONDO', 'OTHER', 'MILITARY HOUSING',
                     'BOAT', 'ASSISTED LIVING FACILITY']
        # Find subset of dataset with damage observations for the given occupancy, hazard, and component:
        dbldg_lst = []
        if len(res_type) > 0:
            if hazard_type == 'wind' and ('roof' in component_type):
                # Find the subset of the dataset corresponding to roof damage for the occupancy class:
                df_sub = df_fema.loc[(df_fema['roofDamage'] == True) & (df_fema['residenceType'] == res_type)]
                if len(df_sub) > 0:
                    # Extract damage descriptions:
                    for row in range(0, len(df_sub['damagedZipCode'])):
                        data_details = {'available': False, 'fidelity': self, 'component type': component_type,
                                        'hazard type': hazard_type, 'value': None}
                        # Specify the damage scale that will be used to do semantic translations of damage:
                        if damage_scale_name == 'HAZUS-HM':
                            self.get_damage_scale(damage_scale_name, component_type, global_flag=True,
                                                  component_flag=True)
                        else:
                            # Populate default damage scale information to force development of mapping function:
                            self.get_damage_scale('FEMA IHARLD', component_type, global_flag=True, component_flag=True)
                        # Import necessary modules:
                        from shapely.geometry import Point
                        from OBDM.zone import Building, Story
                        from OBDM.element import Roof
                        # Create a new parcel data model and add location data:
                        new_parcel = Building()
                        new_parcel.hasLocation['Zip Code'] = df_sub['damagedZipCode'][row]
                        new_parcel.hasLocation['City'] = df_sub['damagedCity'][row].upper()
                        new_parcel.hasLocation['State'] = df_sub['damagedStateAbbreviation'][row].upper()
                        new_parcel.hasOccupancy = df_sub['residenceType'][row].upper()
                        # Find latitude/longitude information:
                        df_geo = pd.read_csv('C:/Users/Karen/Desktop/FClaims_locs.csv')
                        idx = df_geo.loc[
                            df_geo['CITY'] == new_parcel.hasLocation['City'] & df_geo['ZIP'] == new_parcel.hasLocation[
                                'Zip Code']].index.to_list()
                        new_parcel.hasLocation['Geodesic'] = Point(df_geo['LONGITUDE'][idx], df_geo['LATITUDE'][idx])
                        # Add story and height information:
                        if res_type != 'CONDO':
                            new_parcel.hasStory.append(Story())
                            new_parcel.hasGeometry['Height'] = bldg.hasGeometry['Height'] / len(bldg.hasStory)
                        else:
                            # Assume a three story structure for condominium buildings:
                            new_parcel.hasStory = [Story(), Story(), Story()]
                            new_parcel.hasGeometry['Height'] = len(new_parcel.hasStory) * (
                                        bldg.hasGeometry['Height'] / len(bldg.hasStory))
                        # Create Roof element and add information:
                        new_roof = Roof()
                        new_roof.hasCover = bldg.hasElement['Roof'][0].hasCover
                        new_roof.hasType = bldg.hasElement['Roof'][0].hasCover
                        new_parcel.hasStory[-1].adjacentElement['Roof'] = [new_roof]
                        new_parcel.hasStory[-1].update_elements()
                        new_parcel.update_zones()
                        new_parcel.update_elements()
                        # Designating component-level damage:
                        for row in range(0, len(df_sub)):
                            if df_sub['destroyed'][row]:
                                data_details['value'] = self.hasDamageScale['component damage states']['value'][4]
                            else:
                                if not df_sub['floodDamage'][row]:
                                    if 'roof' in component_type:
                                        if not df_sub['habitabilityRepairsRequired'][row] and df_sub['ppfvl'][row] == 0:
                                            data_details['value'] = \
                                            self.hasDamageScale['component damage states']['value'][1]
                                        elif not df_sub['habitabilityRepairsRequired'][row] and df_sub['ppfvl'][
                                            row] > 0:
                                            data_details['value'] = \
                                            self.hasDamageScale['component damage states']['value'][2]
                                        elif df_sub['habitabilityRepairsRequired'][row] and df_sub['ppfvl'][row] > 0:
                                            data_details['value'] = \
                                            self.hasDamageScale['component damage states']['value'][3]
                                    else:
                                        print('Only roof components supported at this time')
                                else:
                                    print('Flood damage descriptions currently not supported')
                            new_parcel.hasElement['Roof'][0].hasDamageData = data_details
                            new_parcel.hasDamageData['roof cover'] = new_parcel.hasElement['Roof'][0].hasDamageData
                            dbldg_lst.append(new_parcel)
                else:
                    print('No IA Dataset observations for the case study parcel')
            else:
                print('Hazard and component type not currently supported')
        else:
            print('No IA Dataset observations for the case study parcel')
        return dbldg_lst


class FemaHma(PostDisasterDamageDataset):
    def __init__(self):
        PostDisasterDamageDataset.__init__(self)
        self.hasDamagePrecision['component, discrete'] = False
        self.hasDamagePrecision['component, range'] = True
        self.hasLocationPrecision['zipcode/censusblock level'] = True
        self.hasAccuracy = True
        self.hasType['fema claims data'] = True

    def pull_fema_hma_data(self, event_name):
        """
        Function to query Hazard Mitigation Assistance Mitigated Properties dataset from OpenFEMA and convert to
        DataFrame. Reports damage observations (i.e., damageCategory data field != 'N/A').

        :param event_name: String specifying the name of the disaster event.
        :return: df_fema: DataFrame with damage observations for the event_name.
        """
        self.hasEventName = event_name
        api_endpoint = 'https://www.fema.gov/api/open/v2/HazardMitigationAssistanceMitigatedProperties'
        if event_name == 'Hurricane Michael':
            disasterNumber = '4399'
        elif event_name == 'Hurricane Irma':
            disasterNumber = '4337'
        else:
            pass
        query = api_endpoint + '?$filter=disasterNumber eq ' + disasterNumber
        # Query data from API and convert to JSON to then convert to pandas DataFrame:
        JSONContent = requests.get(query).json()
        if len(JSONContent['HazardMitigationAssistanceMitigatedProperties']) > 0:
            # Set up headers for pandas columns (i.e., key values in new_dict)
            new_dict = {}
            for key in JSONContent['HazardMitigationAssistanceMitigatedProperties'][0]:
                new_dict[key] = []
            # Populate the data for each key:
            for row in JSONContent['HazardMitigationAssistanceMitigatedProperties']:
                for key in row:
                    new_data = row[key]
                    try:  # String clean-up
                        new_data = new_data.upper()
                    except AttributeError:
                        pass
                    new_dict[key].append(new_data)
            # Convert to DataFrame:
            df_fema = pd.DataFrame(new_dict)
            # Remove any rows that do not pertain to damage observations:
            df_fema.drop(df_fema[df_fema['damageCategory'] == 'N/A'].index, axis=0, inplace=True)
            df_fema.reset_index()
        else:
            df_fema = pd.DataFrame()
            print('No data currently available for this event via API')
        return df_fema

    def add_fema_hma_data(self, bldg, component_type, hazard_type, df_fema, hazard_file_path):
        """
        A function to find damage observations within the Hazard Mitigation Assistance Mitigated Properties dataset.

        :param bldg: Parcel or Building object with hasOccupancy attribute filled.
        :param component_type: String specifying the component type.
        :param hazard_type: String specifying the hazard type.
        :param df_fema: DataFrame with data from the Hazard Mitigation Assistance dataset for a given event.
        :return: df_sub: DataFrame with all "representative" data entries for bldg, hazard, component type
        """
        # First find the appropriate residence type for the query:
        # Note: HMA Buildings are typically govt. bldgs, schools, critical facilities, churches, residential bldgs.
        # Rule-sets listed here are meant to identify building with one of the above subsets.
        # All other occupancy types are not valid for use of this data.
        struc_type = ''
        if bldg.isComm:
            # Global commercial occupancy codes (substrings):
            comm_types = ['CHURCH', 'HOSPITAL', 'MEDICAL', 'SCHOOL', 'CAMPUS']
            if any([substring in bldg.hasOccupancy.upper() for substring in comm_types]):
                struc_type = 'NON-RESIDENTIAL'
            else:
                pass
            # Check if we need county-specific occupancy codes:
            if len(struc_type) > 0:
                pass
            else:
                if bldg.hasLocation['County'].upper() == 'BAY':
                    if 'MUNICIPAL' in bldg.hasOccupancy.upper() or 'COUNTY' in bldg.hasOccupancy.upper():
                        struc_type = 'NON-RESIDENTIAL - PUBLIC'
                elif bldg.hasLocation['County'].upper() == 'COLLIER' or bldg.hasLocation['County'].upper() == 'MONROE':
                    if 'COUNT' in bldg.hasOccupancy.upper():
                        struc_type = 'NON-RESIDENTIAL - PUBLIC'
                else:
                    pass
        else:  # Residential occupancy codes
            # Global occupancy codes:
            if 'SINGLE' in bldg.hasOccupancy.upper():
                struc_type = 'SINGLE FAMILY'
            else:
                pass
            # Check if we need county-specific occupancy codes:
            if len(struc_type) > 0:
                pass
            else:
                if bldg.hasLocation['County'].upper() == 'BAY':
                    if 'MOBILE' in bldg.hasOccupancy.upper():
                        struc_type = 'MANUFACTURED HOME'
                    elif 'MULTI-FAM' in bldg.hasOccupancy.upper():
                        struc_type = 'MULTI-FAMILY DWELLING - 5 OR MORE UNITS'
                elif bldg.hasLocation['County'].upper() == 'COLLIER':
                    pass
                elif bldg.hasLocation['County'].upper() == 'MONROE':
                    pass
                else:
                    pass
        # Find subset of dataset with damage observations for the given occupancy:
        if len(struc_type) > 0:
            structure_types = ['SINGLE FAMILY', 'NON-RESIDENTIAL - PUBLIC', '2-4 FAMILY', 'MANUFACTURED HOME',
                               'NON-RESIDENTIAL - PRIVATE', 'MULTI-FAMILY DWELLING - 5 OR MORE UNITS']
            # Check if there are damage observations for the parcel's occupancy type:
            if any([substring in struc_type for substring in structure_types]):
                df_sub = df_fema.loc[(df_fema['structureType'] == struc_type)]
            else:
                # Get all entries that are either non-residential private or public:
                df_sub = df_fema.loc[(df_fema['structureType'] == 'NON-RESIDENTIAL - PRIVATE') | (
                            df_fema['structureType'] == 'NON-RESIDENTIAL - PUBLIC')]
            if len(df_sub) > 0:
                # Find subset of dataset specific to the given hazard, component:
                if hazard_type == 'wind':
                    # Find buildings with wind retrofit actions listed:
                    df_sub = df_sub[df_sub['propertyAction'].str.contains('WIND RETROFIT')]
                    # Final (component-specific) filter:
                    if 'roof' in component_type:
                        # Drop any observations specific to storm shutters:
                        df_sub.drop(df_sub[df_sub['title'].str.contains('SHUTTER')].index, inplace=True)
                        df_sub = df_sub.reset_index(drop=True)
                        self.create_hma_data_models(bldg, df_sub, component_type, hazard_type, hazard_file_path)
                    elif component_type == 'window':
                        df_sub = df_sub[df_sub['title'].str.contains('SHUTTER')]
                    else:
                        print('Component type not supported')
                else:
                    print('Hazards other than wind not currently supported')
            else:
                pass
        return df_sub

    def create_hma_data_models(self, bldg, df_sub, component_type, hazard_type, hazard_file_path):
        # Import necessary modules:
        from shapely.geometry import Point
        from OBDM.zone import Building, Story
        from OBDM.element import Roof
        from create_fragility import get_wind_speed
        # Loop through data entries, create building data models and populate location + hazard info:
        hma_bldg_list = []
        hazard_list = []
        for row in range(0, len(df_sub['damageCategory'])):
            for prop in range(0, df_sub['numberOfProperties'][row] + 1):
                data_details = {'available': True, 'fidelity': self,
                                'component type': component_type,
                                'hazard type': hazard_type, 'value': None}
                # Create a new parcel data model and add location data:
                new_parcel = Building()
                new_parcel.hasLocation['Zip Code'] = df_sub['zip'][row]
                new_parcel.hasLocation['City'] = df_sub['city'][row].upper()
                new_parcel.hasLocation['County'] = df_sub['county'][row].upper()
                new_parcel.hasLocation['State'] = df_sub['state'][row].upper()
                new_parcel.hasOccupancy = df_sub['structureType'][row].upper()
                # Find latitude/longitude information:
                df_geo = pd.read_csv('C:/Users/Karen/PycharmProjects/DPBWE/Datasets/Geodesic/FClaims_locs.csv')
                idx = df_geo.loc[(df_geo['CITY'] == new_parcel.hasLocation['City']) & (
                        df_geo['ZIP'] == new_parcel.hasLocation['Zip Code'])].index.to_list()
                new_parcel.hasLocation['Geodesic'] = Point(df_geo['LONGITUDE'][idx], df_geo['LATITUDE'][idx])
                # Add story and height information (currently based off of bldg features):
                new_parcel.hasStory.append(Story())
                new_parcel.hasGeometry['Height'] = bldg.hasGeometry['Height'] / len(bldg.hasStory)
                # Create Roof element and add information:
                new_roof = Roof()
                new_roof.hasCover = bldg.hasElement['Roof'][0].hasCover
                new_roof.hasType = bldg.hasElement['Roof'][0].hasCover
                new_parcel.hasStory[-1].adjacentElement['Roof'] = [new_roof]
                new_parcel.hasStory[-1].update_elements()
                new_parcel.update_zones()
                new_parcel.update_elements()
                # Now find this building's hazard intensity information: Basic wind speed in this case
                if hazard_type == 'wind':
                    get_wind_speed(new_parcel, hazard_file_path, exposure='C', unit='english')
                    hazard_list.append(new_parcel.hasDemand['wind speed'])
                else:
                    pass
                # Add damage data:
                # Populate damage scale information:
                self.get_damage_scale('FEMA HMA', component_type, global_flag=True, component_flag=True)
                if '49' in df_sub['damageCategory'][row]:
                    data_details['value'] = self.hasDamageScale['global damage states']['value'][0]
                elif '99' in df_sub['damageCategory'][row]:
                    data_details['value'] = self.hasDamageScale['component damage states']['value'][1]
                else:  # Total loss
                    data_details['value'] = self.hasDamageScale['component damage states']['value'][2]
                new_parcel.hasElement['Roof'][0].hasDamageData = data_details
                new_parcel.hasDamageData['roof cover'] = new_parcel.hasElement['Roof'][0].hasDamageData
                hma_bldg_list.append(new_parcel)
        # Create a histogram to help the user in their designation of damage measures:
        from scipy.stats.distributions import norm, lognorm
        from seaborn import kdeplot
        import numpy as np
        # Use Kernel Density Estimation to fit the data and extract resulting values:
        kde = kdeplot(hazard_list)
        line = kde.lines[0]
        x, y = line.get_data()
        # Plot the data and its KDE plot:
        fig, ax = plt.subplots()
        ax.plot(x, y)
        # Let's try calculating the gradient:
        step_size = x[1] - x[0]
        grad = np.gradient(y, step_size)
        grad_zero = np.where(grad == 0)
        # And calculate the slope to make sure we get
        # Adding in here braindump of fit code:
        shape, loc, scale = lognorm.fit(hazard_list)
        x = np.linspace(min(np.array(hazard_list)), max(np.array(hazard_list)))
        log_pdf = lognorm.pdf(x, shape, loc, scale)
        plt.plot(x, log_pdf)
        from matplotlib import rcParams
        rcParams['font.family'] = "Times New Roman"
        rcParams.update({'font.size': 12})
        plt.hist(hazard_list, bins=20)
        plt.ylabel('Frequency')
        if hazard_type == 'wind':
            plt.xlabel('Wind speed [mph]')
        else:
            pass
        plt.show()
        # Plot the final cdf:
        y = lognorm.cdf(x, shape, loc, scale)
        inv_y = 1 - y
        plt.plot(x, y, label='P(X >= x), DS1')
        plt.show()
        return hma_bldg_list

    def assign_hma_dms(self, hma_bldg_list, spatial_filter, translate_to, component_type):
        # Use spatial filter to remove non-applicable buildings:
        for b in hma_bldg_list:
            if b.hasLocation['Geodesic'].within(spatial_filter):
                dm_idx = self.hasDamageScale['global damage states']['value'].index(b.hasDamage)
                if component_type == 'roof cover':
                    b.hasElement['Roof'][0].hasDamageData['value'], b.hasDamageData['roof cover'] = translate_to[dm_idx]
                else:
                    pass
            else:
                pass

    def find_fit_(self):
        pass
