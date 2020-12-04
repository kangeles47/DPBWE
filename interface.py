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
        self.hasCapacity = {'type': None, 'value': None}
        self.hasDemand = {'type': None, 'value': None}
        self.hasFailure = None
        self.hasFixity = None  # typ. options: fixed, pinned, roller, free
        self.hasGeometry = {'point': None, 'plane': None}  # Suggested Shapely Point and Polgon objects
