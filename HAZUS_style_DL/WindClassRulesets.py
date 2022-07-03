def building_class(BIM):
    wmuh_occupancies = ['MULTI-FAMI (000300)', 'COOPERATIV (000500)', 'HOTELS AND (003900)']
    comm_eng_occupancies = ['OFFICE BLD (001700)', 'STORES, 1 (001100)', 'DRIVE-IN R (002200)']
    if 'SINGLE' in BIM['occupancy_class']:
        if BIM['roof_shape'] != 'flt':
            # Single family homes in HAZUS can only have hip or gable roofs
            if 'MASONRY' in BIM['frame_type']:
                return 'MSF'
            else:
                # Assume that this is a wood frame structural system
                return 'WSF'
        else:
            # Multi-family homes can have flat roofs
            if 'MASONRY' in BIM['frame_type']:
                return 'MMUH'
            else:
                # Assume that this is a wood frame structural system
                return 'WMUH'
    elif any(occ == BIM['occupancy_class'] for occ in wmuh_occupancies):
        # Multi-family homes and Multi-unit hotel/motels:
        if 'STEEL' in BIM['frame_type']:  # engineered residential
            return 'SERB'
        elif 'CONCRETE' in BIM['frame_type']:  # engineered residential
            return 'CERB'
        else:
            if 'MASONRY' in BIM['frame_type'] and BIM['stories'] < 4:
                return 'MMUH'
            else:
                # Assume that this is a wood frame structural system
                return 'WMUH'
    else:
        # Choose from remaining commercial occupancies:
        if 'STEEL' in BIM['frame_type']:  # engineered residential
            if BIM['stories'] == 1:
                return 'SPMB'
            else:
                return 'SECB'
        elif 'CONCRETE' in BIM['frame_type']:  # engineered residential
            return 'CECB'
        elif 'MASONRY' in BIM['frame_type'] and any(occ == BIM['occupancy_class'] for occ in comm_eng_occupancies):
            return 'MECBL'
        elif 'WOOD' in BIM['frame_type'] or 'NOT AVAILABLE' in BIM['frame_type']:
            return 'WMUH'  # model as a hotel/motel/multi-fam unit
