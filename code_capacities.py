import numpy as np
import matplotlib.pyplot as plt


# Laying out the code needed to replicate the pressures from ASCE 7
def pressure_calc(z, wind_speed, exposure, edition, is_cc):
    # Determine the velocity pressure:
    # Roof MWFRS (q = qh):
    qh, alpha = qz_calc(z, wind_speed, exposure, edition, is_cc)  # For roof, q=qh
    # Determine the enclosure classification for the building:
    encl_class = 'Enclosed'
    # Determine GCpi: in the future, will need to develop a procedure to determine the enclosure category
    if encl_class == 'Open':
        gcpi = 0.0
    if edition == 'ASCE 7-95':
        if encl_class == 'Partial': # includes those in hpr regions, no opening protection:
            gcpi = [0.80, -0.3]
        elif encl_class == 'Enclosed':
            gcpi = 0.18
    elif edition == 'ASCE 7-93' or edition == 'ASCE 7-88':
        if encl_class == 'Partial':
            gcpi = [0.75, -0.25]
        elif encl_class == 'Enclosed':
            gcpi = 0.25
    else:
        if encl_class == 'Partial':
            gcpi = 0.55
        elif encl_class == 'Enclosed':
            gcpi = 0.18
    # Gust effect or gust response factor:
    if edition == 'ASCE 7-95':
        if exposure == 'A' or exposure == 'B':
            g = 0.8
        elif exposure == 'C' or exposure == 'D':
            g = 0.85
    elif edition == 'ASCE 7-93' or edition == 'ASCE 7-88':
        # Gust response factors:
        # Gz is used for C&C, Gh for MWFRS:
        # Select surface drag coefficient:
        if exposure == 'A':
            d0 = 0.025
        elif exposure == 'B':
            d0 = 0.010
        elif exposure == 'C':
            d0 = 0.005
        elif exposure == 'D':
            d0 = 0.003
        if is_cc: # Gz and Gh are calculated the exact same way, except that Gz uses the mean roof height
            tz = (2.35*(d0)**(1/2))/((z/30)**(1/alpha))
            gz = 0.65 + 3.65*tz
        else:
            tz = (2.35 * (d0) ** (1 / 2)) / ((z / 30) ** (1 / alpha))
            gz = 0.65 + 3.65 * tz
    else: # All other editions of ASCE 7
        g = 0.85
    # Determine the Cps or GCps:
    
    # Pressure calc: will need to code in a procedure to determine both +/- cases for GCpi
    # ASCE 7-93:
    if is_cc:
        if z < 60:  # should be building height:
            p = qh * (gcp - gcpi)
        else:
            pass  # same equation, except q = qz
    else:
        p = qh * g * cp - qh * gcpi  # q = qz for roof (at mean roof height)



def qz_calc(z, wind_speed, exposure, edition, is_cc):
    hpr = True
    h_ocean = True
    # Every edition of ASCE 7 has a velocity exposure coefficient:
    kz, alpha = kz_coeff(z, exposure, edition, is_cc)
    # Calculate the velocity pressure:
    if edition == 'ASCE 7-93' or edition == 'ASCE 7-88':
        imp = i_factor(z, wind_speed, hpr, h_ocean)
        qz = 0.613 * kz * (imp * wind_speed) ** 2
    elif edition == 'ASCE 7-95':
        kzt = 1.0
        imp = i_factor(z, wind_speed, hpr, h_ocean)
        qz = 0.613 * kz * kzt * imp * wind_speed ** 2
    elif edition == 'ASCE 7-98' or edition == 'ASCE 7-02' or edition == 'ASCE 7-05':
        kzt = 1.0
        kd = 0.85
        imp = i_factor(z, wind_speed, hpr, h_ocean)
        qz = 0.613 * kz * kzt * kd * imp * wind_speed ** 2
    elif edition == 'ASCE 7-10' or edition == 'ASCE 7-16':
        kzt = 1.0
        kd = 0.85
        qz = 0.613 * kz * kzt * kd * wind_speed ** 2
    return qz, alpha


def kz_coeff(z, exposure, edition, is_cc):
    # Given Exposure Category, select alpha and zg:
    if exposure == 'A':
        zg = 1500 / 3.281
        if edition == 'ASCE 7-93' or edition == 'ASCE 7-88':
            alpha = 3.0
        else:
            alpha = 5.0
    elif exposure == 'B':
        zg = 1200 / 3.281
        if edition == 'ASCE 7-93' or edition == 'ASCE 7-88':
            alpha = 4.5
        else:
            alpha = 7.0
    elif exposure == 'C':
        zg = 900 / 3.281
        if edition == 'ASCE 7-93' or edition == 'ASCE 7-88':
            alpha = 7.0
        else:
            alpha = 9.5
    elif exposure == 'D':
        alpha = 11.5
        zg = 700 / 3.281
        if edition == 'ASCE 7-93' or edition == 'ASCE 7-88':
            alpha = 10.0
        else:
            alpha = 11.5
    # Define the factor in front of power law:
    if edition == 'ASCE 7-93' or edition == 'ASCE 7-88':
        factor = 2.58  # ASCE 7-93: Different values (fastest mile wind speeds)
    else:
        factor = 2.01
    # Velocity pressure coefficient:
    # Exception: ASCE 7-98-ASCE 7-05
    # Case 1a for all components and cladding
    # z shall not be taken as less than 30 feet for Case 1 in Exposure B
    if is_cc:
        if exposure == 'B' and edition == 'ASCE 7-98' or edition == 'ASCE 7-02' or edition == 'ASCE 7-05' or edition == 'ASCE 7-10':
            if z < 30 / 3.281:
                z = 30 / 3.281
            else:
                pass
    # Calculate the velocity pressure coefficient:
    if z < 15 / 3.281:  # [m]
        kz = factor * ((15 / 3.281) / zg) ** (2 / alpha)
    elif 15 / 3.281 <= z < zg:
        kz = factor * (z / zg) ** (2 / alpha)
    return kz, alpha


def i_factor(z, wind_speed, hpr, h_ocean):
    # Importance factor for ASCE 7-05 and older:
    # Assume occupancy category is II for now (later add logic to identify tags for the region (MED, UNIV, etc.):
    cat = 1
    if edition == 'ASCE 7-88' or edition == 'ASCE 7-93':
        if h_ocean:  # if building is at hurricane oceanline (ASCE 7-88 and 7-93)
            categories = np.array([1.05, 1.11, 1.11, 1.00])
            imp = categories[cat - 1]
        else:
            categories = np.array([1.00, 1.07, 1.07, 0.95])
            imp = categories[cat - 1]
    else:
        if hpr and wind_speed > 100 / 2.237:  # wind speed in [m]/[s]
            categories = np.array([0.77, 1.00, 1.15, 1.15])
            imp = categories[cat - 1]
        else:
            categories = np.array([0.87, 1.00, 1.15, 1.15])
            imp = categories[cat - 1]
    return imp


def roof_MWFRS(BIM, wind_direction):
    # Identify roof MWFRS zones and pressure coefficients
    aspect_ratios = None  # [h / L; h / B]
    direction = 'windward'
    for ratio in aspect_ratios:
        if BIM.roof.pitch < 10 or BIM.roof.pitch == 'flat' or BIM.roof.pitch == 'shallow' or BIM.roof.pitch == 'flat or shallow' or wind_direction == 'parallel':
            if ratio <= 0.5:
                Cp_full = np.array([[-0.9, -0.18], [-0.9, -0.18], [-0.5, -0.18], [-0.3, -0.18]])
                zones = np.array([0.5 * BIM.h_bldg, BIM.h_bldg, 2 * BIM.h_bldg, 2.0001 * BIM.h_bldg])
                num_zones = np.count_nonzero(zones <= ratio)
                # Get back all Cps for the identified zones:
                Cps = Cp_full[0:num_zones]
            elif ratio >= 1.0:
                Cp_full = np.array([[-1.3, -0.18], [-0.7, -0.18]])
                zones = np.array([0.5 * BIM.h_bldg, 0.50001 * BIM.h_bldg])
                num_zones = np.count_nonzero(zones <= ratio)
                # Get back all Cps for the identified zones:
                Cps = Cp_full[0:num_zones]
        else:
            if direction == 'windward':
                angles = np.array([10, 15, 20, 25, 30, 35, 45, 60, 80])
                if ratio <= 0.25:
                    Cp_full = np.array(
                        [[-0.7, -0.18], [-0.5, 0.0], [-0.3, 0.2], [-0.2, 0.3], [-0.2, 0.3], [0.0, 0.4], [0.01, 0.01],
                         [0.8, 0.8]])
                    # Choose pressure coefficients given the load direction:
                    Cps = Cp_full
                elif ratio == 0.5:
                    Cp_full = np.array([[-1.3, -0.18], [-0.7, -0.18]])
                    zones = np.array([0.5 * BIM.h_bldg, 0.50001 * BIM.h_bldg])
                    num_zones = np.count_nonzero(zones <= ratio)
                    # Get back all Cps for the identified zones:
                    Cps = Cp_full[0:num_zones]
                elif ratio >= 1.0:
                    pass
            elif direction == 'leeward':
                angles = np.array([10, 15, 20])


def roof_cc(area_eff, pos, zone, edition):
    # Area_eff needs to be in units of ft^2
    area_eff = area_eff * 10.764
    if edition == 'ASCE 7-93' or edition == 'ASCE 7-88' or edition == 'Older':
        # Negative external pressure coefficients: ASCE 7-93, -88, and ANSI-A58.1-1982
        if zone == 1:
            if area_eff < 10:  # [ft^2]
                gcp = -1.4
            elif 10 < area_eff < 20:
                m = (-1.3 - -1.4) / (20 - 10)
                gcp = m * (area_eff - 10) - 1.4
            elif 20 < area_eff < 50:
                m = (-1.275 - -1.3) / (50 - 20)
                gcp = m * (area_eff - 20) - 1.3
            elif 50 < area_eff < 100:
                m = (-1.2 - -1.275) / (100 - 50)
                gcp = m * (area_eff - 50) - 1.275
            elif area_eff > 100:
                gcp = -1.2
        elif zone == 2:
            if area_eff < 10:
                gcp = -2.6
            elif 10 < area_eff < 20:
                m = (-2.25 - -2.6) / (20 - 10)
                gcp = m * (area_eff - 10) - 2.6
            elif 20 < area_eff < 50:
                m = (-1.75 - -2.25) / (50 - 20)
                gcp = m * (area_eff - 20) - 2.25
            elif 50 < area_eff < 100:
                m = (-1.5 - -1.75) / (100 - 50)
                gcp = m * (area_eff - 50) - 1.75
            elif area_eff > 100:
                gcp = -1.5
        elif zone == 3:
            if area_eff < 10:  # [ft^2]
                gcp = -4.0
            elif 10 < area_eff < 20:
                m = (-3.25 - -4.0) / (20 - 10)
                gcp = m * (area_eff - 10) - 4.0
            elif 20 < area_eff < 50:
                m = (-2.25 - -3.25) / (50 - 20)
                gcp = m * (area_eff - 20) - 3.25
            elif 50 < area_eff < 100:
                m = (-1.5 - -2.25) / (100 - 50)
                gcp = m * (area_eff - 50) - 2.25
            elif area_eff > 100:
                gcp = -1.5
    else:
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
                m = (0.2 - 0.225) / (100 - 50)
                gcp = m * (area_eff - 50) + 0.225
            elif area_eff > 100:
                gcp = 0.2
        else:
            # Negative external pressure coefficients:
            if zone == 1:
                if area_eff < 10:  # [ft^2]
                    gcp = -1.0
                elif 10 < area_eff < 20:
                    m = (-0.975 - -1.0) / (20 - 10)
                    gcp = m * (area_eff - 10) - 1.0
                elif 20 < area_eff < 50:
                    m = (-0.95 - -0.975) / (50 - 20)
                    gcp = m * (area_eff - 20) - 0.975
                elif 50 < area_eff < 100:
                    m = (-0.9 - -0.95) / (100 - 50)
                    gcp = m * (area_eff - 50) - 0.95
                elif area_eff > 100:
                    gcp = -0.9
            elif zone == 2:
                if area_eff < 10:
                    gcp = -1.8
                elif 10 < area_eff < 20:
                    m = (-1.6 - -1.8) / (20 - 10)
                    gcp = m * (area_eff - 10) - 1.8
                elif 20 < area_eff < 50:
                    m = (-1.325 - -1.6) / (50 - 20)
                    gcp = m * (area_eff - 20) - 1.6
                elif 50 < area_eff < 100:
                    m = (-1.1 - -1.325) / (100 - 50)
                    gcp = m * (area_eff - 50) - 1.325
                elif area_eff > 100:
                    gcp = -1.1
            elif zone == 3:
                if area_eff < 10:  # [ft^2]
                    gcp = -2.8
                elif 10 < area_eff < 20:
                    m = (-2.3 - -2.8) / (20 - 10)
                    gcp = m * (area_eff - 10) - 2.8
                elif 20 < area_eff < 50:
                    m = (-1.6 - -2.3) / (50 - 20)
                    gcp = m * (area_eff - 20) - 2.3
                elif 50 < area_eff < 100:
                    m = (-1.1 - -1.6) / (100 - 50)
                    gcp = m * (area_eff - 50) - 1.6
                elif area_eff > 100:
                    gcp = -1.1

    return gcp


def wall_cc(area_eff, pos, zone, edition):
    # Area_eff needs to be in units of ft^2
    area_eff = area_eff * 10.764
    if edition == 'ASCE 7-93' or edition == 'ASCE 7-88' or edition == 'Older':
        # Positive external pressure coefficients:
        # Zones 4 and 5
        if pos:
            if area_eff < 10:  # [ft^2]
                gcp = 1.4
            elif 10 < area_eff < 20:
                m = (1.3 - 1.4) / (20 - 10)
                gcp = m * (area_eff - 10) + 1.4
            elif 20 < area_eff < 50:
                m = (1.225 - 1.3) / (50 - 20)
                gcp = m * (area_eff - 20) + 1.3
            elif 50 < area_eff < 100:
                m = (1.15 - 1.225) / (100 - 50)
                gcp = m * (area_eff - 50) + 1.225
            elif 100 < area_eff < 200:
                m = (1.1 - 1.15) / (200 - 100)
                gcp = m * (area_eff - 100) + 1.15
            elif 200 < area_eff < 500:
                m = (1.0 - 1.1) / (500 - 200)
                gcp = m * (area_eff - 200) + 1.1
            elif area_eff > 500:
                gcp = 1.0
        else:
            # Negative external pressure coefficients:
            if zone == 4:
                if area_eff < 10:  # [ft^2]
                    gcp = -1.5
                elif 10 < area_eff < 20:
                    m = (-1.425 - -1.5) / (20 - 10)
                    gcp = m * (area_eff - 10) - 1.5
                elif 20 < area_eff < 50:
                    m = (-1.325 - -1.425) / (50 - 20)
                    gcp = m * (area_eff - 20) - 1.425
                elif 50 < area_eff < 100:
                    m = (-1.25 - -1.325) / (100 - 50)
                    gcp = m * (area_eff - 50) - 1.325
                elif 100 < area_eff < 200:
                    m = (-1.2 - -1.25) / (200 - 100)
                    gcp = m * (area_eff - 100) - 1.25
                elif 200 < area_eff < 500:
                    m = (-1.1 - -1.2) / (500 - 200)
                    gcp = m * (area_eff - 200) - 1.2
                elif area_eff > 500:
                    gcp = -1.1
            elif zone == 5:
                # Zone 5
                if area_eff < 10:  # [ft^2]
                    gcp = -2.0
                elif 10 < area_eff < 20:
                    m = (-1.85 - -2.0) / (20 - 10)
                    gcp = m * (area_eff - 10) - 2.0
                elif 20 < area_eff < 50:
                    m = (-1.625 - -1.85) / (50 - 20)
                    gcp = m * (area_eff - 20) - 1.85
                elif 50 < area_eff < 100:
                    m = (-1.475 - -1.625) / (100 - 50)
                    gcp = m * (area_eff - 50) - 1.625
                elif 100 < area_eff < 200:
                    m = (-1.3 - -1.475) / (200 - 100)
                    gcp = m * (area_eff - 100) - 1.475
                elif 200 < area_eff < 500:
                    m = (-1.1 - -1.3) / (500 - 200)
                    gcp = m * (area_eff - 200) - 1.3
                elif area_eff > 500:
                    gcp = -1.1
    else:
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
                if area_eff < 10:  # [ft^2]
                    gcp = -1.1
                elif 10 < area_eff < 20:
                    m = (-1.05 - -1.1) / (20 - 10)
                    gcp = m * (area_eff - 10) - 1.1
                elif 20 < area_eff < 50:
                    m = (-0.975 - -1.05) / (50 - 20)
                    gcp = m * (area_eff - 20) - 1.05
                elif 50 < area_eff < 100:
                    m = (-0.95 - -0.975) / (100 - 50)
                    gcp = m * (area_eff - 50) - 0.975
                elif 100 < area_eff < 200:
                    m = (-0.85 - -0.95) / (200 - 100)
                    gcp = m * (area_eff - 100) - 0.95
                elif 200 < area_eff < 500:
                    m = (-0.8 - -0.85) / (500 - 200)
                    gcp = m * (area_eff - 200) - 0.85
                elif area_eff > 500:
                    gcp = -0.8
            elif zone == 5:
                # Zone 5
                if area_eff < 10:  # [ft^2]
                    gcp = -1.4
                elif 10 < area_eff < 20:
                    m = (-1.3 - -1.4) / (20 - 10)
                    gcp = m * (area_eff - 10) - 1.4
                elif 20 < area_eff < 50:
                    m = (-1.15 - -1.3) / (50 - 20)
                    gcp = m * (area_eff - 20) - 1.3
                elif 50 < area_eff < 100:
                    m = (-1.05 - -1.15) / (100 - 50)
                    gcp = m * (area_eff - 50) - 1.15
                elif 100 < area_eff < 200:
                    m = (-0.95 - -1.05) / (200 - 100)
                    gcp = m * (area_eff - 100) - 1.05
                elif 200 < area_eff < 500:
                    m = (-0.8 - -0.95) / (500 - 200)
                    gcp = m * (area_eff - 200) - 0.95
                elif area_eff > 500:
                    gcp = -0.8

    return gcp


# Testing out velocity pressure calculation:
z = np.linspace(15 / 3.281, 100/3.281, 200)
wind_speed =  np.linspace(60/ 2.237, 180/2.237, 20) # [m]/[s]
exposure = 'B'
edition = 'ASCE 7-93'
is_cc = False

for speed in wind_speed:
    qzs = np.array([])
    for zs in z:
        qz = qz_calc(zs, speed, exposure, edition, is_cc)
        qzs = np.append(qzs, qz)
    plt.plot(z, qzs)

plt.show()

# Let's plot and see if it works:
# areas = np.arange(0.1, 93, 0.1)
# gcp_lst = np.array([])
# for area in areas:
# gcp = roof_cc(area, pos=False, zone=3)
# gcp_lst = np.append(gcp_lst, gcp)

# plt.plot(areas, gcp_lst)
# plt.show()
