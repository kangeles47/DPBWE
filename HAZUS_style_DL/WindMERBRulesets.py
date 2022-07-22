def merb_config(BIM):
    """
    Rules to identify a HAZUS MERB configuration based on BIM data
    Parameters
    ----------
    BIM: dictionary
        Information about the building characteristics.
    Returns
    -------
    config: str
        A string that identifies a specific configration within this buidling
        class.
    """

    year = BIM['year_built'] # just for the sake of brevity

    # Roof cover
    if BIM['roof_shape'] in ['gab', 'hip']:
        roof_cover = 'bur'
        # no info, using the default supoorted by HAZUS
    else:
        if year >= 1975:
            roof_cover = 'spm'
        else:
            # year < 1975
            roof_cover = 'bur'

    # shutters
    if year >= 2000:
        shutters = BIM['WBD']
    else:
        if BIM['WBD']:
            shutters = random.random() < 0.45
        else:
            shutters = False

    # Wind Debris (widd in HAZSU)
    # HAZUS A: Res/Comm, B: Varies by direction, C: Residential, D: None
    WIDD = 'C' # residential (default)
    if BIM['occupancy_class'] in ['RES1', 'RES2', 'RES3A', 'RES3B', 'RES3C',
                                 'RES3D']:
        WIDD = 'C' # residential
    elif BIM['occupancy_class'] == 'AGR1':
        WIDD = 'D' # None
    else:
        WIDD = 'A' # Res/Comm

    # Metal RDA
    # 1507.2.8.1 High Wind Attachment.
    # Underlayment applied in areas subject to high winds (Vasd greater
    # than 110 mph as determined in accordance with Section 1609.3.1) shall
    #  be applied with corrosion-resistant fasteners in accordance with
    # the manufacturer’s instructions. Fasteners are to be applied along
    # the overlap not more than 36 inches on center.
    if BIM['V_ult'] > 142:
        MRDA = 'std'  # standard
    else:
        MRDA = 'sup'  # superior

    # Window area ratio
    if BIM['window_area'] < 0.33:
        WWR = 'low'
    elif BIM['window_area'] < 0.5:
        WWR = 'med'
    else:
        WWR = 'hig'

    if BIM['stories'] <= 2:
        bldg_tag = 'MERBL'
    elif BIM['stories'] <= 5:
        bldg_tag = 'MERBM'
    else:
        bldg_tag = 'MERBH'

    bldg_config = f"{bldg_tag}_" \
                  f"{roof_cover}_" \
                  f"{WWR}_" \
                  f"{int(shutters)}_" \
                  f"{WIDD}_" \
                  f"{MRDA}_" \
                  f"{int(BIM['terrain'])}"
    return bldg_config
