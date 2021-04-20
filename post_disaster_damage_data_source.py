import pandas as pd
import requests


class PostDisasterDamageDataset:

    def __init__(self):
        self.hasDamagePrecision = {'component, discrete': False, 'component, range': False, 'building, discrete': False, 'building, range': False}
        self.hasLocationPrecision = {'exact location': False, 'street level': False, 'city/town level': False, 'zipcode/censusblock level': False}
        self.hasAccuracy = False
        self.hasCurrentness = False
        self.hasReliability = False
        self.hasDate = '00/00/0000'
        self.hasDamageScale = {'type': '', 'damage states': {}}
        self.hasHazard = {'wind': False, 'tree': False, 'rain': False, 'wind-borne debris': False, 'flood': False, 'surge': False}
        self.hasType = {'field observations': False, 'permit data': False, 'crowdsourced': False,
                        'remote sensing/imagery': False, 'fema modeled assessment': False, 'fema claims data': False}
        self.hasEventName = ''
        self.hasEventYear = '00/00/0000'
        self.hasEventLocation = {'city': '', 'county': '', 'state': '', 'country': ''}

    def get_damage_scale(self, damage_scale_name, component_type, damage_states=None, values=None):
        if damage_scale_name == 'HAZUS-HM':
            self.hasDamageScale['type'] = 'HAZUS-HM'
            dstate_list = [1, 2, 3, 4, 5]
            for state in dstate_list:
                self.hasDamageScale['damage states'][state] = None
            if component_type == 'roof cover':
                dstate_values = [[0, 2], [2, 15], [15, 50], [50, 100], [50, 100]]
                for key in dstate_list:
                    self.hasDamageScale['damage states'][key] = dstate_values[key-1]
            else:
                pass
        else:
            self.hasDamageScale['type'] = damage_scale_name
            for i in range(0, len(damage_states)):
                self.hasDamageScale['damage states'][damage_states[i]] = values[i]


class STEER(PostDisasterDamageDataset):
    def __init__(self):
        PostDisasterDamageDataset.__init__(self)
        self.hasDamagePrecision['component, discrete'] = True
        self.hasDamagePrecision['building, range'] = True
        self.hasLocationPrecision['exact location'] = True
        self.hasLocationPrecision['street level'] = True
        self.hasAccuracy = True
        self.hasType['field observations'] = True

    def add_steer_data(self, bldg, component_type, hazard_type, steer_file_path):
        # Load the StEER Dataset:
        df_steer = pd.read_csv(steer_file_path)
        df_steer['address_full'] = df_steer['address_full'].str.lower().replace(' ', '')  # Data clean-up
        df_steer['address_full'] = df_steer['address_full'].str.replace(' ', '')
        # Define the parcel identifier:
        # Parcel identifier should be the parcel's address in the following format (not case-sensitive):
        # 1842 BRIDGE ST Panama City BAY FL 32409 USA (number, street, city, county, state, zip, country)
        parcel_identifier = bldg.hasLocation['Street Number'] + ' ' + bldg.hasLocation['City'] + ' ' + bldg.hasLocation['County'] + ' ' + bldg.hasLocation['State'] + ' ' + bldg.hasLocation['Zip Code'] + ' USA'
        parcel_identifier = parcel_identifier.lower().replace(' ', '')  # Data clean-up
        # Set up dictionary with details of data for this bldg, component, hazard:
        data_details = {'available': False, 'fidelity': self, 'component type': component_type,
                        'hazard type': hazard_type,
                        'value': None, 'hazard damage rating': {'wind': None, 'surge': None, 'rain': None}}
        try:
            # Check if the parcel has a StEER observation at its exact location:
            idx = df_steer.loc[df_steer['address_full'] == parcel_identifier].index[0]
            self.hasDate = df_steer['date'][idx]
            # Update the Location Precision attribute:
            self.hasLocationPrecision['street level'] = False
            # Extract StEER damage data:
            for key in self.hasHazard:
                if key in df_steer['hazards_present'][idx].lower():
                    self.hasHazard[key] = True
            data_details['hazard damage rating']['wind'] = df_steer['wind_damage_rating'][idx]
            data_details['hazard damage rating']['surge'] = df_steer['surge_damage_rating'][idx]
            data_details['hazard damage rating']['rain'] = df_steer['rainwater_ingress_damage_rating'][idx]
            # Update building and component-level attributes:
            bldg.hasStructuralSystem = df_steer['mwfrs'][idx]
            #bldg.hasElement['Roof'].hasCover = df_steer['roof_cover'][idx]
            bldg.hasElement['Roof'][0].hasShape[df_steer['roof_shape'][idx].lower()] = True
            if bldg.hasElement['Roof'][0].hasPitch is None:
                bldg.hasElement['Roof'][0].hasPitch = df_steer['roof_slope'][idx]
            if bldg.hasElement['Roof'][0].hasYearBuilt is not None:
                if int(df_steer['reroof_year'][idx]) > bldg.hasElement['Roof'][0].hasYearBuilt:
                    bldg.hasElement['Roof'][0].hasYearBuilt = int(df_steer['reroof_year'][idx])
            # Extract component-level damage descriptions if the desired hazard is present:
            if self.hasHazard[hazard_type]:
                # Extract component-level damage descriptions:
                if component_type == 'roof cover':
                    # Check if there are roof-related damage descriptions:
                    if df_steer['roof_cover_damage_'][idx] > 0:
                        data_details['available'] = True
                        data_details['value'] = df_steer['roof_cover_damage_'][idx]
                        # Update the damage data details:
                        self.get_damage_scale('HAZUS-HM', 'roof cover', damage_states=None, values=None)
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

    def add_disaster_permit_data(self, bldg, component_type, hazard_type, site,
                                 permit_file_path, length_unit, damage_scale_name):
        # First activate the damage scale that will be used:
        self.get_damage_scale(damage_scale_name, component_type, damage_states=None, values=None)
        # Permit data can be leveraged to inform the presence of disaster-related damage
        # To bring in permit data, there needs to be a way to map permit number to parcel
        # E.g., the permit may be listed in the parcel's property listing or
        # the permit database may have the parcel's address
        # Load the disaster permit data:
        df = pd.read_csv(permit_file_path, encoding='unicode_escape')
        # Find disaster permit descriptions for the parcel:
        if len(bldg.hasPermitData['disaster']['number']) > 0:
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
        else:
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
                    else:
                        self.hasDate = df['ISSUED'][i]
            except IndexError:
                pass  # No disaster permits available for this parcel
        # Find the component damage using the permit description:
        if len(bldg.hasPermitData['disaster']['number']) > 0:
            data_details = self.get_dis_permit_damage(bldg, component_type, hazard_type, site, length_unit)
        else:
            data_details = {'available': False, 'fidelity': self, 'component type': component_type,
                            'hazard type': hazard_type,
                            'value': None, 'hazard damage rating': {'wind': None, 'surge': None, 'rain': None}}
        return data_details

    def get_dis_permit_damage(self, bldg, component_type, hazard_type, site, length_unit):
        data_details = {'available': False, 'fidelity': self, 'component type': component_type,
                        'hazard type': hazard_type,
                        'value': None, 'hazard damage rating': {'wind': None, 'surge': None, 'rain': None}}
        # Allocate empty lists to gather damage information:
        if component_type == 'roof cover' and hazard_type == 'wind':
            # Loop through the bldg's disaster permits:
            count = 0  # dummy variable to flag multiple roof permits in a parcel
            for p in range(0, len(bldg.hasPermitData['disaster']['number'])):
                if 'ROOF' in bldg.hasPermitData['disaster']['permit type'][p]:
                    # First check to make sure this is a building-related roof permit:
                    if 'GAZ' in bldg.hasPermitData['disaster']['description'][p] or 'CANOPY' in bldg.hasPermitData['disaster']['description'][p]:
                        pass
                    else:
                        # Note that there is a roof permit (at least one):
                        count += 1
                        rcover_damage_cat = None  # reset damage category for each new permit
                        # Check if parcel shares a parcel number ( > 1 buildings in lot):
                        area = bldg.hasGeometry['Total Floor Area']
                        for b in site.hasBuilding:
                            if b.hasID == bldg.hasID:
                                area += b.hasGeometry['Total Floor Area']
                            else:
                                pass
                        area_factor = bldg.hasGeometry['Total Floor Area'] / area  # Used for quantitative desc
                        # Now check if this is a quantitative roof permit description: i.e., tells us # of roof squares
                        desc = bldg.hasPermitData['disaster']['description'][p].split()
                        for i in range(0, len(desc)):
                            if desc[i].isdigit():
                                # Calculate the number of roof squares and percent roof cover damage:
                                num_roof_squares = float(desc[i]) * area_factor
                                rcover_damage_percent = self.rcover_damage_percent(bldg.hasGeometry['Total Floor Area'], len(bldg.hasStory),
                                                                                      num_roof_squares, length_unit)
                                rcover_damage_cat = self.rcover_damage_cat(rcover_damage_percent)
                                break
                            else:
                                if 'SQ' in desc[i]:  # Case when there is no space between quantity and roof SQ
                                    num_roof_squares = float(desc[i][0:-2]) * area_factor
                                    rcover_damage_percent = self.rcover_damage_percent(bldg.hasGeometry['Total Floor Area'],
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
                                # If no quantiative descriptions available, then convert the qualitative description:
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
                else:
                    pass
        else:
            pass
        return data_details

    def rcover_damage_percent(self, total_area, stories, num_roof_squares, unit):
        try:
            total_area = float(total_area)
        except:
            total_area = float(total_area.replace(',', ''))
        if float(stories) == 0:
            stories = 1
        else:
            stories = float(stories)
        floor_area = total_area / stories
        if unit == 'ft':
            roof_square = 100  # sq_ft
        elif unit == 'm':
            roof_square = 100 / 10.764  # sq m
        rcover_damage_percent = 100 * (roof_square * num_roof_squares / floor_area)
        if rcover_damage_percent > 100:
            rcover_damage_percent = 100
        else:
            pass
        return rcover_damage_percent

    def rcover_percent_damage_qual(self, desc):
        substrings = ['RE-ROO', 'REROOF', 'ROOF REPAIR', 'COMMERCIAL HURRICANE REPAIRS',
                      'ROOF OVER']
        if self.hasDamageScale['type'] == 'HAZUS-HM':
            if any([substring in desc for substring in substrings]):
                rcover_damage_percent = [2, 15]
                rcover_damage_cat = self.rcover_damage_cat(rcover_damage_percent)
            elif 'REPLACE' in desc:
                rcover_damage_percent = [15, 50]
                rcover_damage_cat = self.rcover_damage_cat(rcover_damage_percent)
            elif 'WITHDRAWN' in desc:
                rcover_damage_percent = [0, 2]
                rcover_damage_cat = self.rcover_damage_cat(rcover_damage_percent)
            elif 'NEW' in desc:
                rcover_damage_percent = [50, 100]
                rcover_damage_cat = self.rcover_damage_cat(rcover_damage_percent)
            else:
                print(desc)
                rcover_damage_cat = 'Unknown'
                rcover_damage_percent = 'Unknown'
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
                if 'NEW' in permit_data['PERMITSUBTYPE'] or 'REPLACEMENT' in permit_data['PERMITSUBTYPE']:  # Figure out what to do with roof-over
                    new_year = int(permit_data['ISSUED'][-4:])
                    if bldg.hasElement['Roof'].hasYearBuilt < new_year < event_year:
                        bldg.hasElement['Roof'].hasYearBuilt = new_year
                    else:
                        pass
        else:
            pass


class FemaIhaLd(PostDisasterDamageDataset):
    def __init__(self):
        PostDisasterDamageDataset.__init__(self)
        self.hasDamagePrecision['component, discrete'] = True
        self.hasDamagePrecision['component, range'] = True
        self.hasLocationPrecision['zipcode/censusblock level'] = True
        self.hasAccuracy = True
        self.hasType['fema claims data'] = True

    def add_fema_iha_ld_data(self, sim_bldg, component_type, hazard_type, event_name):
        api_endpoint = 'https://www.fema.gov/api/open/v1/IndividualAssistanceHousingRegistrantsLargeDisasters'
        if hazard_type == 'wind':
            if event_name == 'Hurricane Michael':
                disasterNumber = '4399'
            else:
                pass
        query = api_endpoint + '?$filter=disasterNumber eq ' + disasterNumber
        response = requests.get(query)
        if response.status_code != '200' or response.status_code != '300':
            print('API request failed')
        else:
            pass
