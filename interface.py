class Interface:
    def __init__(self, first_instance, second_instance):
        # An interface is the surface where two building elements: 2 zones or 1 element + 1 zone meet
        self.isInterfaceOf = [first_instance, second_instance]
        # Attributes outside of the BOT Ontology:
        # Interfaces like connections can have a 3D Model and capacity:
        self.hasAnalysisModel = None
        self.hasFixity = None  # typ. options: fixed, pinned, roller, free
        self.hasCapacity = {'type': None, 'value': None}
        self.hasLoadingDemand = {'type': None, 'value': None}
        self.hasFailure = None
        self.hasType = None  # options here are point or plane
