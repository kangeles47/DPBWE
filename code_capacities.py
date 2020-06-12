import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import cmath
from scipy.optimize import curve_fit

class PressureCalc:

    def wcc_capacity(self, wind_speed, exposure, edition, h_bldg, area_eff):
        # Determine GCpis for pressure calculation:
        gcpi = PressureCalc.get_gcpi(self, edition, encl_class='Enclosed')
        # Determine components and cladding pressure for building facade components:
        is_cc = True
        # All components and cladding calculations require qh:
        qh, alpha = PressureCalc.qz_calc(self, h_bldg, wind_speed, exposure, edition, is_cc)
        # Get GCps and calculate the pressure for each zone:
        wpos = [True, True, False, False]
        wzone = [4, 5, 4, 5]
        wps = list()
        for ind in range(0, len(wpos)):
            # Find the GCp
            gcp = PressureCalc.wall_cc(self, area_eff, wpos[ind], wzone[ind], edition)
            # Reduce GCp for walls if roof pitch is <= 10 degrees:
            theta = 12
            if theta <= 10:
                gcp = 0.9 * gcp
            else:
                pass
            # Calculate pressure at the zone:
            p = PressureCalc.calc_pressure(self, z, exposure, edition, is_cc, qh, gcp, gcpi)
            wps.append(p)

        return wps

    def rcc_capacity(self, wind_speed, exposure, edition, h_bldg, area_eff):
        # Determine GCpis for pressure calculation:
        gcpi = PressureCalc.get_gcpi(self, edition, encl_class='Enclosed')
        # Determine components and cladding pressure for building roof components:
        is_cc = True
        # All components and cladding calculations require qh:
        qh, alpha = PressureCalc.qz_calc(self, h_bldg, wind_speed, exposure, edition, is_cc)
        # Get GCps and calculate the pressure for each zone:
        rpos = [True, True, True, False, False, False]
        rzone = [1, 2, 3, 1, 2, 3]
        rps = list()
        for ind in range(0, len(rpos)):
            # Find the GCp
            gcp = PressureCalc.roof_cc(self, area_eff, rpos[ind], rzone[ind], edition)
            # Calculate pressure at the zone:
            p = PressureCalc.calc_pressure(self, z, exposure, edition, is_cc, qh, gcp, gcpi)
            rps.append(p)
        return rps

    def rmwfrs_capacity(self, wind_speed, exposure, edition, h_bldg, length):
        # Determine GCpis for pressure calculation:
        gcpi = PressureCalc.get_gcpi(self, edition, encl_class='Enclosed')
        # Determine the velocity pressure:
        is_cc = False
        # Roof uplift pressures require qh:
        qh, alpha = PressureCalc.qz_calc(self, h_bldg, wind_speed, exposure, edition, is_cc)
        # Get the gust effect or gust response factor:
        g = PressureCalc.get_g(self, edition, exposure, is_cc, alpha)
        # Set up to find Cp values:
        direction = 'parallel'
        pitch = 9
        ratio = 0.5
        # Set up placeholders for Cp values:
        rmps = list()
        # Find the Cps:
        cp = PressureCalc.roof_mwfrs(self, h_bldg, direction, ratio, pitch, length)
        for row in cp:
            gcp = g * row[0]  # Take the first Cp value for uplift calculations
            # Calculate uplift pressure at the zone:
            p = PressureCalc.calc_pressure(self, z, exposure, edition, is_cc, qh, gcp, gcpi)
            rmps.append(p)

        return rmps

    def run(self, z, wind_speed, exposure, edition, r_mwfrs, h_bldg, w_cc, r_cc, area_eff=None):
        # Determine GCpis for pressure calculation:
        gcpi = PressureCalc.get_gcpi(self, edition, encl_class='Enclosed')
        # Determine the MWFRS pressures for roof:
        if r_mwfrs:
            wps = 0
            rps = 0
            is_cc = False
            # Roof uplift pressures require qh:
            qh, alpha = PressureCalc.qz_calc(self, h_bldg, wind_speed, exposure, edition, is_cc)
            # Get the gust effect or gust response factor:
            g = PressureCalc.get_g(self, edition, exposure, is_cc, alpha)
            # Set up to find Cp values:
            direction = 'parallel'
            pitch = 9
            ratio = 0.5
            # Set up placeholders for Cp values:
            rmps = list()
            # Find the Cps:
            length = 2*h_bldg
            cp = PressureCalc.roof_mwfrs(self, h_bldg, direction, ratio, pitch, length)
            for row in cp:
                gcp = g*cp[0][0] # Take the first Cp value for uplift calculations
                # Calculate uplift pressure at the zone:
                p = PressureCalc.calc_pressure(self, z, exposure, edition, is_cc, qh, gcp, gcpi)
                rmps.append(p)
        # Determine pressure for components and cladding:
        if w_cc or r_cc:
            # C&C loads:
            is_cc = True
            # All components and cladding calculations require qh:
            qh, alpha = PressureCalc.qz_calc(self, h_bldg, wind_speed, exposure, edition, is_cc)
            # Get GCps and calculate the pressure for each zone:
            if w_cc:
                wpos = [True, True, False, False]
                wzone = [4, 5, 4, 5]
                wps = list()
                for ind in range(0, len(wpos)):
                    # Find the GCp
                    gcp = PressureCalc.wall_cc(self, area_eff, wpos[ind], wzone[ind], edition)
                    # Reduce GCp for walls if roof pitch is <= 10 degrees:
                    theta = 12
                    if theta <= 10:
                        gcp = 0.9*gcp
                    else:
                        pass
                    # Calculate pressure at the zone:
                    p = PressureCalc.calc_pressure(self, z, exposure, edition, is_cc, qh, gcp, gcpi)
                    wps.append(p)
            elif r_cc:
                # Roof C&C:
                rpos = [True, True, True, False, False, False]
                rzone = [1, 2, 3, 1, 2, 3]
                rps = list()
                for ind in range(0, len(rpos)):
                    # Find the GCp
                    gcp = PressureCalc.roof_cc(self, area_eff, rpos[ind], rzone[ind], edition)
                    # Calculate pressure at the zone:
                    p = PressureCalc.calc_pressure(self, z, exposure, edition, is_cc, qh, gcp, gcpi)
                    rps.append(p)
                wps = 0
                rmps = 0
        return wps, rps, rmps

    def get_gcpi(self, edition, encl_class='Enclosed'):
        # Determine GCpi: in the future, will need to develop a procedure to determine the enclosure category
        if encl_class == 'Open':
            gcpi = 0.0
        if edition == 'ASCE 7-95':
            if encl_class == 'Partial':  # includes those in hpr regions, no opening protection:
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

        return gcpi

    def get_g(self, edition, exposure, is_cc, alpha):
        alpha = 7.0  # Provide default value for Exposure B
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
            if is_cc:  # Gz and Gh are calculated the exact same way, except that Gz uses the mean roof height
                tz = (2.35 * (d0) ** (1 / 2)) / ((z / (30 / 3.281)) ** (1 / alpha))
                g = 0.65 + 3.65 * tz
            else:
                tz = (2.35 * (d0) ** (1 / 2)) / ((z / (30 / 3.281)) ** (1 / alpha))
                g = 0.65 + 3.65 * tz
        else:  # All other editions of ASCE 7
            g = 0.85
        return g

    # Laying out the code needed to replicate the pressures from ASCE 7
    def calc_pressure(self, z, exposure, edition, is_cc, q, gcp, gcpi):
        # Pressure calc: will need to code in a procedure to determine both +/- cases for GCpi
        # ASCE 7-93:
        if is_cc:
            if z <= 60 / 3.281:  # should be building height:
                # Calculate pressure for the controlling case:
                if gcp > 0:
                    p = q * (gcp + gcpi)
                elif gcp < 0:
                    p = q * (gcp - gcpi)
            else:
                pass  # same equation, except q = qz
            # Exception for ASCE 7-95: For buildings in Exposure B, calculated pressure shall be multiplied by 0.85
            if edition == 'ASCE 7-95':
                p = 0.85 * p
            else:
                pass
            # Minimum design pressure for C&C:
            if abs(p) / 1000 < 0.48:  # [kN/m^2]
                p = np.sign(p) * 0.48 * 1000  # [N/m^2]
            else:
                pass
        else:
            p = q * gcp - q * gcpi  # q = qz for roof (at mean roof height)
        return p

    def qz_calc(self, z, wind_speed, exposure, edition, is_cc):
        hpr = True
        h_ocean = True
        # Every edition of ASCE 7 has a velocity exposure coefficient:
        kz, alpha = PressureCalc.get_kz(self, z, exposure, edition, is_cc)
        # Calculate the velocity pressure:
        if edition == 'ASCE 7-93' or edition == 'ASCE 7-88':
            imp = PressureCalc.get_i(self, z, wind_speed, hpr, h_ocean)
            qz = 0.613 * kz * (imp * wind_speed) ** 2
        elif edition == 'ASCE 7-95':
            kzt = 1.0
            imp = PressureCalc.get_i(self, z, wind_speed, hpr, h_ocean)
            qz = 0.613 * kz * kzt * imp * wind_speed ** 2
        elif edition == 'ASCE 7-98' or edition == 'ASCE 7-02' or edition == 'ASCE 7-05':
            kzt = 1.0
            kd = 0.85
            imp = PressureCalc.get_i(self, z, wind_speed, hpr, h_ocean)
            qz = 0.613 * kz * kzt * kd * imp * wind_speed ** 2
        elif edition == 'ASCE 7-10' or edition == 'ASCE 7-16':
            kzt = 1.0
            kd = 0.85
            qz = 0.613 * kz * kzt * kd * wind_speed ** 2
        print('qz:', qz * 0.020885, 'z:', z, 'wind_speed:', wind_speed*2.237)
        return qz, alpha

    def get_kz(self, z, exposure, edition, is_cc):
        # ASCE 7-95 and older: Exposure Category is C for C&C (B allowed for 7-95)
        if is_cc:
            if edition == 'ASCE 7-95':
                if exposure == 'A' or exposure == 'D':
                    exposure = 'C'
                else:
                    pass
            elif edition == 'ASCE 7-93' or edition == 'ASCE 7-88':
                exposure = 'C'
        else:
            pass
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
            if exposure == 'B' and (
                    edition == 'ASCE 7-98' or edition == 'ASCE 7-02' or edition == 'ASCE 7-05' or edition == 'ASCE 7-10'):
                if z < 30 / 3.281:
                    z = 30 / 3.281
                else:
                    pass
        # Calculate the velocity pressure coefficient:
        if z <= 15 / 3.281:  # [m]
            kz = factor * ((15 / 3.281) / zg) ** (2 / alpha)
        elif 15 / 3.281 < z < zg:
            kz = factor * (z / zg) ** (2 / alpha)
        return kz, alpha

    def get_i(self, z, wind_speed, hpr, h_ocean):
        # Importance factor for ASCE 7-05 and older:
        # Assume occupancy category is II for now (later add logic to identify tags for the region (MED, UNIV, etc.):
        cat = 2
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

    def roof_mwfrs(self, h_bldg, direction, ratio, pitch, length):
        # Identify roof MWFRS zones and pressure coefficients
        if (pitch < 10 or pitch == 'flat' or pitch == 'shallow' or pitch == 'flat or shallow') or direction == 'parallel':
            if ratio <= 0.5:
                Cp_full = np.array([[-0.9, -0.18], [-0.9, -0.18], [-0.5, -0.18], [-0.3, -0.18]])
                if length <= 0.5*h_bldg:
                    zones = 1
                elif 0.5*h_bldg < length <= h_bldg:
                    zones = 2
                elif h_bldg < length <= 2*h_bldg:
                    zones = 3
                elif length > 2*h_bldg:
                    zones = 4
                # Get back all Cps for the identified zones:
                Cps = Cp_full[0:zones]
            elif ratio >= 1.0:
                Cp_full = np.array([[-1.3, -0.18], [-0.7, -0.18]])
                zones = np.array([0.5 * h_bldg, 0.50001 * h_bldg])
                if length <= 0.5 * h_bldg:
                    zones = 1
                elif length > 0.5 * h_bldg:
                    zones = 2
                # Get back all Cps for the identified zones:
                Cps = Cp_full[0:zones]
        else:
            if direction == 'windward':
                angles = np.array([10, 15, 20, 25, 30, 35, 45, 60, 80])
                if ratio <= 0.25:
                    Cp_full = np.array([[-0.7, -0.18], [-0.5, 0.0], [-0.3, 0.2], [-0.2, 0.3], [-0.2, 0.3], [0.0, 0.4],[0.01, 0.01],[0.8, 0.8]])
                    # Choose pressure coefficients given the load direction:
                    Cps = Cp_full
                elif ratio == 0.5:
                    Cp_full = np.array([[-1.3, -0.18], [-0.7, -0.18]])
                    zones = np.array([0.5 * h_bldg, 0.50001 * h_bldg])
                    num_zones = np.count_nonzero(zones <= ratio)
                    # Get back all Cps for the identified zones:
                    Cps = Cp_full[0:num_zones]
                elif ratio >= 1.0:
                    pass
            elif direction == 'leeward':
                angles = np.array([10, 15, 20])
        return Cps

    def roof_cc(self, area_eff, pos, zone, edition):
        # Area_eff needs to be in units of ft^2
        area_eff = area_eff * 10.764
        if edition == 'ASCE 7-93' or edition == 'ASCE 7-88':
            # Negative external pressure coefficients: ASCE 7-93, -88, and ANSI-A58.1-1982
            if zone == 1:
                if area_eff <= 10:  # [ft^2]
                    gcp = -1.4
                elif 10 < area_eff <= 20:
                    m = (-1.3 - -1.4) / (20 - 10)
                    gcp = m * (area_eff - 10) - 1.4
                elif 20 < area_eff <= 50:
                    m = (-1.275 - -1.3) / (50 - 20)
                    gcp = m * (area_eff - 20) - 1.3
                elif 50 < area_eff <= 100:
                    m = (-1.2 - -1.275) / (100 - 50)
                    gcp = m * (area_eff - 50) - 1.275
                elif area_eff > 100:
                    gcp = -1.2
            elif zone == 2:
                if area_eff <= 10:
                    gcp = -2.6
                elif 10 < area_eff <= 20:
                    m = (-2.25 - -2.6) / (20 - 10)
                    gcp = m * (area_eff - 10) - 2.6
                elif 20 < area_eff <= 50:
                    m = (-1.75 - -2.25) / (50 - 20)
                    gcp = m * (area_eff - 20) - 2.25
                elif 50 < area_eff <= 100:
                    m = (-1.5 - -1.75) / (100 - 50)
                    gcp = m * (area_eff - 50) - 1.75
                elif area_eff > 100:
                    gcp = -1.5
            elif zone == 3:
                if area_eff <= 10:  # [ft^2]
                    gcp = -4.0
                elif 10 < area_eff <= 20:
                    m = (-3.25 - -4.0) / (20 - 10)
                    gcp = m * (area_eff - 10) - 4.0
                elif 20 < area_eff <= 50:
                    m = (-2.25 - -3.25) / (50 - 20)
                    gcp = m * (area_eff - 20) - 3.25
                elif 50 < area_eff <= 100:
                    m = (-1.5 - -2.25) / (100 - 50)
                    gcp = m * (area_eff - 50) - 2.25
                elif area_eff > 100:
                    gcp = -1.5
        else:
            # Positive external pressure coefficients:
            # Zones 1, 2, and 3
            if pos:
                if area_eff <= 10:  # [ft^2]
                    gcp = 0.3
                elif 10 < area_eff <= 20:
                    m = (0.25 - 0.3) / (20 - 10)
                    gcp = m * (area_eff - 10) + 0.3
                elif 20 < area_eff <= 50:
                    m = (0.225 - 0.25) / (50 - 20)
                    gcp = m * (area_eff - 20) + 0.25
                elif 50 < area_eff <= 100:
                    m = (0.2 - 0.225) / (100 - 50)
                    gcp = m * (area_eff - 50) + 0.225
                elif area_eff > 100:
                    gcp = 0.2
            else:
                # Negative external pressure coefficients:
                if zone == 1:
                    if area_eff <= 10:  # [ft^2]
                        gcp = -1.0
                    elif 10 < area_eff <= 20:
                        m = (-0.975 - -1.0) / (20 - 10)
                        gcp = m * (area_eff - 10) - 1.0
                    elif 20 < area_eff <= 50:
                        m = (-0.95 - -0.975) / (50 - 20)
                        gcp = m * (area_eff - 20) - 0.975
                    elif 50 < area_eff <= 100:
                        m = (-0.9 - -0.95) / (100 - 50)
                        gcp = m * (area_eff - 50) - 0.95
                    elif area_eff > 100:
                        gcp = -0.9
                elif zone == 2:
                    if area_eff <= 10:
                        gcp = -1.8
                    elif 10 < area_eff <= 20:
                        m = (-1.6 - -1.8) / (20 - 10)
                        gcp = m * (area_eff - 10) - 1.8
                    elif 20 < area_eff <= 50:
                        m = (-1.325 - -1.6) / (50 - 20)
                        gcp = m * (area_eff - 20) - 1.6
                    elif 50 < area_eff <= 100:
                        m = (-1.1 - -1.325) / (100 - 50)
                        gcp = m * (area_eff - 50) - 1.325
                    elif area_eff > 100:
                        gcp = -1.1
                elif zone == 3:
                    if area_eff <= 10:  # [ft^2]
                        gcp = -2.8
                    elif 10 < area_eff <= 20:
                        m = (-2.3 - -2.8) / (20 - 10)
                        gcp = m * (area_eff - 10) - 2.8
                    elif 20 < area_eff <= 50:
                        m = (-1.6 - -2.3) / (50 - 20)
                        gcp = m * (area_eff - 20) - 2.3
                    elif 50 < area_eff <= 100:
                        m = (-1.1 - -1.6) / (100 - 50)
                        gcp = m * (area_eff - 50) - 1.6
                    elif area_eff > 100:
                        gcp = -1.1

        return gcp

    def wall_cc(self, area_eff, pos, zone, edition):
        # Area_eff needs to be in units of ft^2
        area_eff = area_eff * 10.764
        if edition == 'ASCE 7-93' or edition == 'ASCE 7-88':
            # Positive external pressure coefficients:
            # Zones 4 and 5
            if pos:
                if area_eff <= 10:  # [ft^2]
                    gcp = 1.4
                elif 10 < area_eff <= 20:
                    m = (1.3 - 1.4) / (20 - 10)
                    gcp = m * (area_eff - 10) + 1.4
                elif 20 < area_eff <= 50:
                    m = (1.225 - 1.3) / (50 - 20)
                    gcp = m * (area_eff - 20) + 1.3
                elif 50 < area_eff <= 100:
                    m = (1.15 - 1.225) / (100 - 50)
                    gcp = m * (area_eff - 50) + 1.225
                elif 100 < area_eff <= 200:
                    m = (1.1 - 1.15) / (200 - 100)
                    gcp = m * (area_eff - 100) + 1.15
                elif 200 < area_eff <= 500:
                    m = (1.0 - 1.1) / (500 - 200)
                    gcp = m * (area_eff - 200) + 1.1
                elif area_eff > 500:
                    gcp = 1.0
            else:
                # Negative external pressure coefficients:
                if zone == 4:
                    if area_eff <= 10:  # [ft^2]
                        gcp = -1.5
                    elif 10 < area_eff <= 20:
                        m = (-1.425 - -1.5) / (20 - 10)
                        gcp = m * (area_eff - 10) - 1.5
                    elif 20 < area_eff <= 50:
                        m = (-1.325 - -1.425) / (50 - 20)
                        gcp = m * (area_eff - 20) - 1.425
                    elif 50 < area_eff <= 100:
                        m = (-1.25 - -1.325) / (100 - 50)
                        gcp = m * (area_eff - 50) - 1.325
                    elif 100 < area_eff <= 200:
                        m = (-1.2 - -1.25) / (200 - 100)
                        gcp = m * (area_eff - 100) - 1.25
                    elif 200 < area_eff <= 500:
                        m = (-1.1 - -1.2) / (500 - 200)
                        gcp = m * (area_eff - 200) - 1.2
                    elif area_eff > 500:
                        gcp = -1.1
                elif zone == 5:
                    # Zone 5
                    if area_eff <= 10:  # [ft^2]
                        gcp = -2.0
                    elif 10 < area_eff <= 20:
                        m = (-1.85 - -2.0) / (20 - 10)
                        gcp = m * (area_eff - 10) - 2.0
                    elif 20 < area_eff <= 50:
                        m = (-1.625 - -1.85) / (50 - 20)
                        gcp = m * (area_eff - 20) - 1.85
                    elif 50 < area_eff <= 100:
                        m = (-1.475 - -1.625) / (100 - 50)
                        gcp = m * (area_eff - 50) - 1.625
                    elif 100 < area_eff <= 200:
                        m = (-1.3 - -1.475) / (200 - 100)
                        gcp = m * (area_eff - 100) - 1.475
                    elif 200 < area_eff <= 500:
                        m = (-1.1 - -1.3) / (500 - 200)
                        gcp = m * (area_eff - 200) - 1.3
                    elif area_eff > 500:
                        gcp = -1.1
        else:
            # Positive external pressure coefficients:
            # Zones 4 and 5
            if pos:
                if area_eff <= 10:  # [ft^2]
                    gcp = 1.0
                elif 10 < area_eff <= 20:
                    m = (0.95 - 1.0) / (20 - 10)
                    gcp = m * (area_eff - 10) + 1.0
                elif 20 < area_eff <= 50:
                    m = (0.85 - 0.95) / (50 - 20)
                    gcp = m * (area_eff - 20) + 0.95
                elif 50 < area_eff <= 100:
                    m = (0.825 - 0.85) / (100 - 50)
                    gcp = m * (area_eff - 50) + 0.85
                elif 100 < area_eff <= 200:
                    m = (0.775 - 0.825) / (200 - 100)
                    gcp = m * (area_eff - 100) + 0.825
                elif 200 < area_eff <= 500:
                    m = (0.7 - 0.775) / (500 - 200)
                    gcp = m * (area_eff - 200) + 0.775
                elif area_eff > 500:
                    gcp = 0.7
            else:
                # Negative external pressure coefficients:
                if zone == 4:
                    if area_eff <= 10:  # [ft^2]
                        gcp = -1.1
                    elif 10 < area_eff <= 20:
                        m = (-1.05 - -1.1) / (20 - 10)
                        gcp = m * (area_eff - 10) - 1.1
                    elif 20 < area_eff <= 50:
                        m = (-0.975 - -1.05) / (50 - 20)
                        gcp = m * (area_eff - 20) - 1.05
                    elif 50 < area_eff <= 100:
                        m = (-0.95 - -0.975) / (100 - 50)
                        gcp = m * (area_eff - 50) - 0.975
                    elif 100 < area_eff <= 200:
                        m = (-0.85 - -0.95) / (200 - 100)
                        gcp = m * (area_eff - 100) - 0.95
                    elif 200 < area_eff <= 500:
                        m = (-0.8 - -0.85) / (500 - 200)
                        gcp = m * (area_eff - 200) - 0.85
                    elif area_eff > 500:
                        gcp = -0.8
                elif zone == 5:
                    # Zone 5
                    if area_eff <= 10:  # [ft^2]
                        gcp = -1.4
                    elif 10 < area_eff <= 20:
                        m = (-1.3 - -1.4) / (20 - 10)
                        gcp = m * (area_eff - 10) - 1.4
                    elif 20 < area_eff <= 50:
                        m = (-1.15 - -1.3) / (50 - 20)
                        gcp = m * (area_eff - 20) - 1.3
                    elif 50 < area_eff <= 100:
                        m = (-1.05 - -1.15) / (100 - 50)
                        gcp = m * (area_eff - 50) - 1.15
                    elif 100 < area_eff <= 200:
                        m = (-0.95 - -1.05) / (200 - 100)
                        gcp = m * (area_eff - 100) - 1.05
                    elif 200 < area_eff <= 500:
                        m = (-0.8 - -0.95) / (500 - 200)
                        gcp = m * (area_eff - 200) - 0.95
                    elif area_eff > 500:
                        gcp = -0.8

        return gcp

    def get_warea(self, ctype, parcel_flag, h_story):
        # Determine the effective area for a wall C&C:
        if ctype == 'mullion':
            if parcel_flag == 1:
                if h_story <= 15/3.281:  # [m]
                    area_eff = h_story*(5/3.281)  # [m^2]
                else:
                    area_eff = h_story*h_story/3  # [m^2]
            else:
                pass
        elif ctype == 'glass curtain wall':
            if parcel_flag == 1:
                area_eff = (h_story/2)*(5/3.281)  # [m^2]
            else:
                pass
        elif ctype == 'wall':
            area_eff = h_story*h_story/3  # [m^2]

        return area_eff

    def get_rarea(self, ctype, parcel_flag, h_story):
        # Determine the effective area for roof C&C:
        if ctype == 'Metal deck':
            pass


    def base_bldg(self):
        # Base building parameters:
        base_exposure = 'C'
        base_story = 9/3.281 # [m]
        base_height = 9/3.281 # [m]
        return base_exposure, base_story, base_height

    def get_mwfrs_pressure(self, wind_speed, exposure, edition, h_story, h_bldg):
        # Given the input building parameters, return the pressure for the specified component:
        # Base building parameters:
        base_exposure, base_story, base_height = PressureCalc.base_bldg(self)
        # Filter #1: Code editions:
        if edition == 'ASCE 7-88' or edition == 'ASCE 7-93':
            pass
        elif edition == 'ASCE 7-95':
            pass
        elif edition == 'ASCE 7-98' or edition == 'ASCE 7-02' or edition == 'ASCE 7-05':
            pass
        elif edition == 'ASCE 7-10':
            if h_story == base_story and exposure == base_exposure and h_bldg == base_height:
                # Quadratic function parameters:
                a = 1
                b = 2
                c = 3 - wind_speed

        elif edition == 'ASCE 7-16':
            pass

    def get_sim(self, a, b, c):
        # Solve the quadratic equation ax**2 + bx + c = 0
        # Calculate the discriminant
        d = (b ** 2) - (4 * a * c)
        # Find two solutions
        sol1 = (-b - cmath.sqrt(d)) / (2 * a)
        sol2 = (-b + cmath.sqrt(d)) / (2 * a)

        print('The solution are {0} and {1}'.format(sol1, sol2))


def func(x, a, b, c):
    return a*(x**2)+b*x+c


# Case study #1: Same building, different wind speeds:
base_exposure = 'B'
base_story = 9 / 3.281  # [m]
base_height = 9 / 3.281  # [m]
z = base_height
# Define a range of wind speed values:
wind_speed = np.linspace(90, 180, 9)/2.237 # [m]/[s]
# Create an instance of PressureCalc()
pressures = PressureCalc()
# Start with ASCE 7-10:
edition = 'ASCE 7-10'
# Set up a dataframe to compare values:
df = pd.DataFrame(columns=['Zone 1', 'Zone 2', 'Zone 3', 'Zone 4'])
# Play with roof mwfrs:

# Set up a matplotlib figure:
fig, ax = plt.subplots()

# Set up placeholder:
rmps_arr = np.array([])
for speed in wind_speed:
    rmps = pressures.rmwfrs_capacity(speed, base_exposure, edition, base_height, 3.0*base_height)
    # Add values to Dataframe:
    df = df.append({'Zone 1': rmps[0], 'Zone 2': rmps[1], 'Zone 3': rmps[2], 'Zone 4': rmps[3]}, ignore_index = True)
# Plot the results:
ax.plot(df['Zone 1']*0.020885, wind_speed * 2.237)
ax.plot(df['Zone 2']*0.020885, wind_speed * 2.237)
ax.plot(df['Zone 3']*0.020885, wind_speed * 2.237)
ax.plot(df['Zone 4']*0.020885, wind_speed * 2.237)
ax.legend(['Zone 1', 'Zone 2', 'Zone 3', 'Zone 4'])

#params = curve_fit(func, wall_pressures[:,3], wind_speed*2.237)
#[a, b, c] = params[0]
#fit_curve = ax.plot(wall_pressures[:, 3], func(wall_pressures[:,3], a, b, c), label=str(area * 10.7639))


plt.title('Roof uplift pressures (MWFRS) for all zones vs. Wind speed for h=9.0 ft')
plt.ylabel('Wind Speed [mph]')
plt.xlabel('Pressure [psf]')
plt.ylim(90, max(wind_speed)*2.237)
plt.show()

print(df)

# Figure out the pressure difference for various heights:
print('percent change in wind speed:')
print(df.pct_change(axis=0))
# Figure out the pressure difference between zones:
print('percent change in pressure by zone:')
print(df.pct_change(axis=1))

# Figure out what the percent difference is from the base wind speed to other wind speeds:
for row in range(0, len(df['Zone 4'])):
    a =df['Zone 4'][0]
    if row > 0:
        pct = (df['Zone 4'][0] - df['Zone 4'][row])/df['Zone 4'][0]
        print(pct)
    else:
        pass

# Time to figure out the differences in height across zone pressures:
# Set up a dataframe to compare values:
dfh = pd.DataFrame()
# Play with roof mwfrs:
h_bldg = np.array([base_height, 2*base_height, 3*base_height, 4*base_height])
# Set up a matplotlib figure:
fig, ax = plt.subplots()

# Set up placeholder:

for h in h_bldg:
    rmps_arr = np.array([])
    for speed in wind_speed:
        rmps = pressures.rmwfrs_capacity(speed, base_exposure, edition, h, 1.5*base_height)
        print('rmps', rmps)
        rmps_arr = np.append(rmps_arr, rmps[2])
    # Add values to DataFrame:
    col_name = str(h)
    dfh[col_name] = rmps_arr
    # Plot the results:
    ax.plot(dfh[col_name] * 0.020885, wind_speed * 2.237)
# Plot the results:
ax.legend(['h = 9.0 ft', 'h = 18.0 ft', 'h = 27.0 ft', 'h = 36.0 ft'])
plt.title('Roof uplift pressures (MWFRS) for Zone 1 vs. Wind speed for various heights')
plt.ylabel('Wind Speed [mph]')
plt.xlabel('Pressure [psf]')
plt.ylim(90, max(wind_speed)*2.237)
plt.show()

# Figure out the pressure difference for various heights:
print('percent change in height:')
a = dfh.pct_change(axis=1)
print(dfh.pct_change(axis=1))
# Try for a different exposure category:
#exposure = 'B'
#df2 = pd.DataFrame()

#for h in h_bldg:
    #rmps_arr = np.array([])
    #for speed in wind_speed:
        #wps, rps, rmps = pressures.run(z, speed, exposure, edition, r_mwfrs, h, w_cc=False, r_cc=False, area_eff=None)
        # Each row in rmps will contain as many pressures as zones identified:
        #rmps[2] = rmps[2]*0.020885
        #rmps_arr = np.append(rmps_arr, rmps[2])
    # Append column of pressures for various wind speeds for this height:
    #col_name = str(h*3.281)
    #df2[col_name] = rmps_arr

#print(df2)

# Check the difference between Exposure B and Exposure C:
print((df['10.0']-df2['10.0'])/df['10.0'], (df['20.0']-df2['20.0'])/df['20.0'], (df['30.0']-df2['30.0'])/df['30.0'], (df['40.0']-df2['40.0'])/df['40.0'])

# Set up a matplotlib figure:
fig, ax = plt.subplots()
line = ax.plot(rmps_arr, wind_speed*2.237)
plt.ylim(90, max(wind_speed)*2.237)
plt.show()


df_wcc = pd.DataFrame()
# Set up array of effective areas:
area_eff= np.array([27, 90])/10.764
# Set up empty numpy arrays to store wall and roof pressures:
wall_pressures = np.empty((0, 4))
roof_pressures = np.empty((0, 6))
w_cc = True
r_cc = False
h_bldg = 9 / 3.281
count = 0
fig2, ax2 = plt.subplots()
for area in area_eff:
    wall_pressures = np.empty((0, 4))
    roof_pressures = np.empty((0, 6))
    for speed in wind_speed:
        wps, rps, rmps = pressures.run(z, speed, exposure, edition, r_mwfrs, h_bldg, w_cc, r_cc, area)
        # Add to our empty array:
        wall_pressures = np.append(wall_pressures, np.array([wps]), axis=0)
        #roof_pressures = np.append(roof_pressures, np.array([rps]), axis=0)
    count = count + 1
    line = ax2.plot(wall_pressures[:,0]*0.020885, wind_speed*2.237, label='bound'+str(count))
    # Append column of pressures for various wind speeds for this height:
    col_name = str(area)
    df_wcc[col_name] = wall_pressures[:,0]
    #params = curve_fit(func, wall_pressures[:,3], wind_speed*2.237)
    #[a, b, c] = params[0]
    #fit_curve = ax.plot(wall_pressures[:, 3], func(wall_pressures[:,3], a, b, c), label=str(area * 10.7639))

#ax.legend()
#plt.ylim(90, max(wind_speed)*2.237)
print('percent change in effective area:')
print(df_wcc.pct_change(axis=1))
ax2.legend()
plt.ylim(90, max(wind_speed)*2.237)
plt.title('Mullion C&C bounds (+), Zones 4 and 5 for h = ' + str(h_bldg*3.281)+ ' [ft]')
plt.ylabel('Wind Speed [mph]')
plt.xlabel('Pressure [psf]')
plt.show()

# First I need to determine the effective area for the component that I am interested in:
ctype = 'mullion'
parcel_flag = 1
h_story = 10/3.281
h_bldg = np.array([h_story, h_story*2, h_story*3, h_story*4, h_story*5, h_story*6])
fig3, ax3 = plt.subplots()
df_wccm = pd.DataFrame()

for h in h_bldg:
    wall_pressures = np.empty((0, 4))
    area_eff = pressures.get_warea(ctype, parcel_flag, h_story)
    for speed in wind_speed:
        # Calculate the pressure across various wind speeds, heights, and exposures:
        wps = pressures.wcc_capacity(speed, exposure, edition, h, area_eff)
        wall_pressures = np.append(wall_pressures, np.array([wps]), axis=0)
    line = ax3.plot(wall_pressures[:, 1] * 0.020885, wind_speed * 2.237, label= str(round(h*3.281))+ ' ft')
    col_name = str(h*3.281)
    df_wccm[col_name] = wall_pressures[:, 1]* 0.020885

ax3.legend()
plt.ylim(90, max(wind_speed)*2.237)
plt.ylabel('Wind Speed [mph]')
plt.xlabel('Pressure [psf]')
plt.title('Mullion C&C pressures (-), Zone 5 for h_story = h_bldg')
plt.show()

pct_change = df_wccm.pct_change(axis=1)
print(df_wccm.pct_change(axis=1))

print((df_wccm['10.0']-df_wccm['60.0'])/df_wccm['10.0'])
# Plot the range of pressures for all wind speeds:
#plt.plot(wall_pressures[:,0], wind_speed)
#plt.plot(wall_pressures[:,1], wind_speed)
#plt.plot(wall_pressures[:,2], wind_speed)
#plt.plot(wall_pressures[:,3], wind_speed)
#plt.show()
# Let's plot and see if it works:
# areas = np.arange(0.1, 93, 0.1)
# gcp_lst = np.array([])
# for area in areas:
# gcp = roof_cc(area, pos=False, zone=3)
# gcp_lst = np.append(gcp_lst, gcp)

# plt.plot(areas, gcp_lst)
# plt.show()
