class Assembly:
    def __init__(self):
        self.type = None
        self.is_loadbearing = None
        self.length = None
        self.matls = None
        self.thcks = None
        self.location = None

        # List out the atrributes that every building assembly shares:
        # data = dict.fromkeys(['type', 'is_loadbearing', 'length', 'materials','thicknesses', 'location'])


class WallAssem(Assembly):
    def __init__(self, bldg_model):
        Assembly.__init__(self)
        # Add in wall instance attributes:
        self.is_impact_resistant = None
        self.height = None
        self.is_exterior = None
        self.base_floor = None
        self.top_floor = None


class RoofAssem(Assembly):
    def __init__(self, bldg_model):
        Assembly.__init__(self)
        # Add in roof instance attributes:
        self.pitch = None
        self.cover = None
        self.height = None


class FloorAssem(Assembly):
    def __init__(self, bldg_model):
        Assembly.__init__(self)
        # Add in roof instance attributes:
        self.is_loadbearing = True


class CeilingAssem(Assembly):
    def __init__(self, bldg_model):
        Assembly.__init__(self)
        # Add in roof instance attributes:
        self.is_loadbearing = False


class StructSys(Assembly):
    def __init__(self, bldg_model):
        Assembly.__init__(self)
        # Add in roof instance attributes:
        self.is_loadbearing = True