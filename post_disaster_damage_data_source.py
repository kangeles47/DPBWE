import pandas as pd


class PostDisasterDamageDataSource:

    def __init__(self):
        self.hasDamagePrecision = {'component, discrete': False, 'component, range': False, 'building, discrete': False, 'building, range': False}
        self.hasLocationPrecision = {'exact location': False, 'street level': False, 'city/town level': False, 'zipcode/censusblock level': False}
        self.hasAccuracy = False
        self.hasDamageScale = {'type': '', 'damage states': {'description': list(), 'value': list()}}
        self.hasDate = str()
        self.hasHazard = {'wind': False, 'tree': False, 'rain': False, 'wind-borne debris': False, 'flood': False, 'surge': False}


class STEER(PostDisasterDamageDataSource):
    def __init__(self):
        PostDisasterDamageDataSource.__init__(self)
        self.hasDamagePrecision['component, discrete'] = True
        self.hasDamagePrecision['building, range'] = True
        self.hasLocationPrecision['exact location'] = True
        self.hasLocationPrecision['street level'] = True
        self.hasAccuracy = True
        self.hasDamageScale['type'] = 'HAZUS-HM'
        self.hasDamageScale['description'] = ['No Damage', 'Minor Damage', 'Moderate Damage', 'Severe Damage', 'Destruction']

    def add_steer_data(self, bldg, steer_file_path):
        parcel_identifier = bldg.hasLocation['Address']
        # Parcel identifier should be the parcel's address in the following format (not case-sensitive):
        # 1842 BRIDGE ST Panama City BAY FL 32409 USA (number, street, city, county, state, zip, country)
        df_steer = pd.read_csv(steer_file_path)
        try:
            # Check if the parcel has a StEER observation at its exact location:
            idx = df_steer.loc[df_steer['address_full'].lower() == parcel_identifier.lower()].index[0]
            # Update the Location Precision attribute:
            self.hasLocationPrecision['street level'] = False
            # Extract StEER damage data:
            for key in self.hasHazard:
                if key in df_steer['hazards_present'].lower():
                    self.hasHazard[key] = True
            bldg.hasDamageData['wind damage rating'] = df_steer['wind_damage_rating'][idx]
            bldg.hasElement['Roof'].hasShape[df_steer['roof_shape'][idx].lower()] = True
            bldg.hasElement['Roof'].hasPitch = df_steer['roof_slope'][idx]
            bldg.hasStructuralSystem = df_steer['mwfrs'][idx]
            bldg.hasElement['Roof'].hasCover = df_steer['roof_cover'][idx]
            bldg.hasDamageData['roof']['cover']['StEER'] = df_steer['roof_cover_damage_'][idx]
            bldg.hasDamageData['roof']['structure']['StEER'] = df_steer['roof_structure_damage_'][idx]
            bldg.hasDamageData['roof']['substrate']['StEER'] = df_steer['roof_substrate_damage'][idx]
            if int(df_steer['reroof_year'][idx]) > bldg.hasElement['Roof'].hasYearBuilt:
                bldg.hasElement['Roof'].hasYearBuilt = int(df_steer['reroof_year'][idx])
            else:
                pass
            # Add roof damage data description to Roof Element:
            bldg.hasElement['Roof'].hasDamageData = bldg.hasDamageData['Roof']
        except IndexError:  # No StEER entry exists for this exact location: Check General Area or does not exist
            pass
