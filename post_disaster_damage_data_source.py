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


