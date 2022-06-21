import pandas as pd


def get_hazus_occupancy(occupancy, roof_shape, frame_type, num_stories):
    wmuh_occupancies = ['MULTI-FAMI (000300)', 'COOPERATIV (000500)', 'HOTELS AND (003900)']
    if 'SINGLE' in occupancy:
        if roof_shape != 'FLAT':
            # Single family homes in HAZUS can only have hip or gable roofs
            if 'MASONRY' in frame_type:
                return 'MSF'
            else:
                # Assume that this is a wood frame structural system
                return 'WSF'
        else:
            # Multi-family homes can have flat roofs
            if 'MASONRY' in frame_type:
                return 'MMUH'
            else:
                # Assume that this is a wood frame structural system
                return 'WMUH'
    elif any(occ == occupancy for occ in wmuh_occupancies):
        # Multi-family homes and Multi-unit hotel/motels:
        if 'STEEL' in frame_type:  # engineered residential
            return 'SERB'
        elif 'CONCRETE' in frame_type:  # engineered residential
            return 'CERB'
        else:
            if 'MASONRY' in frame_type and num_stories < 4:
                return 'MMUH'
            else:
                # Assume that this is a wood frame structural system
                return 'WMUH'
    else:
        # Choose from remaining commercial occupancies:
        if 'STEEL' in frame_type:  # engineered residential
            if num_stories == 1:
                return 'SPMB'
            else:
                return 'SECB'
        elif 'CONCRETE' in frame_type:  # engineered residential
            return 'CECB'
        elif 'MASONRY' in frame_type and occupancy == 'STORES, 1 (001100)':
            return 'MECBL'
