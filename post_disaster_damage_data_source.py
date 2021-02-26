import pandas as pd


class PostDisasterDamageDataSource:

    def __init__(self):
        self.hasDamagePrecision = {'component, discrete': False, 'component, range': False, 'building, discrete': False, 'building, range': False}
        self.hasLocationPrecision = {'exact location': False, 'street level': False, 'city/town level': False, 'zipcode/censusblock level': False}
        self.hasAccuracy = False
        self.hasDamageScale = {'type': '', 'damage states': {}}
        self.hasDate = str()
        self.hasHazard = {'wind': False, 'tree': False, 'rain': False, 'wind-borne debris': False, 'flood': False, 'surge': False}
        self.hasType = {'field observations': False, 'permit data': False, 'crowdsourced': False,
                        'remote-sensing/imagery': False, 'fema modeled assessment': False, 'fema claims data': False}

    def get_damage_scale(self, damage_scale_name, component_type, damage_states=None, values=None):
        if damage_scale_name == 'HAZUS-HM':
            self.hasDamageScale['type'] = 'HAZUS-HM'
            dstate_list = [1, 2, 3, 4, 5]
            for state in dstate_list:
                self.hasDamageScale['damage states'][state] = None
            if component_type == 'roof cover':
                dstate_values = [[0, 2], [2, 15], [15, 50], [50, 100], [50, 100]]
                for j in range(0, len(dstate_values)):
                    self.hasDamageScale['damage_states'][j] = dstate_values[j]
            else:
                pass
        else:
            self.hasDamageScale['type'] = damage_scale_name
            for i in range(0, len(damage_states)):
                self.hasDamageScale['damage states'][damage_states[i]] = values[i]


class STEER(PostDisasterDamageDataSource):
    def __init__(self):
        PostDisasterDamageDataSource.__init__(self)
        self.hasDamagePrecision['component, discrete'] = True
        self.hasDamagePrecision['building, range'] = True
        self.hasLocationPrecision['exact location'] = True
        self.hasLocationPrecision['street level'] = True
        self.hasAccuracy = True
        self.hasType['field observations'] = True

    def add_steer_data(self, bldg, component_type, hazard_type, steer_file_path):
        parcel_identifier = bldg.hasLocation['Address']
        # Parcel identifier should be the parcel's address in the following format (not case-sensitive):
        # 1842 BRIDGE ST Panama City BAY FL 32409 USA (number, street, city, county, state, zip, country)
        df_steer = pd.read_csv(steer_file_path)
        data_details = {'available': False, 'fidelity': None, 'component type': component_type,
                        'hazard type': hazard_type,
                        'value': None, 'hazard damage rating': {'wind': None, 'surge': None, 'rain': None}}
        try:
            # Check if the parcel has a StEER observation at its exact location:
            idx = df_steer.loc[df_steer['address_full'].lower() == parcel_identifier.lower()].index[0]
            # Update the Location Precision attribute:
            self.hasLocationPrecision['street level'] = False
            # Extract StEER damage data:
            for key in self.hasHazard:
                if key in df_steer['hazards_present'].lower():
                    self.hasHazard[key] = True
            data_details['hazard_damage_rating']['wind'] = df_steer['wind_damage_rating'][idx]
            data_details['hazard_damage_rating']['surge'] = df_steer['surge_damage_rating'][idx]
            data_details['hazard_damage_rating']['rain'] = df_steer['rainwater_damage_rating'][idx]
            # Update building and component-level attributes:
            bldg.hasStructuralSystem = df_steer['mwfrs'][idx]
            bldg.hasElement['Roof'].hasCover = df_steer['roof_cover'][idx]
            bldg.hasElement['Roof'].hasShape[df_steer['roof_shape'][idx].lower()] = True
            bldg.hasElement['Roof'].hasPitch = df_steer['roof_slope'][idx]
            if int(df_steer['reroof_year'][idx]) > bldg.hasElement['Roof'].hasYearBuilt:
                bldg.hasElement['Roof'].hasYearBuilt = int(df_steer['reroof_year'][idx])
            else:
                pass
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
                        data_details['fidelity'] = self
            else:
                pass
        except IndexError:  # No StEER entry exists for this exact location: Check General Area or does not exist
            pass
        return data_details


class BayCountyPermits(PostDisasterDamageDataSource):
    def __init__(self):
        PostDisasterDamageDataSource.__init__(self)
        self.hasDamagePrecision['component, discrete'] = True
        self.hasDamagePrecision['component, range'] = True
        self.hasLocationPrecision['exact location'] = True
        self.hasAccuracy = False
        self.hasType['permit data'] = True
