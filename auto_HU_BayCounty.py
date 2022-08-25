from WindMetaVarRulesets import parse_BIM
from WindClassRulesets import building_class
from WindWSFRulesets import WSF_config


def auto_populate(BIM):
    """
    Populates the DL model for hurricane assessments in Bay County, FL

    Assumptions:
    - Everything relevant to auto-population is provided in the Buiding
    Information Model (BIM).
    - The information expected in the BIM file is described in the parse_BIM
    method.

    Parameters
    ----------
    BIM_in: dictionary
        Contains the information that is available about the asset and will be
        used to auto-populate the damage and loss model.

    Returns
    -------
    BIM_ap: dictionary
        Contains the extended BIM data.
    DL_ap: dictionary
        Contains the auto-populated loss model.
    """

    # parse the BIM data
    BIM_ap = parse_BIM(BIM)

    # identify the building class
    bldg_class = building_class(BIM_ap)
    BIM_ap.update({'HazusClassW': bldg_class})

    # prepare the building configuration string
    if bldg_class == 'WSF':
        bldg_config = WSF_config(BIM_ap)
    # elif bldg_class == 'WMUH':
    #     bldg_config = WMUH_config(BIM_ap)
    else:
        raise ValueError(
            f"Building class {bldg_class} not recognized by the "
            f"auto-population routine."
        )
    print(bldg_config)
    DL_ap = {
        '_method'      : 'HAZUS MH HU',
        'LossModel'    : {
            'DecisionVariables': {
                "ReconstructionCost": True
            },
            'ReplacementCost'  : 100
        },
        'Components'   : {
            bldg_config: [{
                'location'       : '1',
                'direction'      : '1',
                'median_quantity': '1.0',
                'unit'           : 'ea',
                'distribution'   : 'N/A'
            }]
        }
    }
    # Note: might needs to add some "Combinations field: see auto_HU_LA"
    return BIM_ap, DL_ap