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