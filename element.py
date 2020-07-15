class Element:
    def __init__(self, storey, parcel_flag):
        # Elements can have subelements:
        self.hasSubElement = None
        # Elements can be adjacent to other elements
        self.adjacentZone = None
        # Elements can be modeled as well:
        self.has3DModel = None
        # Attributes outside of BOT Ontology:
        self.hasType = None
        self.isLoadbearing = None
        self.hasLength = None
        self.hasMatls = None
        self.hasThickness = None
        self.has2DLocation = None  # Update with building-specific coordinates
        self.hasCapacity = None

class Wall(Element):
    def __init__(self, bldg_model, storey, parcel_flag):
        Element.__init__(self, storey, parcel_flag)
        # Add in wall instance attributes:
        self.isImpactResistant = None
        self.hasHeight = None
        self.isExterior = None
        # Note: need to make sure this being linked back to specific story/stories


class Roof(Element):
    def __init__(self, bldg_model, storey, parcel_flag):
        Element.__init__(self, storey, parcel_flag)
        # Add in roof instance attributes:
        self.hasPitch = None
        self.hasCover = None
        self.hasHeight = None


class Floor(Element):
    def __init__(self, bldg_model, storey, parcel_flag):
        Element.__init__(self, storey, parcel_flag)
        # Add in roof instance attributes:
        self.isLoadbearing = True



class Ceiling(Element):
    def __init__(self, bldg_model, storey, parcel_flag):
        Element.__init__(self, storey, parcel_flag)
        # Add in roof instance attributes:
        self.isLoadbearing = False


class StructSys(Element):
    def __init__(self, bldg_model, storey, parcel_flag):
        Element.__init__(self, storey, parcel_flag)
        # Add in roof instance attributes:
        self.isLoadbearing = True