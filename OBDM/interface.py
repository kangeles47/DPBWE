# -------------------------------------------------------------------------------
# Name:             interface.py
# Purpose:          Define Interface class for the ontology-based data model
#
# Author:           Karen Irely Angeles (kangeles@nd.edu)
# Affiliation:      Department of Civil and Environmental Engineering and Earth Sciences,
#                   University of Notre Dame, Notre Dame, IN

# Last updated:          (v1) 01/20/2021
# ------------------------------------------------------------------------------


class Interface:
    def __init__(self, object_list):
        # An interface is the surface where zones, elements, or zones and elements
        if isinstance(object_list, list):
            self.isInterfaceOf = object_list
        else:
            print('Please insert a list of Zone and/or Element Objects')
        # Attributes outside of the BOT Ontology:
        # Interfaces like connections can have a 3D Model and capacity:
        self.hasAnalysisModel = None
        edp_dict = {'peak interstory drift ratio': None, 'peak absolute velocity': None,
                    'peak absolute acceleration': None, 'wind speed': None,
                    'wind pressure': {'external': None, 'internal': None, 'total': None}, 'debris impact': None,
                    'axial force': None, 'shear force': None, 'bending moment': None, 'peak flexural stress': None,
                    'peak shear stress': None, 'peak flexural strain': None, 'curvature': None, 'rotation': None,
                    'elongation': None}
        self.hasCapacity = edp_dict
        self.hasDemand = edp_dict
        self.hasFailure = {}
        for key in edp_dict:
            self.hasFailure[key] = False
        self.hasFragility = edp_dict
        self.hasFixity = {'local': {'x': False, 'y': False, 'z': False, 'user-defined': None}}
        self.hasGeometry = {'point': None, 'plane': None}  # Suggested Shapely Point and Polgon objects
        self.hasManufacturer = None
        self.hasMaterial = []
        self.hasOutputVariable = {'repair cost': None, 'downtime': None, 'fatalities': None}
        self.hasType = None
        self.hasYearBuilt = None
        self.inLoadPath = False
