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

    # Preliminary query to see if this building is in Florida and Bay County
    # Print warnings if otherwise:
    if BIM_ap['state'].upper() == 'FL' or BIM_ap['state'].upper() == 'FLORIDA':
        pass
    else:
        print("WARNING: Custom fragilities are developed using sample buildings from Florida's Bay County")
    if 'BAY' in BIM_ap['county'].upper():
        pass
    else:
        print("WARNING: Custom fragilities are developed using sample buildings from Florida's Bay County")

    # Execute simple year_built query to figure out if Pre_FBC or FBC construction:
    if BIM_ap['year_built'] < 2002:
        component_config = 'Pre_FBC'
    else:
        component_config = 'FBC'

    # Identify the tag for the roof cover type:
    if BIM_ap['roof_cover'].upper() == 'ENG SHINGL' or 'ASPHALT' in BIM_ap['roof_cover'].upper():
        rcover_tag = 'asphalt'
    else:
        print('Custom fragilities are for asphalt shingle roof covers only. Modify IF statement if identifier is '
              'different than those provided.')

    # Verify occupancy type:
    if 'SINGLE' in BIM_ap['occupancy_class']:
        occ_tag = 'sfh'
    else:
        print('Custom fragilities are for single family occupancies only. Modify IF statement is identifier is '
              'different that those provided.')

    # Building height: Note we used actual heights estimated using DOE's residential reference buildings. Stories
    # estimate useful when no building height data is available.
    if BIM_ap['height_unit'] == 'ft':
        height_m = BIM_ap['height_unit'] * 3.281
    elif BIM_ap['height_unit'] == 'm':
        height_m = BIM_ap['height_unit']
    if 3.35 <= height_m <= 10:
        height_tag = '1'
    else:
        print('Custom fragilities are for single family homes between 3.35-10 m tall stories.')

    # Load path -related queries (based on Wind loading provisions in ASCE 7):
    # Roof shape:
    if 'gab' in BIM_ap['roof_shape'].lower() or 'hip' in BIM_ap['roof_shape'].lower():
        rshape_flag = True
    else:
        print('Custom fragilities are for gable or hip roof shapes only.')
    # Roof pitch:
    if 7 < BIM_ap['roof_pitch'] <= 27:
        rpitch_flag = True
    else:
        print('Custom fragilities are for roof pitches between 7-27.')
    # Pressure zone:
    if rshape_flag and rpitch_flag:
        zone_tag = '2'
    else:
        print('Building roof pressure zone use case is incompatible.')

    # Compile component fragility identifier:
    comp_fragililty_func = component_config + '_' + rcover_tag + '_' + occ_tag + '_' + height_tag + '_' + zone_tag

    # bldg_class = building_class(BIM_ap)
    # BIM_ap.update({'HazusClassW': bldg_class})

    # prepare the building configuration string
    # if bldg_class == 'WSF':
    #     bldg_config = WSF_config(BIM_ap)
    # # elif bldg_class == 'WMUH':
    # #     bldg_config = WMUH_config(BIM_ap)
    # else:
    #     raise ValueError(
    #         f"Building class {bldg_class} not recognized by the "
    #         f"auto-population routine."
    #     )
    # print(bldg_config)
    print(component_config)
    DL_ap = {
        '_method'      : 'HAZUS MH HU',
        'LossModel'    : {
            'DecisionVariables': {
                "ReconstructionCost": True
            },
            'ReplacementCost'  : 100
        },
        'Components'   : {
            component_config: [{
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