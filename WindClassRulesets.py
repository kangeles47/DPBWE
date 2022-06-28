def building_class(BIM):
    wmuh_occupancies = ['MULTI-FAMI (000300)', 'COOPERATIV (000500)', 'HOTELS AND (003900)']
    if 'SINGLE' in BIM['occupancy_class']:
        if BIM['roof_shape'] != 'FLAT':
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
            if 'MASONRY' in BIM['frame_type'] and BIM['num_stories'] < 4:
                return 'MMUH'
            else:
                # Assume that this is a wood frame structural system
                return 'WMUH'
    else:
        # Choose from remaining commercial occupancies:
        if 'STEEL' in BIM['frame_type']:  # engineered residential
            if BIM['num_stories'] == 1:
                return 'SPMB'
            else:
                return 'SECB'
        elif 'CONCRETE' in BIM['frame_type']:  # engineered residential
            return 'CECB'
        elif 'MASONRY' in BIM['frame_type'] and BIM['occupancy_class'] == 'STORES, 1 (001100)':
            return 'MECBL'
