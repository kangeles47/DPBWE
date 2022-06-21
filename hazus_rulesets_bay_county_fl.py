import pandas as pd


def get_hazus_occupancy(occupancy, roof_shape, frame_type):
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
        if 'MASONRY' in frame_type:
            return 'MMUH'
        elif 'STEEL' in frame_type:  # Engineered residential building
            return 'SERL'
        elif 'CONCRETE' in frame_type:  # Engineered residential building
            return 'CERL'
        else:
            # Assume that this is a wood frame structural system
            return 'WMUH'
