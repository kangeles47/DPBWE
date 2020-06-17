import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import cmath
import csv
from scipy.optimize import curve_fit

class PressureCalc:

    def wcc_capacity(self, wind_speed, exposure, edition, h_bldg, area_eff):
        # Determine GCpis for pressure calculation:
        gcpi = PressureCalc.get_gcpi(self, edition, encl_class='Enclosed')
        # Determine components and cladding pressure for building facade components:
        is_cc = True
        # All components and cladding calculations require qh:
        qh, alpha = PressureCalc.qz_calc(self, h_bldg, wind_speed, exposure, edition, is_cc, cat)
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
            p = PressureCalc.calc_pressure(self, h_bldg, exposure, edition, is_cc, qh, gcp, gcpi)
            wps.append(p)

        return wps

    def rcc_capacity(self, wind_speed, exposure, edition, h_bldg, area_eff):
        # Determine GCpis for pressure calculation:
        gcpi = PressureCalc.get_gcpi(self, edition, encl_class='Enclosed')
        # Determine components and cladding pressure for building roof components:
        is_cc = True
        # All components and cladding calculations require qh:
        qh, alpha = PressureCalc.qz_calc(self, h_bldg, wind_speed, exposure, edition, is_cc, cat)
        # Get GCps and calculate the pressure for each zone:
        rpos = [True, True, True, False, False, False]
        rzone = [1, 2, 3, 1, 2, 3]
        rps = list()
        for ind in range(0, len(rpos)):
            # Find the GCp
            gcp = PressureCalc.roof_cc(self, area_eff, rpos[ind], rzone[ind], edition)
            # Calculate pressure at the zone:
            p = PressureCalc.calc_pressure(self, h_bldg, exposure, edition, is_cc, qh, gcp, gcpi)
            rps.append(p)
        return rps

    def rmwfrs_capacity(self, wind_speed, exposure, edition, h_bldg, length, ratio, cat):
        # Determine GCpis for pressure calculation:
        gcpi = PressureCalc.get_gcpi(self, edition, encl_class='Enclosed')
        # Determine the velocity pressure:
        is_cc = False
        # Roof uplift pressures require qh:
        qh, alpha = PressureCalc.qz_calc(self, h_bldg, wind_speed, exposure, edition, is_cc, cat)
        # Get the gust effect or gust response factor:
        g = PressureCalc.get_g(self, edition, exposure, is_cc, alpha, h_bldg)
        # Set up to find Cp values:
        direction = 'parallel'
        pitch = 9
        # Set up placeholders for Cp values:
        rmps = list()
        # Find the Cps:
        cp = PressureCalc.roof_mwfrs(self, h_bldg, direction, ratio, pitch, length)
        for row in cp:
            gcp = g * row[0]  # Take the first Cp value for uplift calculations
            # Calculate uplift pressure at the zone:
            p = PressureCalc.calc_pressure(self, h_bldg, exposure, edition, is_cc, qh, gcp, gcpi)
            # Minimum design pressures for roof MWFRS:
            #if abs(p) < 10:
                #if edition != 'ASCE 7-10':  # [psf]
                    #p = np.sign(p) * 10  # [psf]
                #elif abs(p) < 8 and edition == 'ASCE 7-10':
                    #p = np.sign(p) * 8  # [psf]
            #else:
                #pass
            rmps.append(p)

        return rmps

    def run(self, z, wind_speed, exposure, edition, r_mwfrs, h_bldg, w_cc, r_cc, area_eff, cat):
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
            g = PressureCalc.get_g(self, edition, exposure, is_cc, alpha, h_bldg)
            # Set up to find Cp values:
            direction = 'parallel'
            pitch = 9
            ratio = 0.5
            # Set up placeholders for Cp values:
            rmps = list()
            # Find the Cps:
            cp = PressureCalc.roof_mwfrs(self, h_bldg, direction, ratio, pitch, length)
            for row in cp:
                gcp = g*cp[0][0] # Take the first Cp value for uplift calculations
                # Calculate uplift pressure at the zone:
                p = PressureCalc.calc_pressure(self, z, exposure, edition, is_cc, qh, gcp, gcpi)
                # Minimum design pressure for roof MWFRS (ASCE 7-10):
                if abs(p) < 8 and edition == 'ASCE 7-10':  # [psf]
                    p = np.sign(p) * 8  # [psf]
                else:
                    pass
                rmps.append(p)
        # Determine pressure for components and cladding:
        if w_cc or r_cc:
            # C&C loads:
            is_cc = True
            # All components and cladding calculations require qh:
            qh, alpha = PressureCalc.qz_calc(self, h_bldg, wind_speed, exposure, edition, is_cc, cat)
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

    def get_g(self, edition, exposure, is_cc, alpha,z):
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
                tz = (2.35 * (d0) ** (1 / 2)) / ((z /30) ** (1 / alpha))
                g = 0.65 + 3.65 * tz
            else:
                tz = (2.35 * (d0) ** (1 / 2)) / ((z /30) ** (1 / alpha))
                g = 0.65 + 3.65 * tz
        else:  # All other editions of ASCE 7
            g = 0.85
        return g

    # Laying out the code needed to replicate the pressures from ASCE 7
    def calc_pressure(self, z, exposure, edition, is_cc, q, gcp, gcpi):
        # Pressure calc: will need to code in a procedure to determine both +/- cases for GCpi
        if is_cc:
            if z <= 60:  # [ft]
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
            # Minimum design pressure for C&C (ASCE 7-10):
            #if abs(p) < 16 and edition == 'ASCE 7-10':  # [psf]
                #p = np.sign(p) * 16 # [psf]
            #elif abs(p) < 10 and edition != 'ASCE 7-10':
                #p = np.sign(p) * 10  # [psf]
        else:
            p = q * gcp - q * gcpi  # q = qz for roof (at mean roof height)

        return p

    def qz_calc(self, z, wind_speed, exposure, edition, is_cc, cat):
        hpr = True
        h_ocean = True
        # Every edition of ASCE 7 has a velocity exposure coefficient:
        kz, alpha = PressureCalc.get_kz(self, z, exposure, edition, is_cc)
        # Calculate the velocity pressure:
        if edition == 'ASCE 7-93' or edition == 'ASCE 7-88':
            imp = PressureCalc.get_i(self, z, wind_speed, hpr, h_ocean, cat)
            qz = 0.00256 * kz * (imp * wind_speed) ** 2
        elif edition == 'ASCE 7-95':
            kzt = 1.0
            imp = PressureCalc.get_i(self, z, wind_speed, hpr, h_ocean, cat)
            qz = 0.00256 * kz * kzt * imp * wind_speed ** 2
        elif edition == 'ASCE 7-98' or edition == 'ASCE 7-02' or edition == 'ASCE 7-05':
            kzt = 1.0
            kd = 0.85
            imp = PressureCalc.get_i(self, z, wind_speed, hpr, h_ocean, cat)
            qz = 0.00256 * kz * kzt * kd * imp * wind_speed ** 2
        elif edition == 'ASCE 7-10' or edition == 'ASCE 7-16':
            kzt = 1.0
            kd = 0.85
            qz = 0.00256 * kz * kzt * kd * wind_speed ** 2
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
            zg = 1500  # [ft]
            if edition == 'ASCE 7-93' or edition == 'ASCE 7-88':
                alpha = 3.0
            else:
                alpha = 5.0
        elif exposure == 'B':
            zg = 1200
            if edition == 'ASCE 7-93' or edition == 'ASCE 7-88':
                alpha = 4.5
            else:
                alpha = 7.0
        elif exposure == 'C':
            zg = 900
            if edition == 'ASCE 7-93' or edition == 'ASCE 7-88':
                alpha = 7.0
            else:
                alpha = 9.5
        elif exposure == 'D':
            alpha = 11.5
            zg = 700
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
        # Exception: ASCE 7-98-ASCE 7-10
        # Case 1a for all components and cladding and (7-10 Chapter 30 Provisions)
        # z shall not be taken as less than 30 feet for Case 1 in Exposure B
        if is_cc:
            if exposure == 'B' and (
                    edition == 'ASCE 7-98' or edition == 'ASCE 7-02' or edition == 'ASCE 7-05' or edition == 'ASCE 7-10'):
                if z < 30:
                    z = 30  # [ft]
                else:
                    pass
        # Calculate the velocity pressure coefficient:
        if z <= 15:  # [ft]
            kz = factor * (15 / zg) ** (2 / alpha)
        elif 15 < z < zg:
            kz = factor * (z / zg) ** (2 / alpha)
        return kz, alpha

    def get_i(self, z, wind_speed, hpr, h_ocean, cat):
        # Importance factor for ASCE 7-05 and older:
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
        # Assume effective wind area is in units of ft^2
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
        # Assume effective wind area is in units of ft^2
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
                if h_story <= 15:  # [ft]
                    area_eff = h_story*5  # [ft^2]
                else:
                    area_eff = h_story*h_story/3  # [ft^2]
            else:
                pass
        elif ctype == 'glass curtain wall':
            if parcel_flag == 1:
                area_eff = (h_story/2)*5  # [ft^2]
            else:
                pass
        elif ctype == 'wall':
            area_eff = h_story*h_story/3  # [ft^2]

        return area_eff

    def get_rarea(self, ctype, parcel_flag, h_story):
        # Determine the effective area for roof C&C:
        if ctype == 'Metal deck':
            pass


    def base_bldg(self):
        # Base building parameters:
        base_exposure = 'B'
        base_story = 9 # [ft]
        base_height = 9 # [ft]
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

    def get_sim_pressure(self, a, b, c):
        # Solve the quadratic equation ax**2 + bx + c = 0
        # Calculate the discriminant
        d = (b ** 2) - (4 * a * c)
        # Find two solutions
        sol1 = (-b - cmath.sqrt(d)) / (2 * a)
        sol2 = (-b + cmath.sqrt(d)) / (2 * a)

        print('The solution are {0} and {1}'.format(sol1, sol2))
        return sol1, sol2


def func(x, a, b, c):
    return a*(x**2)+b*x+c


# Case study #1: Same building, different wind speeds:
base_exposure = 'B'
base_height = 9  # [ft]
# Assume occupancy category is II for now (later add logic to identify tags for the region (MED, UNIV, etc.):
cat = 2
# Define a range of wind speed values:
wind_speed = np.arange(90, 185, 5)  # [mph]
# Create an instance of PressureCalc()
pressures = PressureCalc()
# Create a vector of editions:
edition = ['ASCE 7-95', 'ASCE 7-98', 'ASCE 7-10'] #, 'ASCE 7-16']
# Set up a dataframe to compare values:
#df = pd.DataFrame(columns=['Zone 1', 'Zone 2', 'Zone 3'], index=edition)
# Play with roof mwfrs:
length = 2*base_height
ratio = base_height/length

# Fit curves for each zone for each code edition
# Create an empty list that will hold DataFrames for each code edition:
ed_list = list()
for ed in edition:
    # Create a new dataframe for each edition:
    df = pd.DataFrame(columns=['Zone 1', 'Zone 2', 'Zone 3'])
    for speed in wind_speed:
        rmps = pressures.rmwfrs_capacity(speed, base_exposure, ed, base_height, length, ratio, cat)
        # Add values to Dataframe:
        df = df.append({'Zone 1': rmps[0], 'Zone 2': rmps[1], 'Zone 3': rmps[2]}, ignore_index=True)
    # Add DataFrame to list:
    ed_list.append(df)
    # Plot the results:
    #fig, ax = plt.subplots()
    #ax.plot(df['Zone 1'], wind_speed)
    #ax.plot(df['Zone 2'], wind_speed)
    #ax.plot(df['Zone 3'], wind_speed)
    #plt.title('Roof uplift pressures (MWFRS) for Zones 1-3 vs. Wind speed for h=9.0 ft')
    #plt.ylabel('Wind Speed [mph]')
    #plt.xlabel('Pressure [psf]')
    #plt.show()
    print('percent change between zones:', df.pct_change(axis=1))

# Next step: Fit a curve to each zone for each code edition and save to a .csv:
df_param = pd.DataFrame(columns=df.columns)
for dframe in ed_list:
    # Plot the results:
    #fig2, ax2 = plt.subplots()
    param_lst = list()
    for zone in range(0,3):
        col_names = dframe.columns
        params = curve_fit(func, dframe[col_names[zone]], wind_speed)
        [a, b, c] = params[0]
        #fit_curve = ax2.plot(dframe[col_names[zone]], func(dframe[col_names[zone]], a, b, c), label='Fitted Zone '+str(zone))
        #real_curve = ax2.plot(dframe[col_names[zone]], wind_speed, label='Real Zone '+str(zone))
        # Save parameters in list:
        param_lst.append([a,b,c])
    # Add parameters to DataFrame:
    df_param = df_param.append({col_names[0]: param_lst[0], col_names[1]: param_lst[1], col_names[2]: param_lst[2]}, ignore_index=True)
    # Uncomment to show curve fit for each zone
    #ax2.legend()
    #plt.title('Roof uplift pressures (MWFRS) for all zones vs. Wind speed for h=9.0 ft')
    #plt.ylabel('Wind Speed [mph]')
    #plt.xlabel('Pressure [psf]')
    #plt.ylim(min(wind_speed), max(wind_speed))
    #plt.show()

# Set the index to the corresponding code editions:
# Add column:
df_param['Edition'] = edition
df_param.set_index('Edition', inplace=True)
# Save the DataFrame to a .csv file for future reference:
#df_param.to_csv('Roof_MWFRS_05.csv')

# Get back the pressure for a specific wind speed:
y = 120  # [mph]
sim_pressure1, sim_pressure2 = pressures.get_sim_pressure(a, b, c-y)

# Figure out the pressure difference between wind speeds:
print('percent change in wind speed:')
print(df.pct_change(axis=0))
# Figure out the pressure difference between zones:
print('percent change in pressure by zone:')
print(df.pct_change(axis=1))

# Time to figure out the differences in height across zone pressures for h/L = 0.5 or wind direction = parallel:
# Create an empty list that will hold DataFrames for each code edition:
edh_list = list()
# Play with roof mwfrs:
h_bldg = np.arange(base_height, 61, 1)

for ed in edition:
    # Set up a dataframe to compare values:
    dfh = pd.DataFrame()
    # Set up a matplotlib figure:
    #fig3, ax3 = plt.subplots()
    for h in h_bldg:
        rmps_arr = np.array([])
        for speed in wind_speed:
            length = 2*h
            ratio = h/length
            rmps = pressures.rmwfrs_capacity(speed, base_exposure, ed, h, length, ratio, cat)
            rmps_arr = np.append(rmps_arr, rmps[0])  # Zone 1 since variation across heights is the same for all zones
        # Add values to DataFrame:
        col_name = str(h) + ' ft'
        dfh[col_name] = rmps_arr
        # Plot the results:
        #ax3.plot(dfh[col_name], wind_speed, label = str(h)+ ' ft')
    # Add DataFrame to list:
    edh_list.append(dfh)
    # Plot the results:
    #ax3.legend()
    #plt.title('Roof uplift pressures (MWFRS) for Zone 1 vs. Wind speed for various heights')
    #plt.ylabel('Wind Speed [mph]')
    #plt.xlabel('Pressure [psf]')
    #plt.ylim(90, max(wind_speed))
    #plt.show()
    # Print the percent change in pressure as height varies:
    print('Percent change in pressure between heights:', ed, dfh.pct_change(axis=1))

# Calculate the percent change in pressure (compared to base height):
df_hfactor = pd.DataFrame()
row = dfh.iloc[0] # Only need one since variation with height is same for all codes
for index in range(0, len(row)):
    if index == 0:
        factor = 1.0
    elif row[index] == row[0]:
        factor = 1.0
    else:
        factor = (row[index]-row[0])/row[0]
    hcol_name = dfh.columns[index]
    df_hfactor[hcol_name] = np.array([factor])
# Save the DataFrame to a .csv file for future reference:
#df_hfactor.to_csv('Roof_MWFRS_h.csv')

# Try for a different exposure category:
exposures = ['B', 'C', 'D']
# Exposure effects change with height:
h_bldg = np.arange(base_height, 61, 1)
# Specify code editions:
edition = ['ASCE 7-95','ASCE 7-10']
# Set up an empty list to store the dataframes:
exp_list = list()

for ed in edition:
    # Set up DataFrame to save pressure difference across exposure categories for various heights:
    df_Efactor = pd.DataFrame(columns=exposures)
    for h in h_bldg:
        dfE = pd.DataFrame()
        #fig4, ax4 = plt.subplots()
        for exp in exposures:
            rmps_arr = np.array([])
            for speed in wind_speed:
                length = 2 * h
                ratio = h / length
                rmps = pressures.rmwfrs_capacity(speed, exp, ed, h, length, ratio, cat)
                rmps_arr = np.append(rmps_arr, rmps[1])
            # Add values to DataFrame:
            dfE[exp] = rmps_arr
            # Plot the results (Exposures B, C, D for one height:
            #ax4.plot(dfE[exp], wind_speed, label=exp)
        # Plot the results:
        #ax4.legend()
        #plt.title('Roof uplift pressures (MWFRS, Zone 1) and h = '+str(h)+ ' ft')
        #plt.ylabel('Wind Speed [mph]')
        #plt.xlabel('Pressure [psf]')
        #plt.ylim(90, max(wind_speed))
        #plt.show()
        # Check the percent change between Exposure categories:
        #print('percent change in pressure by Exposure Category by h:', h, exp)
        #print(dfE.pct_change(axis=1))
        # Calculate the percent change from Exposure B:
        row = dfE.iloc[0]
        factor_list = list()
        for index in range(0, len(row)):
            if index == 0:
                factor = 1.0
            elif row[index] == row[0]:
                factor = 1.0
            else:
                factor = (row[index] - row[0]) / row[0]
            factor_list.append(factor)
        df_Efactor = df_Efactor.append({'B': factor_list[0], 'C': factor_list[1], 'D': factor_list[2]}, ignore_index=True)
    # Set the index to the corresponding building heights:
    # Add column:
    df_Efactor['Height in ft'] = h_bldg
    df_Efactor.set_index('Height in ft', inplace=True)
    # Store the DataFrame of Exposure factors:
    exp_list.append(df_Efactor)

# Save the DataFrame to a .csv file for future reference:
#df_Efactor.to_csv('Roof_MWFRS_Exp.csv')

# Time to play with Wall C&C pressures --> Mullions:
# Define the reference building and site conditions:
ref_exposure = 'B'
ref_story = 9  # [ft]
ref_height = 9  # [ft]
# Assume occupancy category is II for now (later add logic to identify tags for the region (MED, UNIV, etc.):
cat = 2
# Define a range of wind speed values:
wind_speed = np.arange(90, 185, 5)  # [mph]
# Create an instance of PressureCalc()
pressures = PressureCalc()
# Create a vector of editions:
edition = ['ASCE 7-93', 'ASCE 7-95', 'ASCE 7-98', 'ASCE 7-10']

# Case 1: Reference building against various wind speeds for various editions:
# Determine the effective area using typical practice:
ctype = 'mullion'
parcel_flag = 1
area_eff = pressures.get_warea(ctype, parcel_flag, ref_story)

# Create an empty list to hold all DataFrames:
edw_list = list()
for ed in edition:
    # Create a new dataframe for each edition:
    df_wcc = pd.DataFrame(columns=['Zone 4+', 'Zone 5+', 'Zone 4-', 'Zone 5-'])
    # Set up plotting
    #fig, ax = plt.subplots()
    for speed in wind_speed:
        # Calculate the pressure across various wind speeds for each code edition:
        wps = pressures.wcc_capacity(speed, ref_exposure, ed, ref_height, area_eff)
        # Add values to Dataframe:
        df_wcc = df_wcc.append({'Zone 4+': wps[0], 'Zone 5+': wps[1], 'Zone 4-': wps[2], 'Zone 5-': wps[3]}, ignore_index=True)
    # Add DataFrame to list:
    edw_list.append(df_wcc)
    # Plot Zone pressures for 1 case (Zones 4 and 5 (+) are equal):
    #ax.plot(df_wcc['Zone 4+'], wind_speed)
    #plt.ylim(90, max(wind_speed))
    #plt.ylabel('Wind Speed [mph]')
    #plt.xlabel('Pressure [psf]')
    #plt.title('Mullion C&C pressures (+), Zones 4 and 5 for h_story = 9.0 ft')
    #plt.show()
    # Show the difference in pressure between zones for the typical effective wind area
    print('percent change between zones:', ed, df_wcc.pct_change(axis=1))
    print('percent change in wind speed:', ed, df_wcc.pct_change(axis=0))

# Next step: Fit a curve to each zone for each code edition and save to a .csv:
df_wparam = pd.DataFrame(columns=df.columns)
for dwframe in edw_list:
    # Plot the results:
    #fig2, ax2 = plt.subplots()
    param_lst = list()
    for zone in range(0,3):
        col_names = dwframe.columns
        params = curve_fit(func, dwframe[col_names[zone]], wind_speed)
        [a, b, c] = params[0]
        #fit_curve = ax2.plot(dwframe[col_names[zone]], func(dwframe[col_names[zone]], a, b, c), label='Fitted Zone '+str(zone))
        #real_curve = ax2.plot(dwframe[col_names[zone]], wind_speed, label='Real Zone '+str(zone))
        # Save parameters in list:
        param_lst.append([a,b,c])
    # Add parameters to DataFrame:
    df_wparam = df_wparam.append({col_names[0]: param_lst[0], col_names[1]: param_lst[1], col_names[2]: param_lst[2]}, ignore_index=True)

# Set the index to the corresponding code editions:
# Add column:
df_wparam['Edition'] = edition
df_wparam.set_index('Edition', inplace=True)
# Save the DataFrame to a .csv file for future reference:
#df_wparam.to_csv('Mullion_Ref.csv')

# Reference Building with more than 1 story:
# Define an array of building heights:
h_bldg = np.arange(ref_height*1, ref_height*7, ref_height)  # [ft], all heights < 60 ft
# Percent change in pressure between heights is same for all Zones
# Two groups: ASCE 7-95 and older vs. ASCE 7-98 and older, here we are going to collect all for easy access/comparison
dfw_hfactor = pd.DataFrame()

for ed in edition:
    # Set up a dataframe to compare values:
    dfwh = pd.DataFrame()
    # Set up a matplotlib figure:
    #fig3, ax3 = plt.subplots()
    for h in h_bldg:
        wps_arr = np.array([])
        for speed in wind_speed:
            # Calculate the pressure across various wind speeds for each code edition:
            wps = pressures.wcc_capacity(speed, ref_exposure, ed, h, area_eff)
            wps_arr = np.append(wps_arr, wps[0])  # Zone 4+ since variation across heights is the same for all zones
        # Add values to DataFrame:
        col_name = str(h) + ' ft'
        dfwh[col_name] = wps_arr
        # Plot the results:
        #ax3.plot(dfwh[col_name], wind_speed, label = str(h)+ ' ft')
    # Plot the results:
    #ax3.legend()
    #plt.title('Mullion Pressures (C&C) for Zone 4 (+) vs. Wind speed for various building heights')
    #plt.ylabel('Wind Speed [mph]')
    #plt.xlabel('Pressure [psf]')
    #plt.ylim(90, max(wind_speed))
    #plt.show()
    # Print the percent change in pressure as height varies:
    print('Percent change in pressure between heights:', ed, dfwh.pct_change(axis=1))
    # Determine the percent change in pressure (compared to reference height) for each code edition:
    row = dfwh.iloc[0] # Get first row of each DataFrame to find variation with height (same for all wind speeds)
    factor_list = list()
    for index in range(0, len(row)):
        if index == 0:
            factor = 1.0
        elif row[index] == row[0]:
            factor = 1.0
        else:
            factor = (row[index]-row[0])/row[0]
        factor_list.append(factor)
    # Create a quick dictionary:
    factor_dict = {dfwh.columns[i]: factor_list[i] for i in range(len(factor_list))}
    dfw_hfactor = dfw_hfactor.append(factor_dict, ignore_index=True)

# Set the index to the corresponding code editions:
# Add column:
dfw_hfactor['Edition'] = edition
dfw_hfactor.set_index('Edition', inplace=True)
# Save the DataFrame to a .csv file for future reference:
#dfw_hfactor.to_csv('Mullion_RefH.csv')



# Reference Building with range of effective wind areas using typical practice:
df_wcc = pd.DataFrame()
# Set up array of effective areas:
area_eff= np.array([27, 45, 54, 90]) # [ft^2]
# Set up empty numpy arrays to store wall and roof pressures:
wall_pressures = np.empty((0, 4))
r_mwfrs = False
w_cc = True
r_cc = False
h_bldg = 9 # [ft]
count = 0
fig, ax = plt.subplots()
edition = 'ASCE 7-10'

for area in area_eff:
    wall_pressures = np.empty((0, 4))
    for speed in wind_speed:
        wps = pressures.wcc_capacity(speed, ref_exposure, edition, ref_height, area)
        # Add to our empty array:
        wall_pressures = np.append(wall_pressures, np.array([wps]), axis=0)
    count = count + 1
    line = ax.plot(wall_pressures[:,0], wind_speed, label=str(area)+ 'sq ft')
    # Append column of pressures for various wind speeds for this height:
    col_name = str(area)
    df_wcc[col_name] = wall_pressures[:,0]
    #params = curve_fit(func, wall_pressures[:,3], wind_speed*2.237)
    #[a, b, c] = params[0]
    #fit_curve = ax.plot(wall_pressures[:, 3], func(wall_pressures[:,3], a, b, c), label=str(area * 10.7639))

print('percent change in effective area:')
print(df_wcc.pct_change(axis=1))
ax.legend()
plt.ylim(90, max(wind_speed))
plt.title('Mullion C&C bounds (+), Zones 4 and 5 for h = ' + str(h_bldg)+ ' [ft]')
plt.ylabel('Wind Speed [mph]')
plt.xlabel('Pressure [psf]')
plt.show()
