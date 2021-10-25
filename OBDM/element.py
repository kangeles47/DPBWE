# -------------------------------------------------------------------------------
# Name:             element.py
# Purpose:          Define Element classes and sub-classes for the ontology-based data model
#
# Author:           Karen Irely Angeles (kangeles@nd.edu)
# Affiliation:      Department of Civil and Environmental Engineering and Earth Sciences,
#                   University of Notre Dame, Notre Dame, IN

# Last updated:          (v1) 01/20/2021
# ------------------------------------------------------------------------------


class Element:
    """
    Defines class attributes for objects within the Element class.

    Notes:
        Original Element attributes according to the BOT ontology can be found at:
        https://w3c-lbd-cg.github.io/bot/#Element
    """
    def __init__(self):
        # Elements can have sub-elements:
        self.hasSubElement = None
        # Elements can be modeled as well:
        self.has3DModel = None
        self.hasSimpleModel = None
        # Attributes outside of BOT Ontology:
        self.hasAnalysisModel = None
        self.hasType = None
        self.hasMaterial = []
        self.hasGeometry = {'3D Geometry': {'geodesic': None, 'local': None, 'rotated': None}, '2D Geometry': {'geodesic': None, 'local': None, 'rotated': None}, '1D Geometry': {'geodesic': None, 'local': None, 'rotated': None}, 'Thickness': None, 'Length': None, 'Height': None}
        self.hasModeOfFabrication = {'on-site': False, 'off-site': False}  # options: on-site, off-site, unknown (None object)
        edp_dict = {'peak interstory drift ratio': None, 'peak absolute velocity': None, 'peak absolute acceleration': None,
                    'wind speed': None, 'wind pressure': {'external': None, 'internal': None, 'total': None},
                    'debris impact': None, 'axial force': None, 'shear force': None, 'bending moment': None,
                    'peak flexural stress': None, 'peak shear stress': None, 'peak flexural strain': None, 'curvature': None,
                    'rotation': None, 'elongation': None}
        self.hasCapacity = edp_dict
        self.hasDemand = edp_dict.copy()
        self.hasFailure = {}
        for key in edp_dict:
            self.hasFailure[key] = False
        self.hasFragility = edp_dict
        self.hasOutputVariable = {'repair cost': None, 'downtime': None, 'fatalities': None}
        self.hasServiceLife = None  # placeholder for typical replacement times (i.e., maintenance)
        self.hasManufacturer = None
        self.inLoadPath = False
        self.hasDirection = None  # options here are x or y as defined by building geometry
        self.hasYearBuilt = None
        self.hasDamageData = {'available': False, 'fidelity': None, 'component type': None, 'hazard type': None, 'value': None, 'hazard damage rating': {'wind': None, 'surge': None, 'rain': None}}


class Wall(Element):
    def __init__(self):
        Element.__init__(self)
        # Add in wall instance attributes:
        self.isImpactResistant = False


class Window(Element):
    def __init__(self):
        Element.__init__(self)
        # Add in window instance attributes:
        self.isImpactResistant = False


class Roof(Element):
    def __init__(self):
        Element.__init__(self)
        # Add in roof instance attributes:
        self.hasPitch = None
        self.hasCover = None
        self.hasElevation = None
        self.inLoadPath = True
        self.hasEaveLength = None
        self.hasShape = {'flat': False, 'gable': False, 'hip': False, 'complex': False, 'gable/hip combo': False,
                         'gambrel': False, 'mansard': False, 'monoslope': False, 'user-defined': False}
        self.hasSheathing = None
        self.hasStructureType = None
        self.hasSubElement = {'cover': [], 'sheathing': [], 'roof member': []}


class Floor(Element):  # Consider how we might bring in something like piles
    def __init__(self):
        Element.__init__(self)
        # Add in roof instance attributes:
        self.hasElevation = None
        self.inLoadPath = True


class Ceiling(Element):
    def __init__(self):
        Element.__init__(self)
        # Add in ceiling instance attributes:
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
