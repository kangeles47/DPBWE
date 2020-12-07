class Element:
    def __init__(self):
        # Elements can have subelements:
        self.hasSubElement = None
        # Elements can be modeled as well:
        self.has3DModel = None
        self.hasSimpleModel = None
        # Attributes outside of BOT Ontology:
        self.hasType = None
        self.hasMaterial = []
        self.hasGeometry = {'3D Geometry': {'geodesic': None, 'local': None, 'rotated': None}, '2D Geometry': {'geodesic': None, 'local': None, 'rotated': None}, '1D Geometry': {'geodesic': None, 'local': None, 'rotated': None}, 'Thickness': None, 'Length': None, 'Height': None}
        self.hasModeOfFabrication = {'on-site': False, 'off-site': False}  # options: on-site, off-site, unknown (None object)
        edp_dict = {'peak interstory drift ratio': None, 'peak absolute velocity': None, 'peak absolute acceleration': None, 'wind speed': None, 'wind pressure': {'external': None, 'internal': None, 'total': None}, 'debris impact': None, 'axial force': None, 'shear force': None, 'bending moment': None, 'peak flexural stress': None, 'peak shear stress': None, 'peak flexural strain': None, 'curvature': None, 'rotation': None, 'elongation': None}
        self.hasEDP = {'x direction': edp_dict, 'y direction': edp_dict, 'user-defined': edp_dict}  # Specifying direction for of out-of-plane
        self.hasCapacity = edp_dict
        self.hasDemand = edp_dict
        self.hasFailure = {}
        for key in edp_dict:
            self.hasFailure[key] = False
        self.hasFragility = edp_dict
        self.hasOutputVariable = {'repair cost': None, 'downtime': None, 'fatalities': None}
        self.hasServiceLife = None  # placeholder for typical replacement times (i.e., maintenance)
        self.hasManufacturer = None
        self.inLoadPath = None
        self.hasDirection = None  # options here are x or y as defined by building geometry
        self.hasYearBuilt = None


class Wall(Element):
    def __init__(self):
        Element.__init__(self)
        # Add in wall instance attributes:
        self.isImpactResistant = None


class Window(Element):
    def __init__(self):
        Element.__init__(self)
        # Add in wall instance attributes:
        self.isImpactResistant = None


class Roof(Element):
    def __init__(self):
        Element.__init__(self)
        # Add in roof instance attributes:
        self.hasPitch = None
        self.hasCover = None
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

class Beam(Element):
    def __init__(self):
        Element.__init__(self)
        # Add in beam instance attributes:
        self.inLoadPath = True
