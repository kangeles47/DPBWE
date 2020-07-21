class Element:
    def __init__(self, storey, parcel_flag):
        # Elements can have subelements:
        self.hasSubElement = None
        # Elements can be adjacent to other elements
        self.adjacentElement = None
        # Elements can be modeled as well:
        self.has3DModel = None
        # Attributes outside of BOT Ontology:
        self.hasType = None
        self.isLoadbearing = None
        self.hasLength = None
        self.hasMatls = None
        self.hasThickness = None
        self.hasCapacity = None

class Wall(Element):
    def __init__(self, bldg_model, storey, parcel_flag):
        Element.__init__(self, storey, parcel_flag)
        # Add in wall instance attributes:
        self.isImpactResistant = None
        self.hasHeight = None
        self.isExterior = None
        self.has1DModel = None
        self.hasCapacity = {}


class Roof(Element):
    def __init__(self, bldg_model, storey, parcel_flag):
        Element.__init__(self, storey, parcel_flag)
        # Add in roof instance attributes:
        self.hasPitch = None
        self.hasCover = None
        self.hasHeight = None
        self.hasElevation = None


class Floor(Element):
    def __init__(self, bldg_model, storey, parcel_flag):
        Element.__init__(self, storey, parcel_flag)
        # Add in roof instance attributes:
        self.isLoadbearing = True
        self.hasElevation = None



class Ceiling(Element):
    def __init__(self, bldg_model, storey, parcel_flag):
        Element.__init__(self, storey, parcel_flag)
        # Add in roof instance attributes:
        self.isLoadbearing = False
        self.hasElevation = None


class StructSys(Element):
    def __init__(self, bldg_model, storey, parcel_flag):
        Element.__init__(self, storey, parcel_flag)
        # Add in roof instance attributes:
        self.isLoadbearing = True