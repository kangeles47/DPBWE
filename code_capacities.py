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
    aspect_ratios = None #[h / L; h / B]
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

def roof_cc(area_eff, pos, zone):
    # Area_eff needs to be in units of ft^2
    area_eff = area_eff*10.764
    # Positive external pressure coefficients:
    # Zones 1, 2, and 3
    if pos:
        if area_eff < 10:  # [ft^2]
            gcp = 0.3
        elif 10 < area_eff < 20:
            m = (0.25 - 0.3) / (20 - 10)
            gcp = m * (area_eff - 10) + 0.3
        elif 20 < area_eff < 50:
            m = (0.225 - 0.25) / (50 - 20)
            gcp = m * (area_eff - 20) + 0.25
        elif 50 < area_eff < 100:
            m = (0.3 - 0.225) / (100 - 50)
            gcp = m * (area_eff - 50) + 0.225
        elif area_eff > 100:
            gcp = 0.3
    else:
        # Negative external pressure coefficients:
        if zone == 1:
            if area_eff < 10: # [ft^2]
                gcp1 = -1.0
            elif 10 < area_eff < 20:
                m = (-0.975--1.0)/(20-10)
                gcp1 = m*(area_eff-10)-1.0
            elif 20 < area_eff < 50:
                m = (-0.95--0.975)/(50-20)
                gcp1 = m*(area_eff-20)-0.975
            elif 50 < area_eff < 100:
                m = (-0.9--0.95)/(100-50)
                gcp1 = m*(area_eff-50)-0.95
            elif area_eff > 100:
                gcp1 = -0.9
        elif zone == 2:
            if area_eff < 10:
                gcp = -1.8
            elif 10 < area_eff < 20:
                m = (-1.6--1.8)/(20-10)
                gcp = m*(area_eff-10)-1.8
            elif 20 < area_eff < 50:
                m = (-1.325--1.6)/(50-20)
                gcp = m*(area_eff-20)-1.6
            elif 50 < area_eff < 100:
                m = (-1.1--1.325)/(100-50)
                gcp = m*(area_eff-50)-1.325
            elif area_eff > 100:
                gcp = -1.1
        elif zone == 3:
            if area_eff < 10: # [ft^2]
                gcp = -2.8
            elif 10 < area_eff < 20:
                m = (-2.3--2.8)/(20-10)
                gcp = m*(area_eff-10)-2.8
            elif 20 < area_eff < 50:
                m = (-1.6--2.3)/(50-20)
                gcp = m*(area_eff-20)-2.3
            elif 50 < area_eff < 100:
                m = (-1.1--1.6)/(100-50)
                gcp = m*(area_eff-50)-1.6
            elif area_eff > 100:
                gcp = -1.1
    return gcp

def wall_cc(area_eff, pos, zone):
    # Area_eff needs to be in units of ft^2
    area_eff = area_eff*10.764
    # Positive external pressure coefficients:
    # Zones 4 and 5
    if pos:
        if area_eff < 10:  # [ft^2]
            gcp = 1.0
        elif 10 < area_eff < 20:
            m = (0.95 - 1.0) / (20 - 10)
            gcp = m * (area_eff - 10) + 1.0
        elif 20 < area_eff < 50:
            m = (0.85 - 0.95) / (50 - 20)
            gcp = m * (area_eff - 20) + 0.95
        elif 50 < area_eff < 100:
            m = (0.825 - 0.85) / (100 - 50)
            gcp = m * (area_eff - 50) + 0.85
        elif 100 < area_eff < 200:
            m = (0.775 - 0.825) / (200 - 100)
            gcp = m * (area_eff - 100) + 0.825
        elif 200 < area_eff < 500:
            m = (0.7 - 0.775) / (500 - 200)
            gcp = m * (area_eff - 200) + 0.775
        elif area_eff > 500:
            gcp = 0.7
    else:
        # Negative external pressure coefficients:
        if zone == 4:
            if area_eff < 10: # [ft^2]
                gcp = -1.1
            elif 10 < area_eff < 20:
                m = (-1.05--1.1)/(20-10)
                gcp = m*(area_eff-10)-1.1
            elif 20 < area_eff < 50:
                m = (-0.975--1.05)/(50-20)
                gcp = m*(area_eff-20)-1.05
            elif 50 < area_eff < 100:
                m = (-0.95--0.975)/(100-50)
                gcp = m*(area_eff-50)-0.975
            elif 100 < area_eff < 200:
                m = (-0.85--0.95)/(200-100)
                gcp = m*(area_eff-100)-0.95
            elif 200 < area_eff < 500:
                m = (-0.8--0.85)/(500-200)
                gcp = m*(area_eff-200)-0.85
            elif area_eff > 500:
                gcp = -0.8
        elif zone == 5:
        # Zone 5
            if area_eff < 10: # [ft^2]
                gcp = -1.0
            elif 10 < area_eff < 20:
                m = (-1.3--1.4)/(20-10)
                gcp = m*(area_eff-10)-1.4
            elif 20 < area_eff < 50:
                m = (-1.15--1.3)/(50-20)
                gcp = m*(area_eff-20)-1.3
            elif 50 < area_eff < 100:
                m = (-1.05--1.15)/(100-50)
                gcp = m*(area_eff-50)-1.15
            elif 100 < area_eff < 200:
                m = (-0.95--1.05)/(200-100)
                gcp = m*(area_eff-100)-1.05
            elif 200 < area_eff < 500:
                m = (-0.8--0.95)/(500-200)
                gcp = m*(area_eff-200)-0.95
            elif area_eff > 500:
                gcp = -0.8

    return gcp

# Let's plot and see if it works:
areas = np.linspace(5, 500, 5)