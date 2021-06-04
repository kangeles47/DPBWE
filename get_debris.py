# Create decision trees to characterize missile environment and consequent debris trajectories
    # Might want to include here consideration of roof assembly condition (age)
    # Typical debris types: roof covers, roof sheathing, frame/joist elements (e.g., timber)
# Develop rulesets for site-specific debris classification for range of common typologies
# Map debris classes to appropriate trajectory models
# Develop decision trees to extract relevant component data from manufacturer's specifications to refine site-specific debris models
# Implement similitude parameters to project source building damage


def get_trajectory(bldg, debris_class):
    pass


def get_debris_class(bldg):
    # To determine debris class, roof material composition will need to be known:
    compact_types = ['gravel']
    sheet_types = ['metal']
    rod_types = ['frame', 'joist']
    if bldg.hasElement['Roof'][0].hasCover:
        debris_class = None
    return debris_class


def get_mass_unit_area(bldg):
    # Derive mass per unit area values for each debris type from regional manufacturers
    if bldg.hasLocation['State'] == 'FL':
        if bldg.hasLocation['County'] == 'Bay':
            pass