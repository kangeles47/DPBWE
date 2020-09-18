class Element:
    def __init__(self):
        # Elements can have subelements:
        self.hasSubElement = None
        # Elements can be adjacent to other elements
        self.adjacentElement = None
        # Elements can be modeled as well:
        self.has3DModel = None
        self.hasSimpleModel = None
        # Attributes outside of BOT Ontology:
        self.hasType = None
        self.isLoadbearing = None
        self.hasMaterial = None
        self.hasCapacity = {'type': [], 'value': []}
        self.hasLoadingDemand = {'type': [], 'value': []}
        self.hasFailure = False  # Default value
        self.hasGeometry = {'3D Geometry': None, '2D Geometry': None, '1D Geometry': None, 'Thickness': None}
        self.hasFragility = None
        self.hasModeOfFabrication = None  # options: on-site, off-site, unknown (None object)
        edp_dict = {'peak interstory drift ratio': None, 'peak absolute velocity': None, 'peak absolute acceleration': None, 'wind speed': None, 'pressure': None, 'impact': None, 'axial force': None, 'shear force': None, 'bending moment': None, 'peak flexural stress': None, 'peak shear stress': None, 'peak flexural strain': None, 'curvature': None, 'rotation': None, 'elongation': None}
        self.hasEDP = {'x direction': edp_dict, 'y direction': edp_dict}  # Specifying direction for of out-of-plane
        self.hasOutputVariable = {'repair cost': None, 'downtime': None, 'fatalities': None}
        self.hasServiceLife = None  # placeholder for typical replacement times (i.e., maintenance)
        self.hasManufacturer = None
        self.inLoadPath = None
        self.hasDirection = None  # options here are x or y as defined by building geometry


class Wall(Element):
    def __init__(self):
        Element.__init__(self)
        # Add in wall instance attributes:
        self.isImpactResistant = None
        self.hasHeight = None


class Window(Element):
    def __init__(self):
        Element.__init__(self)
        # Add in wall instance attributes:
        self.isImpactResistant = None
        self.hasHeight = None


class Roof(Element):
    def __init__(self):
        Element.__init__(self)
        # Add in roof instance attributes:
        self.hasPitch = None
        self.hasCover = None
        self.hasHeight = None
        self.hasElevation = None
        self.inLoadPath = True
        self.hasEaveLength = None
        self.hasShape = None


class Floor(Element):  # Consider how we might bring in something like piles
    def __init__(self):
        Element.__init__(self)
        # Add in roof instance attributes:
        self.hasElevation = None
        self.inLoadPath = True



class Ceiling(Element):
    def __init__(self):
        Element.__init__(self)
        # Add in roof instance attributes:
        self.inLoadPath = False
        self.hasElevation = None


class Column(Element):
    def __init__(self):
        Element.__init__(self)
        # Add in column instance attributes:
        self.inLoadPath = True
        self.hasHeight = None

class Beam(Element):
    def __init__(self):
        Element.__init__(self)
        # Add in beam instance attributes:
        self.inLoadPath = True
        self.hasLength = None
