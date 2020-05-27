import numpy as np
# Laying out the code needed to replicate the pressures from ASCE 7

def kz(z, exposure, edition, is_cc):
    # Given Exposure Category, select alpha and zg:
    if exposure == 'A':
        zg = 1500 / 3.281
        if edition == 'ASCE-93' or edition == 'ASCE 7-88':
            alpha = 3.0
        else:
            alpha = 5.0
    elif exposure == 'B':
        zg = 1200/3.281
        if edition == 'ASCE-93' or edition == 'ASCE 7-88':
            alpha = 4.5
        else:
            alpha = 7.0
    elif exposure == 'C':
        zg = 900/3.281
        if edition == 'ASCE-93' or edition == 'ASCE 7-88':
            alpha = 7.0
        else:
            alpha = 9.5
    elif exposure == 'D':
        alpha = 11.5
        zg = 700/3.281
        if edition == 'ASCE-93' or edition == 'ASCE 7-88':
            alpha = 10.0
        else:
            alpha = 11.5
    # Define the factor in front of power law:
    if edition == 'ASCE-93' or edition == 'ASCE 7-88':
        factor = 2.58 # ASCE 7-93: Different values (fastest mile wind speeds)
    else:
        factor = 2.01
    # Velocity pressure coefficient:
    # Exception: ASCE 7-98
    # Case 1a for all components and cladding
    # z shall not be taken as less than 30 feet for Case 1 in Exposure B
    if edition == 'ASCE 7-98' and is_cc:
        if z < 30/3.281:
            z = 30/3.281
        else:
            pass
    # Calculate the velocity pressure coefficient:
    if z < 15/3.281:  # [m]
        kz = factor * ((15/3.281)/zg)**(2/alpha)
    elif 15/3.281 < z < zg:
        kz = factor * (z/zg) ** (2/alpha)

    return kz

def roof_MWFRS(BIM, wind_direction):
    # Identify roof MWFRS zones and pressure coefficients
    aspect_ratios = [h / L; h / B]
    direction = 'windward'
    for ratio in aspect_ratios:
        if BIM.roof.pitch < 10 or BIM.roof.pitch == 'flat' or BIM.roof.pitch == 'shallow' or BIM.roof.pitch == 'flat or shallow' or wind_direction == 'parallel':
            if ratio <= 0.5:
                Cp_full = np.array([[-0.9, -0.18], [-0.9, -0.18], [-0.5, -0.18], [-0.3, -0.18]])
                zones = np.array([0.5*BIM.h_bldg, BIM.h_bldg, 2*BIM.h_bldg, 2.0001*BIM.h_bldg])
                num_zones = np.count_nonzero(zones <= ratio)
                # Get back all Cps for the identified zones:
                Cps = Cp_full[0:num_zones]
            elif ratio >= 1.0:
                Cp_full = np.array([[-1.3, -0.18], [-0.7, -0.18]])
                zones = np.array([0.5 * BIM.h_bldg, 0.50001*BIM.h_bldg])
                num_zones = np.count_nonzero(zones <= ratio)
                # Get back all Cps for the identified zones:
                Cps = Cp_full[0:num_zones]
        else:
            if direction == 'windward':
                angles = np.array([10, 15, 20, 25, 30, 35, 45, 60, 80])
                if ratio <= 0.25:
                    Cp_full = np.array([[-0.7, -0.18], [-0.5, 0.0], [-0.3, 0.2], [-0.2, 0.3], [-0.2, 0.3], [0.0, 0.4], [0.01, 0.01], [0.8, 0.8]])
                    # Choose pressure coefficients given the load direction:
                    Cps = Cp_full
                elif ratio == 0.5:
                    Cp_full = np.array([[-1.3, -0.18], [-0.7, -0.18]])
                    zones = np.array([0.5 * BIM.h_bldg, 0.50001*BIM.h_bldg])
                    num_zones = np.count_nonzero(zones <= ratio)
                    # Get back all Cps for the identified zones:
                    Cps = Cp_full[0:num_zones]
                elif ratio >= 1.0:
                    pass
            elif direction == 'leeward':
                angles = np.array([10, 15, 20])

def roof_CC(BIM):
    # Negative external pressure coefficients:
    # Zone 3
    if area_eff < 0.9: # [m^2]
        gcp = -2.8
    elif 0.9 < area_eff < 9.3:
        m = -1.7/8.4
        gcp = m*(area_eff-0.9)-2.8
    else:
        gcp = -1.1
    # Zone 2
    if area_eff < 0.9: # [m^2]
        gcp = -1.6
    elif 0.9 < area_eff < 9.3:
        m = (-1.1--1.6)/(9.3-0.9) # Slope of Line 3
        gcp = m*(area_eff-0.9)-1.8
    else:
        gcp = -1.1
    # Zone 1
    if area_eff < 0.9: # [m^2]
        gcp = -1.0
    elif 0.9 < area_eff < 9.3:
        m = (-1.1--1.6)/(9.3-0.9) # Slope of Line 3
        gcp = m*(area_eff-0.9)-2.8
    else:
        gcp = -0.9