import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from OBDM.element import Wall, Roof


class PressureCalc:

    def wcc_pressure(self, wind_speed, exposure, edition, h_bldg, pitch, area_eff, cat, hpr, h_ocean, encl_class, tpu_flag):
        """
        Orchestrates the calculation of design pressures per zone for the given C&C effective area (facade C&C).

        Accesses GCPi for pressure calculation (get_gcpi).
        Calculates velocity pressure and extracts alpha from power law (qz_calc).
        Obtains GCp for each Zone (4, 5) and sign (+, -) (get_wcc_gcp).
        Calculates pressure for each zone (calc_pressure).

        Parameters:
            wind_speed: The wind speed the building is subject to
            exposure: A string providing the ASCE 7 Exposure Category
            edition: A string naming the edition of ASCE 7 wind loading provision for the building
            h_bldg: The building height
            pitch: The roof pitch needed to determine the appropriate use case for the building
            area_eff: Effective wind area for a component type
            cat: A string with the ASCE 7 Importance Factor Category
            hpr: A Boolean indicating if the location is in a hurricane-prone region (True/False, Yes/No)
            h_ocean: A Boolean identifying if building is at hurricane oceanline (ASCE 7-88 and 7-93)
            encl_class: A string with ASCE 7 Enclosure Class ('Enclosed', 'Partial', 'Open')

        Returns:
            wps: (List) Zone pressures for each zone number and sign (ordered Zone4+, Zone5+, Zone4-, Zone5-).
        """
        # Determine GCpis for pressure calculation:
        gcpi = PressureCalc.get_gcpi(self, edition, encl_class)
        # Determine components and cladding pressure for building facade components:
        is_cc = True
        # All components and cladding calculations require qh:
        qh, alpha = PressureCalc.qz_calc(self, h_bldg, wind_speed, exposure, edition, is_cc, cat, hpr, h_ocean, tpu_flag)
        # Get GCps and calculate the pressure for each zone:
        wpos = [True, True, False, False]
        wzone = [4, 5, 4, 5]
        wps = list()
        for ind in range(0, len(wpos)):
            # Find the GCp
            gcp = PressureCalc.get_wcc_gcp(self, area_eff, wpos[ind], wzone[ind], edition)
            # Reduce GCp for walls if roof pitch is <= 10 degrees:
            if pitch <= 10:
                gcp = 0.9 * gcp
            else:
                pass
            # Calculate pressure at the zone:
            p = PressureCalc.calc_pressure(self, h_bldg, edition, is_cc, qh, gcp, gcpi, tpu_flag)
            wps.append(p)

        return wps

    def rcc_pressure(self, wind_speed, exposure, edition, h_bldg, pitch, area_eff, cat, hpr, h_ocean, encl_class, tpu_flag):
        """
        Orchestrates the calculation of design pressures per zone for the given C&C effective area (roof C&C).

        Accesses GCPi for pressure calculation (get_gcpi).
        Calculates velocity pressure and extracts alpha from power law (qz_calc).
        Obtains GCp for each Zone (1, 2, 3) and sign (+, -) (get_roof_gcp).
        Calculates pressure for each zone (calc_pressure).

        Parameters:
            wind_speed: The wind speed the building is subject to
            exposure: A string providing the ASCE 7 Exposure Category
            edition: A string naming the edition of ASCE 7 wind loading provision for the building
            h_bldg: The building height
            pitch: The roof pitch needed to determine the appropriate use case for the building
            area_eff: Effective wind area for a component type [ft^2]
            cat: A string with the ASCE 7 Importance Factor Category
            hpr: A Boolean indicating if the location is in a hurricane-prone region (True/False, Yes/No)
            h_ocean: A Boolean identifying if building is at hurricane oceanline (ASCE 7-88 and 7-93)
            encl_class: A string with ASCE 7 Enclosure Class ('Enclosed', 'Partial', 'Open')

        Returns:
            rps: (List) Zone pressures for each zone number and sign (Zone1+, Zone2+, Zone3+, Zone1-, Zone2-, Zone3-).
        """
        # Determine GCpis for pressure calculation:
        gcpi = PressureCalc.get_gcpi(self, edition, encl_class)
        # Determine components and cladding pressure for building roof components:
        is_cc = True
        # All components and cladding calculations require qh:
        qh, alpha = PressureCalc.qz_calc(self, h_bldg, wind_speed, exposure, edition, is_cc, cat, hpr, h_ocean, tpu_flag)
        # Get GCps and calculate the pressure for each zone:
        if h_bldg > 60:
            if edition == 'ASCE 7-88' or edition == 'ASCE 7-93':
                rpos = [False, False, False, False]
                rzone = [1, 2, 3, 4]
            else:
                rpos = [False, False, False]
                rzone = [1, 2, 3]
        else:
            rpos = [True, True, True, False, False, False]
            rzone = [1, 2, 3, 1, 2, 3]
        rps = list()
        for ind in range(0, len(rpos)):
            # Find the GCp
            gcp = PressureCalc.get_roof_gcp(self, h_bldg, pitch, area_eff, rpos[ind], rzone[ind], edition)
            # Calculate pressure at the zone:
            p = PressureCalc.calc_pressure(self, h_bldg, edition, is_cc, qh, gcp, gcpi, tpu_flag)
            rps.append(p)
        return rps

    def rmwfrs_pressure(self, wind_speed, exposure, edition, h_bldg, direction, length, ratio, pitch, cat, hpr, h_ocean, encl_class, tpu_flag):
        """
        Orchestrates the calculation of design pressures per zone for roof uplift pressures.

        Accesses GCPi for pressure calculation (get_gcpi).
        Calculates velocity pressure and extracts alpha from power law (qz_calc).
        Determine the gust factor (get_g).
        Obtains (-) Cp for each Roof Zone (get_cp_rmwfrs). Note: currently set for 'parallel' use case
        Calculates pressure for each zone (calc_pressure).

        Parameters:
            wind_speed: The wind speed the building is subject to
            exposure: A string providing the ASCE 7 Exposure Category
            edition: A string naming the edition of ASCE 7 wind loading provision for the building
            h_bldg: The building height
            length: The building length needed to calculate the h/L ratio to access roof MWFRS pressure coefficients
            ratio: h/L ratio
            pitch: The roof pitch needed to determine the appropriate use case for the building
            cat: A string with the ASCE 7 Importance Factor Category
            hpr: A Boolean indicating if the location is in a hurricane-prone region (True/False, Yes/No)
            h_ocean: A Boolean identifying if building is at hurricane oceanline (ASCE 7-88 and 7-93)
            encl_class: A string with ASCE 7 Enclosure Class ('Enclosed', 'Partial', 'Open')

        Returns:
            rmps: (List) Uplift pressures for each zone.
        """
        # Determine GCpis for pressure calculation:
        gcpi = PressureCalc.get_gcpi(self, edition, encl_class)
        # Determine the velocity pressure:
        is_cc = False
        # Roof uplift pressures require qh:
        qh, alpha = PressureCalc.qz_calc(self, h_bldg, wind_speed, exposure, edition, is_cc, cat, hpr, h_ocean, tpu_flag)
        print(qh)
        # Get the gust effect or gust response factor:
        g = PressureCalc.get_g(self, edition, exposure, is_cc, alpha, h_bldg)
        print(g)
        print(gcpi)
        # Set up placeholders for Cp values:
        rmps = list()
        # Find the Cps:
        cp = PressureCalc.get_cp_rmwfrs(self, h_bldg, direction, ratio, pitch, length, edition)
        print(cp[0])
        if len(cp) == 1: # In cases when there is only one zone
            gcp = g*cp[0]
            # Calculate uplift pressure at the zone:
            p = PressureCalc.calc_pressure(self, h_bldg, edition, is_cc, qh, gcp, gcpi, tpu_flag)
            # Add pressure to list:
            rmps.append(p)
        else:
            for row in cp:
                gcp = g * row[0]  # Take the first Cp value for uplift calculations
                # Calculate uplift pressure at the zone:
                p = PressureCalc.calc_pressure(self, h_bldg, edition, is_cc, qh, gcp, gcpi, tpu_flag)
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

    def get_tpu_pressure(self, v_basic, cp, exposure, z, unit):
        if unit == 'mph':
            v_basic = v_basic/2.237  # convert to [m]/[s^2]
            z = z/3.281  # convert height from [ft] to [m]
        else:
            pass
        # TPU pressure coefficients are referenced at 10 m height in Exposure B:
        if exposure == 'B':
            # Calculate the equivalent wind speed for this terrain using the wind speed in Exposure C:
            vg = v_basic / ((10/274.32)**(1/9.5))
            zg_b = 365.76
            alpha_b = 7
            v = vg*(z/zg_b)**(1/alpha_b)  # Wind speed Exposure B, at height z
        else:
            print('only suburban terrain supported at this time')
        # Calculate the pressure at the tap location: p = 1/2*rho*Cp*V^2
        rho = 1.225  # [kg]/[m^3]
        avg_factor = (1/1.52)**2  # Factor to switch between mean hourly and 3-s wind speeds
        p = 0.5 * rho * cp*avg_factor * (v) ** 2  # [N]/[m^2]
        if unit == 'mph':
            # Covert pressure to lb/ft^2
            p = p * 0.020885
        else:
            pass
        return p

    def get_gcpi(self, edition, encl_class):
        """
        Determines the GCpi for the building.

        Parameters:
            edition: A string naming the edition of ASCE 7 wind loading provision for the building
            encl_class: A string with ASCE 7 Enclosure Class ('Enclosed', 'Partial', 'Open')

        Returns:
            gcpi: GCpi value for the enclosure category
        """
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

    def get_g(self, edition, exposure, is_cc, alpha, z):
        """
        Determines the Gust effect or gust response factor for the building.

        Parameters:
            edition: A string naming the edition of ASCE 7 wind loading provision for the building
            exposure: A string providing the ASCE 7 Exposure Category
            is_cc: A Boolean indicating if the assessment is for C&C (True) or MWFRS (False)
            alpha: Used in power law and depends on Exposure Category
            z: (For ASCE 7-93 and earlier) height at which g is calculated

        Returns:
            g: Gust effect or gust response factor for the building.
        """
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
            # Adjust the height if necessary:
            if z < 15:  # [ft]
                z = 15
            else:
                pass
            # Calculate the gust reponse factor
            if is_cc:  # Gz and Gh are calculated the exact same way, except that Gz uses the mean roof height
                tz = (2.35 * (d0) ** (1 / 2)) / ((z /30) ** (1 / alpha)) # Gz calc
                g = 0.65 + 3.65 * tz
            else:
                tz = (2.35 * (d0) ** (1 / 2)) / ((z /30) ** (1 / alpha)) # Gh calc
                g = 0.65 + 3.65 * tz
        else:  # All other editions of ASCE 7
            g = 0.85
        return g

    # Laying out the code needed to replicate the pressures from ASCE 7
    def calc_pressure(self, z, edition, is_cc, q, gcp, gcpi, tpu_flag):
        """
        Determines the Gust effect or gust response factor for the building.

        Parameters:
            z: The height the pressure needs to be calculated at.
            edition: A string naming the edition of ASCE 7 wind loading provision for the building
            is_cc: A Boolean indicating if the assessment is for C&C (True) or MWFRS (False)
            q: Velocity pressure at height z
            gcp: Either C&C coefficient or product or gust effect/response factor and Cp
            gcpi: Interior pressure coefficient

        Returns:
            p: The design pressure.
        """
        # Pressure calc: will need to code in a procedure to determine both +/- cases for GCpi
        if is_cc:
            if tpu_flag:
                p = q * gcp
            else:
                # Calculate pressure for the controlling case:
                if gcp > 0:
                    p = q * (gcp + gcpi)
                elif gcp < 0:
                    p = q * (gcp - gcpi)
            # Exception for ASCE 7-95: For buildings in Exposure B, calculated pressure shall be multiplied by 0.85
            if edition == 'ASCE 7-95':
                p = 0.85 * p
            else:
                pass
        else:
            if tpu_flag:
                p = q * gcp
            else:
                p = q * gcp - q * gcpi  # q = qz for roof (at mean roof height)

        return p

    def qz_calc(self, z, wind_speed, exposure, edition, is_cc, cat, hpr, h_ocean, tpu_flag):
        """
        Orchestrates the velocity pressure calculation.

        Accesses Kz value for the given z (get_kz).
        Determines the building's Importance Factor (get_i).
        Calculates the velocity pressure, qz.

        Parameters:
            z: Height qz must be calculated at [ft]
            wind_speed: The wind speed the building is subject to
            exposure: A string providing the ASCE 7 Exposure Category
            edition: A string naming the edition of ASCE 7 wind loading provision for the building
            is_cc: A Boolean indicating if the assessment is for C&C (True) or MWFRS (False)g
            cat: A string with the ASCE 7 Importance Factor Category
            hpr: A Boolean indicating if the location is in a hurricane-prone region (True/False, Yes/No)
            h_ocean: A Boolean identifying if building is at hurricane oceanline (ASCE 7-88 and 7-93)

        Returns:
            qz: Velocity pressure at height z
            alpha: Used in power law and depends on Exposure Category
        """
        # Every edition of ASCE 7 has a velocity exposure coefficient:
        kz, alpha = PressureCalc.get_kz(self, z, exposure, edition, is_cc)
        # Calculate the velocity pressure:
        if edition == 'ASCE 7-93' or edition == 'ASCE 7-88':
            imp = PressureCalc.get_i(self, wind_speed, hpr, h_ocean, cat, edition)
            qz = 0.00256 * kz * (imp * wind_speed) ** 2
        elif edition == 'ASCE 7-95':
            kzt = 1.0
            imp = PressureCalc.get_i(self, wind_speed, hpr, h_ocean, cat, edition)
            qz = 0.00256 * kz * kzt * imp * wind_speed ** 2
        elif edition == 'ASCE 7-98' or edition == 'ASCE 7-02' or edition == 'ASCE 7-05':
            kzt = 1.0
            if tpu_flag:
                kd = 1.0
            else:
                kd = 0.85
            imp = PressureCalc.get_i(self, wind_speed, hpr, h_ocean, cat, edition)
            qz = 0.00256 * kz * kzt * kd * imp * wind_speed ** 2
        elif edition == 'ASCE 7-10' or edition == 'ASCE 7-16':
            kzt = 1.0
            if tpu_flag:
                kd = 1.0
            else:
                kd = 0.85
            qz = 0.00256 * kz * kzt * kd * wind_speed ** 2
        return qz, alpha

    def get_kz(self, z, exposure, edition, is_cc):
        """
        Calculates the velocity pressure exposure coefficient.

        Parameters:
            z: The height the coefficient needs to be calculated at.
            exposure: A string providing the ASCE 7 Exposure Category
            edition: A string naming the edition of ASCE 7 wind loading provision for the building
            is_cc: A Boolean indicating if the assessment is for C&C (True) or MWFRS (False)g

        Returns:
            kz: Velocity pressure at height z
            alpha: Used in power law and depends on Exposure Category
        """
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
            if exposure == 'B' and (edition == 'ASCE 7-98' or edition == 'ASCE 7-02' or edition == 'ASCE 7-05' or edition == 'ASCE 7-10' or edition == 'ASCE 7-16'):
                if z < 30:
                    z = 30  # [ft]
                else:
                    pass
        else:
            pass
        # Calculate the velocity pressure coefficient:
        if z <= 15:  # [ft]
            kz = factor * (15 / zg) ** (2 / alpha)
        elif 15 < z < zg:
            kz = factor * (z / zg) ** (2 / alpha)
        return kz, alpha

    def get_i(self, wind_speed, hpr, h_ocean, cat, edition):
        """
        Determines the building's Importance Factor.

        Parameters:
            wind_speed: The wind speed the building is subject to
            hpr: A Boolean indicating if the location is in a hurricane-prone region (True/False, Yes/No)
            h_ocean: A Boolean identifying if building is at hurricane oceanline (ASCE 7-88 and 7-93)
            cat: A string with the ASCE 7 Importance Factor Category
            edition: A string naming the edition of ASCE 7 wind loading provision for the building

        Returns:
            imp: Building Importance Factor.
        """
        # Importance factor for ASCE 7-05 and older:
        if edition == 'ASCE 7-88' or edition == 'ASCE 7-93':
            if h_ocean:  # if building is at hurricane oceanline (ASCE 7-88 and 7-93)
                categories = np.array([1.05, 1.11, 1.11, 1.00])
                imp = categories[cat - 1]
            else:
                categories = np.array([1.00, 1.07, 1.07, 0.95])
                imp = categories[cat - 1]
        else:
            if hpr and wind_speed > 100:  # wind speed in [mph] - this rule is for ASCE 7-98 - 7-05
                categories = np.array([0.77, 1.00, 1.15, 1.15])
                imp = categories[cat - 1]
            else:
                categories = np.array([0.87, 1.00, 1.15, 1.15])
                imp = categories[cat - 1]
        return imp

    def get_cp_rmwfrs(self, h_bldg, direction, ratio, pitch, length, edition):
        """
        Determines all possible Cps for a roof uplift pressures use case.

        Accesses GCPi for pressure calculation (get_gcpi).
        Calculates velocity pressure and extracts alpha from power law (qz_calc).
        Determine the gust factor (get_g).
        Obtains (-) Cp for each Roof Zone (get_cp_rmwfrs). Note: currently set for 'parallel' use case
        Calculates pressure for each zone (calc_pressure).

        Parameters:
            h_bldg: The building height
            direction: A string indicating the wind direction ('parallel' or 'normal')
            ratio: h/L ratio
            pitch: The roof pitch needed to determine the appropriate use case for the building
            length: The building length needed to calculate the h/L ratio to access roof MWFRS pressure coefficients
            edition: A string naming the edition of ASCE 7 wind loading provision for the building

        Returns:
            Cps: (List) Uplift pressure coefficients.
        """
        # Identify roof MWFRS zones and pressure coefficients
        if edition == 'ASCE 7-88' or edition == 'ASCE 7-93':
            if direction == 'parallel':
                if ratio <= 2.5:
                    Cps = [-0.7]
                elif ratio > 2.5:
                    Cps = [-0.8]
            else:
                pass
        else:
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
                    if length <= 0.5*h_bldg:
                        zones = 1
                    elif length > 0.5*h_bldg:
                        zones = 2
                    # Get back all Cps for the identified zones:
                    Cps = Cp_full[0:zones]
                else:
                    # Use cases between 0.5 and 1.0
                    # Determine how many zones are present:
                    if length <= 0.5*h_bldg:
                        zones = 1
                    elif 0.5*h_bldg < length <= h_bldg:
                        zones = 2
                    elif h_bldg < length <= 2*h_bldg:
                        zones = 3
                    elif length > 2*h_bldg:
                        zones = 4
                    # Now create an array of interpolated Cp values:
                    cp_full05 = np.array([[-0.9, -0.18], [-0.9, -0.18], [-0.5, -0.18], [-0.3, -0.18]])
                    cp_full1 = np.array([[-1.3, -0.18], [-0.7, -0.18]])
                    xp = [0.5, 1.0]
                    yp2 = -0.18
                    Cps = []
                    for coeff in range(0, zones):
                        if coeff == 0:
                            yp = [cp_full05[coeff][0], cp_full1[0][0]]
                        else:
                            yp = [cp_full05[coeff][0], cp_full1[1][0]]
                        cp = np.interp(ratio, xp, yp)
                    Cps.append([cp, yp2])
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

    def get_roof_gcp(self, h_bldg, pitch, area_eff, pos, zone, edition):
        """
        Determines the GCp for Roof C&C.

        Parameters:
            pitch: The roof pitch needed to determine the appropriate use case for the building
            area_eff: Effective wind area for a component type
            pos: A Boolean indicating if the coefficients are for positive (True) or negative (False) pressures
            zone: The roof C&C zone number
            edition: A string naming the edition of ASCE 7 wind loading provision for the building

        Returns:
            gcp: The GCp for the C&C's effective area.
        """
        # Assume effective wind area is in units of ft^2
        if pitch < 10:
            if edition == 'ASCE 7-93' or edition == 'ASCE 7-88':
                if h_bldg < 60:  # [ft]
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
                    # Zones 1, 2, and 3
                    if pos:
                        gcp = 0.2
                    else:
                        # Negative external pressure coefficients:
                        if zone == 1:
                            if area_eff <= 10:  # [ft^2]
                                gcp = -2.0
                            elif 10 < area_eff <= 100:
                                m = (-1.0 - -2.0) / (100 - 10)
                                gcp = m * (area_eff - 10) - 2.0
                            elif area_eff > 100:
                                gcp = -1.0
                        elif zone == 2:
                            if area_eff <= 10:
                                gcp = -2.5
                            elif 10 < area_eff <= 100:
                                m = (-2.0 - -2.5) / (100 - 10)
                                gcp = m * (area_eff - 10) - 2.5
                            elif area_eff > 100:
                                gcp = -2.0
                        elif zone == 3:
                            if area_eff <= 10:  # [ft^2]
                                gcp = -4.0
                            elif 10 < area_eff <= 100:
                                m = (-2.0 - -4.0) / (100 - 10)
                                gcp = m * (area_eff - 10) - 4.0
                            elif area_eff > 100:
                                gcp = -2.0
                        elif zone == 4:
                            if area_eff <= 10:  # [ft^2]
                                gcp = -5.0
                            elif 10 < area_eff <= 100:
                                m = (-2.0 - -5.0) / (100 - 10)
                                gcp = m * (area_eff - 10) - 5.0
                            elif area_eff > 100:
                                gcp = -2.0
            else:
                if h_bldg < 60:  # [ft]
                    if pitch < 7:
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
                else:
                    if pitch < 10:
                        # Positive external pressure coefficients:
                        # Zones 1, 2, and 3
                        if pos:
                            gcp = 0.2
                        else:
                            # Negative external pressure coefficients:
                            if zone == 1:
                                if area_eff <= 10:  # [ft^2]
                                    gcp = -1.4
                                elif 10 < area_eff <= 500:
                                    m = (-0.9 - -1.4) / (500 - 10)
                                    gcp = m * (area_eff - 10) - 1.4
                                elif area_eff > 500:
                                    gcp = -0.9
                            elif zone == 2:
                                if area_eff <= 10:
                                    gcp = -2.3
                                elif 10 < area_eff <= 500:
                                    m = (-1.6 - -2.3) / (500 - 10)
                                    gcp = m * (area_eff - 10) - 2.3
                                elif area_eff > 500:
                                    gcp = -1.6
                            elif zone == 3:
                                if area_eff <= 10:  # [ft^2]
                                    gcp = -3.2
                                elif 10 < area_eff <= 500:
                                    m = (-2.3 - -3.2) / (500 - 10)
                                    gcp = m * (area_eff - 10) - 3.2
                                elif area_eff > 500:
                                    gcp = -2.3

        else:
            print('Roof pitch GCp values currently not supported')

        return gcp

    def get_wcc_gcp(self, area_eff, pos, zone, edition):
        """
        Determines the GCp for Wall (facade) C&C.

        Parameters:
            area_eff: Effective wind area for a component type
            pos: A Boolean indicating if the coefficients are for positive (True) or negative (False) pressures
            zone: The wall C&C zone number
            edition: A string naming the edition of ASCE 7 wind loading provision for the building

        Returns:
            gcp: The GCp for the C&C's effective area.
        """
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

    def run_sim_rmwfrs(self, ref_exposure, ref_hbldg, ref_pitch, ref_cat, wind_speed, edition, use_case, hpr, h_ocean, encl_class, plot_flag, save_flag):
        """
        Orchestrates generation of similitude parameters for the specified reference building, use_case, code edition.

        Creates Zone tags and geometries needed for a given use case.
        Calculates the reference pressure for the reference building.
        Calculate roof uplift pressures at various wind speeds.
        Determines similitude parameters for variations in wind speed.
        Calculates roof uplift pressures at various wind speeds, building heights.
        Determines similitude parameters for variations in height.
        Calculate roof uplift pressures for various wind speeds, Exposure Categories.
        Determines similitude parameters for variations in Exposure Category.
        (Option) Generates plots of zone pressures for each variation consideration.
        (Option) Saves reference pressures and similitude parameters in .csv files

        Parameters:
            ref_exposure: A string providing the ASCE 7 Exposure Category for the reference building
            ref_hbldg: The height of a given reference building
            ref_pitch: The roof pitch for a given reference building
            ref_cat: The Importance factor for a given reference building
            wind_speed: The wind speed the building is subject to
            edition: A string naming the edition of ASCE 7 wind loading provision for the building
            use_case: A number indicating the roof MWFRS use case (user-provided)
            hpr: A Boolean indicating if the location is in a hurricane-prone region (True/False, Yes/No)
            h_ocean: A Boolean identifying if building is at hurricane oceanline (ASCE 7-88 and 7-93)
            encl_class: A string with ASCE 7 Enclosure Class ('Enclosed', 'Partial', 'Open')
            plot_flag: A Boolean to activate/deactivate plots (True/False)
            save_flag: A Boolean to indicate if files for the use case need to be generated (True/False)
        """
        # Figure out what Use Case, populate column names for DataFrame and set up h/L, wind direction, etc.:
        if use_case == 1: # theta < 10 or wind direction || to ridge AND h/L <= 0.5
            case_col = ['Zone 1', 'Zone 2', 'Zone 3', 'Zone 4']
            length = 3 * ref_hbldg  # Choose a length that gives ratio to return pressures for all zones
            ratio = ref_hbldg / length
        elif use_case == 2:  # theta < 10 or wind direction || to ridge AND h/L >= 1.0
            case_col = ['Zone 1', 'Zone 2']
            length = ref_hbldg  # Choose a length that gives ratio to return pressures for all zones
            ratio = ref_hbldg / length
        elif use_case == 3:  # (ASCE 7-88/-93) wind direction || to ridge AND h/L <= 2.5
            case_col = ['Zone 1']
            length = ref_hbldg  # Choose a length that gives ratio <= 2.5
            ratio = ref_hbldg / length
        elif use_case == 4:  # (ASCE 7-88/-93) wind direction || to ridge AND h/L <= 2.5
            case_col = ['Zone 1']
            length = ref_hbldg/3  # Choose a length that gives ratio > 2.5
            ratio = ref_hbldg / length
        else:
            print('use case not supported')
        # VARIATION 1: Reference building at various wind speeds:
        # Create an empty list that will hold DataFrames for each code edition:
        ed_list = list()
        # Create an empty DataFrame to hold reference pressures:
        df_pref = pd.DataFrame()
        for ed in edition:
            # Create a new DataFrame for each edition:
            df = pd.DataFrame(columns=case_col)
            for speed in wind_speed:
                rmps = self.rmwfrs_pressure(speed, ref_exposure, ed, ref_hbldg, length, ratio, ref_pitch, ref_cat, hpr, h_ocean, encl_class)
                # Pair zone names with zone pressures:
                zone_dict = {df.columns[i]: rmps[i] for i in range(len(rmps))}
                # Add values to Dataframe:
                df = df.append(zone_dict, ignore_index=True)
            # Add DataFrame to list:
            ed_list.append(df)
            # Extract reference pressures:
            df_pref = df_pref.append(df.iloc[0], ignore_index=True) # First row corresponds to pressure at min(wind_speed)
            # Uncomment to plot the zone pressures for this code edition:
            if plot_flag:
                fig, ax = plt.subplots()
                for j in range(0, len(rmps)):
                    zone_curve = ax.plot(df[case_col[j]], wind_speed, label=case_col[j])
                plt.title('Roof uplift pressures (MWFRS) for All Zones vs. Wind speed for ' + str(ref_hbldg) + ' ft ' + ed)
                plt.ylabel('Wind Speed [mph]')
                plt.xlabel('Pressure [psf]')
                plt.show()
            else:
                pass
            # Uncomment to show the percent change in pressure between zones and wind speeds:
            print('percent change between zones:', df.pct_change(axis=1))
            print('percent change between wind speeds:', df.pct_change(axis=0))
        # Add column for reference pressures DataFrame:
        df_pref['Edition'] = edition
        df_pref.set_index('Edition', inplace=True)
        # Save the DataFrame to a .csv file for future reference:
        if save_flag:
            df_pref.to_csv('Roof_MWFRS_ref' + str(use_case) + '.csv')  # holds the reference pressures
        else:
            pass
        # Determine similitude parameters, wind speed using pressure at reference wind speed:
        # Note: Variation in wind speed is the same across zones:
        df_Vfactor = pd.DataFrame()
        for dframe in ed_list:
            # Use Zone 1 pressures to calculate pressure differences due to change in wind speed:
            col = dframe[dframe.columns[0]]
            vfactor_list = list()
            for index in range(0, len(col)):
                if index == 0:  # First index corresponds to pressure when V = min(wind_speed)
                    factor = 0.0
                elif col[index] == col[0]:
                    factor = 0.0
                else:
                    factor = (col[index] - col[0]) / col[0]
                vfactor_list.append(factor)
            vfactor_dict = {wind_speed[i]: vfactor_list[i] for i in range(len(vfactor_list))}  # Pairs each key (wind speed) with its factor
            # Add to DataFrame:
            df_Vfactor = df_Vfactor.append(vfactor_dict, ignore_index=True)
        # Set the index to the corresponding code editions:
        # Add column:
        df_Vfactor['Edition'] = edition
        df_Vfactor.set_index('Edition', inplace=True)
        # Save the DataFrame to a .csv file for future reference:
        if save_flag:
            df_Vfactor.to_csv('Roof_MWFRS_v' + str(use_case)+'.csv')
        else:
            pass
        # VARIATION 2: Different building height, different wind speeds:
        # Create an empty list that will hold DataFrames for each code edition:
        edh_list = list()
        # Set up array of building heights:
        h_bldg = np.arange(ref_hbldg, 61, 1)
        # Goal here is to get the pressure difference between ref height and other heights for various wind speeds
        for ed in edition:
            # Set up a Dataframe to compare values:
            dfh = pd.DataFrame()
            if plot_flag:
                # Set up a matplotlib figure:
                fig3, ax3 = plt.subplots()
            else:
                pass
            for h in h_bldg:
                # Figure out Use Case, populate column names for DataFrame and set up h/L, wind direction, etc.:
                if use_case == 1:   # theta < 10 or wind direction || to ridge AND h/L <= 0.5
                    length = 3 * h
                    ratio = h / length
                elif use_case == 2:  # theta < 10 or wind direction || to ridge AND h/L >= 1.0
                    length = h  # Choose a length that gives ratio to return pressures for all zones
                    ratio = h / length
                elif use_case == 3:  # (ASCE 7-88/-93) wind direction || to ridge AND h/L <= 2.5
                    length = h  # Choose a length that gives ratio <= 2.5
                    ratio = h / length
                elif use_case == 4:  # (ASCE 7-88/-93) wind direction || to ridge AND h/L <= 2.5
                    length = h / 3  # Choose a length that gives ratio > 2.5
                    ratio = h / length
                else:
                    print('use case not supported')
                rmps_arr = np.array([])
                for speed in wind_speed:
                    rmps = self.rmwfrs_pressure(speed, ref_exposure, ed, h, length, ratio, ref_pitch, ref_cat, hpr, h_ocean, encl_class)
                    rmps_arr = np.append(rmps_arr, rmps[0])  # Zone 1 (variation across heights is same across zones)
                # Add values to DataFrame:
                col_name = str(h) + ' ft'
                dfh[col_name] = rmps_arr
                # Plot the results:
                if plot_flag:
                    ax3.plot(dfh[col_name], wind_speed, label = str(h)+ ' ft')
                else:
                    pass
            # Add DataFrame to list:
            edh_list.append(dfh)
            # Plot the results:
            if plot_flag:
                ax3.legend()
                plt.title('Roof uplift pressures (MWFRS) for Zone 1 vs. Wind speed for various heights')
                plt.ylabel('Wind Speed [mph]')
                plt.xlabel('Pressure [psf]')
                plt.ylim(90, max(wind_speed))
                plt.show()
            else:
                pass
            # Uncomment to show the percent change in pressure between heights:
            print('Percent change in pressure between heights:', ed, dfh.pct_change(axis=1))
        # Calculate the percent change in pressure (compared to reference building height):
        df_hfactor = pd.DataFrame()
        row = dfh.iloc[0]  # Only need one since variation with height is same for across wind speeds
        for index in range(0, len(row)):
            if index == 0:
                factor = 0.0
            elif row[index] == row[0]:
                factor = 0.0
            else:
                factor = (row[index] - row[0]) / row[0]
            hcol_name = dfh.columns[index]
            df_hfactor[hcol_name] = np.array([factor])
        # Uncomment to save the DataFrame to a .csv file for future reference:
        if save_flag:
            df_hfactor.to_csv('h.csv')
        else:
            pass
        # VARIATION 3: Different building height, different wind speeds, different exposures:
        exposures = ['B', 'C', 'D']
        # Set up an empty list to store the dataframe for each code edition:
        exp_list = list()
        for ed in edition:
            # Set up DataFrame to save pressure difference across exposure categories for various heights:
            df_Efactor = pd.DataFrame(columns=exposures)
            for h in h_bldg:
                dfE = pd.DataFrame()
                # Figure out what Use Case is being populated, populate column names for DataFrame and set up h/L, wind direction, etc.:
                if use_case == 1:   # theta < 10 or wind direction || to ridge AND h/L <= 0.5
                    length = 3 * h
                    ratio = h / length
                elif use_case == 2:  # theta < 10 or wind direction || to ridge AND h/L >= 1.0
                    length = h  # Choose a length that gives ratio to return pressures for all zones
                    ratio = h / length
                elif use_case == 3:  # (ASCE 7-88/-93) wind direction || to ridge AND h/L <= 2.5
                    length = h  # Choose a length that gives ratio <= 2.5
                    ratio = h / length
                elif use_case == 4:  # (ASCE 7-88/-93) wind direction || to ridge AND h/L <= 2.5
                    length = h / 3  # Choose a length that gives ratio > 2.5
                    ratio = h / length
                else:
                    print('use case not supported')
                if plot_flag:
                    fig4, ax4 = plt.subplots()
                else:
                    pass
                for exp in exposures:
                    rmps_arr = np.array([])
                    for speed in wind_speed:
                        rmps = self.rmwfrs_pressure(speed, exp, ed, h, length, ratio, ref_pitch, ref_cat, hpr, h_ocean, encl_class)
                        rmps_arr = np.append(rmps_arr, rmps[0])
                    # Add values to DataFrame:
                    dfE[exp] = rmps_arr
                    # Plot the results (Exposures B, C, D) for one height:
                    if plot_flag:
                        ax4.plot(dfE[exp], wind_speed, label=exp)
                    else:
                        pass
                # Plot the results:
                if plot_flag:
                    ax4.legend()
                    plt.title('Roof uplift pressures (MWFRS, Zone 1) and h = '+str(h)+ ' ft')
                    plt.ylabel('Wind Speed [mph]')
                    plt.xlabel('Pressure [psf]')
                    plt.ylim(90, max(wind_speed))
                    plt.show()
                else:
                    pass
                # Check the percent change between Exposure categories:
                print('percent change in pressure by Exposure Category by h:', h, exp)
                print(dfE.pct_change(axis=1))
                # Calculate the percent change from Exposure B:
                row = dfE.iloc[0]
                factor_list = list()
                for index in range(0, len(row)):
                    if index == 0:
                        factor = 0.0
                    elif row[index] == row[0]:
                        factor = 0.0
                    else:
                        factor = (row[index] - row[0]) / row[0]
                    factor_list.append(factor)
                # Create a quick dictionary:
                factor_dict = {exposures[m]: factor_list[m] for m in
                               range(len(factor_list))}  # Pairs each key (Exposure) with its corresponding factor
                df_Efactor = df_Efactor.append(factor_dict, ignore_index=True)
            # Set the index to the corresponding building heights:
            # Add column:
            df_Efactor['Height in ft'] = h_bldg
            df_Efactor.set_index('Height in ft', inplace=True)
            # Store the DataFrame of Exposure factors:
            exp_list.append(df_Efactor)
            # Save the DataFrame for this code edition to a .csv file for future reference:
            if save_flag:
                df_Efactor.to_csv('Roof_MWFRS_exp_' + ed[-2:]+'.csv')
            else:
                pass

    def run_sim_wcc(self, ref_exposure, ref_hbldg, ref_hstory, ref_pitch, ref_cat,  wind_speed, edition, ctype, parcel_flag, hpr, h_ocean, encl_class, plot_flag, save_flag):
        """
        Orchestrates generation of similitude parameters for the specified reference building, C&C type, code edition.

        Creates Zone tags and determines effective area of given ctype.
        Calculates the reference pressure for the reference building.
        Calculate C&C pressures at various wind speeds.
        Determines similitude parameters for variations in wind speed.
        Calculates C&C pressures at various wind speeds, building heights.
        Determines similitude parameters for variations in height.
        Calculate C&C pressures for various wind speeds, Exposure Categories.
        Determines similitude parameters for variations in Exposure Category.
        (Option) Generates plots of zone pressures for each variation consideration.
        (Option) Saves reference pressures and similitude parameters in .csv files

        Parameters:
            ref_exposure: A string providing the ASCE 7 Exposure Category for the reference building
            ref_hbldg: The height of a given reference building
            ref_hstory: The story height of the reference building
            ref_pitch: The roof pitch for a given reference building
            ref_cat: The Importance factor for a given reference building
            wind_speed: The wind speed the building is subject to
            edition: A string naming the edition of ASCE 7 wind loading provision for the building
            ctype: A string indicating the C&C type.
            parcel_flag: A flag indicating if the effective area will need to be estimated vs. user-defined
            hpr: A Boolean indicating if the location is in a hurricane-prone region (True/False, Yes/No)
            h_ocean: A Boolean identifying if building is at hurricane oceanline (ASCE 7-88 and 7-93)
            encl_class: A string with ASCE 7 Enclosure Class ('Enclosed', 'Partial', 'Open')
            plot_flag: A Boolean to activate/deactivate plots (True/False)
            save_flag: A Boolean to indicate if files for the use case need to be generated (True/False)
        """
        # VARIATION 1: Reference building at various wind speeds:
        # Get the effective wind area for the C&C type:
        area_eff = self.get_warea(ctype, parcel_flag, ref_hstory)
        # Create an empty list to hold all DataFrames:
        edw_list = list()
        # Create an empty DataFrame to hold reference pressures:
        dfw_pref = pd.DataFrame()
        for ed in edition:
            # Create a new dataframe for each edition:
            df_wcc = pd.DataFrame(columns=['Zone 4+', 'Zone 5+', 'Zone 4-', 'Zone 5-'])
            # Set up plotting
            if plot_flag:
                fig, ax = plt.subplots()
            else:
                pass
            for speed in wind_speed:
                # Calculate the pressure across various wind speeds for each code edition:
                wps = self.wcc_pressure(speed, ref_exposure, ed, ref_hbldg, ref_pitch, area_eff, ref_cat, hpr, h_ocean, encl_class, tpu_flag=False)
                # Add values to Dataframe:
                df_wcc = df_wcc.append({'Zone 4+': wps[0], 'Zone 5+': wps[1], 'Zone 4-': wps[2], 'Zone 5-': wps[3]}, ignore_index=True)
            # Add DataFrame to list:
            edw_list.append(df_wcc)
            # Extract reference pressures:
            dfw_pref = dfw_pref.append(df_wcc.iloc[0], ignore_index=True)  # First row corresponds to pressures at min(wind_speed)
            # Plot Zone pressures for 1 case (Zones 4 and 5 (+) are equal):
            if plot_flag:
                ax.plot(df_wcc['Zone 4+'], wind_speed)
                plt.ylim(90, max(wind_speed))
                plt.ylabel('Wind Speed [mph]')
                plt.xlabel('Pressure [psf]')
                plt.title(ctype + 'C&C pressures (+), Zones 4 and 5 for h_story = 9.0 ft')
                plt.show()
            else:
                pass
            # Uncomment to show the difference in pressure between zones and wind speeds for the typical effective wind area
            print('percent change between zones:', ed, df_wcc.pct_change(axis=1))
            print('percent change in wind speed:', ed, df_wcc.pct_change(axis=0))
        # Add column for reference pressures DataFrame:
        dfw_pref['Edition'] = edition
        dfw_pref.set_index('Edition', inplace=True)
        # Save the DataFrame to a .csv file for future reference:
        dfw_pref.to_csv('Wall_CC_ref_' + ctype + '.csv')
        # Determine the appropriate multiplier by comparing to reference wind speed pressure:
        # Note: Variation in wind speed is the same across zones:
        df_Vfactor = pd.DataFrame()
        for dframe in edw_list:
            # Use Zone 4 pressures to calculate pressure differences due to change in wind speed:
            col = dframe[dframe.columns[0]]
            vfactor_list = list()
            for index in range(0, len(col)):
                if index == 0:  # First index corresponds to pressure when V = min(wind_speed)
                    factor = 0.0
                elif col[index] == col[0]:
                    factor = 0.0
                else:
                    factor = (col[index] - col[0]) / col[0]
                vfactor_list.append(factor)
            vfactor_dict = {wind_speed[i]: vfactor_list[i] for i in range(len(vfactor_list))}  # Pairs each key (wind speed) with its corresponding factor
            # Add to DataFrame:
            df_Vfactor = df_Vfactor.append(vfactor_dict, ignore_index=True)
        # Set the index to the corresponding code editions:
        # Add column:
        df_Vfactor['Edition'] = edition
        df_Vfactor.set_index('Edition', inplace=True)
        # Save the DataFrame to a .csv file for future reference:
        if save_flag:
            df_Vfactor.to_csv('Wall_CC_v_'+ ctype+ '.csv')
        else:
            pass
        # VARIATION 2: Reference Building Story height, multiple stories, different wind speeds:
        # Define an array of building heights:
        h_bldg = np.arange(ref_hbldg * 1, ref_hbldg * 7, ref_hbldg)  # [ft], multiply by seven for parcels
        if ref_hstory > 9:
            # Take only values less than or equal to 60 ft:
            check = h_bldg <= 60  # [ft]
            h_bldg = h_bldg[check]
        else:
            pass
        # Percent change in pressure between heights is same for all Zones
        # Two groups: ASCE 7-95 and older vs. ASCE 7-98 and older, here we are going to collect all for easy access/comparison
        dfw_hfactor = pd.DataFrame()
        for ed in edition:
            # Set up a dataframe to compare values:
            dfwh = pd.DataFrame()
            # Set up a matplotlib figure:
            if plot_flag:
                fig3, ax3 = plt.subplots()
            else:
                pass
            for h in h_bldg:
                wps_arr = np.array([])
                for speed in wind_speed:
                    # Calculate the pressure across various wind speeds for each code edition:
                    wps = self.wcc_pressure(speed, ref_exposure, ed, h, ref_pitch, area_eff, ref_cat, hpr, h_ocean, encl_class)
                    wps_arr = np.append(wps_arr, wps[0])  # Zone 4+ since variation across heights is the same for all zones
                # Add values to DataFrame:
                col_name = str(h) + ' ft'
                dfwh[col_name] = wps_arr
                # Plot the results:
                if plot_flag:
                    ax3.plot(dfwh[col_name], wind_speed, label = str(h)+ ' ft')
                else:
                    pass
            # Plot the results:
            if plot_flag:
                ax3.legend()
                plt.title('Mullion Pressures (C&C) for Zone 4 (+) vs. Wind speed for various building heights')
                plt.ylabel('Wind Speed [mph]')
                plt.xlabel('Pressure [psf]')
                plt.ylim(90, max(wind_speed))
                plt.show()
            else:
                pass
            # Uncomment to show the percent change in pressure as height varies:
            print('Percent change in pressure between heights:', ed, dfwh.pct_change(axis=1))
            # Determine the percent change in pressure (compared to reference height) for each code edition:
            row = dfwh.iloc[0]  # Get first row of each DataFrame to find variation with height (same for all wind speeds)
            factor_list = list()
            for index in range(0, len(row)):
                if index == 0:
                    factor = 0.0
                elif row[index] == row[0]:
                    factor = 0.0
                else:
                    factor = (row[index] - row[0]) / row[0]
                factor_list.append(factor)
            # Create a quick dictionary:
            factor_dict = {dfwh.columns[i]: factor_list[i] for i in range(len(factor_list))}
            dfw_hfactor = dfw_hfactor.append(factor_dict, ignore_index=True)
        # Set the index to the corresponding code editions:
        # Add column:
        dfw_hfactor['Edition'] = edition
        dfw_hfactor.set_index('Edition', inplace=True)
        # Save the DataFrame to a .csv file for future reference:
        if save_flag:
            dfw_hfactor.to_csv('Wall_CC_h_' + ctype + '.csv')
        else:
            pass
        # Variation 3: Different building heights (same h_story), different wind speeds, different exposures:
        exposures = ['B', 'C', 'D']
        # Set up an empty list to store the Dataframes:
        expw_list = list()
        for ed in edition:
            # Set up DataFrame to save pressure difference across exposure categories for various heights:
            dfw_Efactor = pd.DataFrame(columns=exposures)
            for h in h_bldg:
                dfwE = pd.DataFrame()
                if plot_flag:
                    fig4, ax4 = plt.subplots()
                else:
                    pass
                for exp in exposures:
                    wps_arr = np.array([])
                    for speed in wind_speed:
                        wps = self.wcc_pressure(speed, exp, ed, h, ref_pitch, area_eff, ref_cat, hpr, h_ocean, encl_class)
                        wps_arr = np.append(wps_arr, wps[1])
                    # Add values to DataFrame:
                    dfwE[exp] = wps_arr
                    # Plot the results (Exposures B, C, D for one height:
                    if plot_flag:
                        ax4.plot(dfwE[exp], wind_speed, label=exp)
                    else:
                        pass
                # Plot the results:
                if plot_flag:
                    ax4.legend()
                    plt.title(ctype + 'pressures (C&C, Zone 4+) and h = '+str(h)+ ' ft')
                    plt.ylabel('Wind Speed [mph]')
                    plt.xlabel('Pressure [psf]')
                    plt.ylim(90, max(wind_speed))
                    plt.show()
                else:
                    pass
                # Check the percent change between Exposure categories:
                print('percent change in pressure by Exposure Category by h:', h, exp)
                print(dfwE.pct_change(axis=1))
                # Calculate the percent change from Exposure B:
                row = dfwE.iloc[0]
                factor_list = list()
                for index in range(0, len(row)):
                    if index == 0:
                        factor = 0.0
                    elif row[index] == row[0]:
                        factor = 0.0
                    else:
                        factor = (row[index] - row[0]) / row[0]
                    factor_list.append(factor)
                dfw_Efactor = dfw_Efactor.append({'B': factor_list[0], 'C': factor_list[1], 'D': factor_list[2]}, ignore_index=True)
            # Set the index to the corresponding building heights:
            # Add column:
            dfw_Efactor['Height in ft'] = h_bldg
            dfw_Efactor.set_index('Height in ft', inplace=True)
            # Store the DataFrame of Exposure factors:
            expw_list.append(dfw_Efactor)
            # Save the DataFrame for this code edition to a .csv file for future reference:
            if save_flag:
                dfw_Efactor.to_csv('Wall_CC_exp_' + ctype + '_' + str(ref_hstory) + 'ft_'+ ed[-2:]+'.csv')
            else:
                pass

    def compare_area_eff(self, ctype, area_eff, edition, exposure, wind_speed, h_bldg, pitch, cat, hpr, h_ocean, encl_class):
        # Quick plot comparisons for pressures between effective areas for a ctype (for Parcel-Informed Models)
        pressures = PressureCalc()
        # Reference Building with range of effective wind areas using typical practice:
        df_wcc = pd.DataFrame()
        # Set up array of effective areas:
        #area_eff = np.array([27, 45, 54, 90])  # [ft^2]
        count = 0
        fig, ax = plt.subplots()
        for area in area_eff:
            wall_pressures = np.empty((0, 4))
            for speed in wind_speed:
                wps = pressures.wcc_pressure(speed, exposure, edition, h_bldg, pitch, area, cat, hpr, h_ocean, encl_class)
                # Add to our empty array:
                wall_pressures = np.append(wall_pressures, np.array([wps]), axis=0)
            count = count + 1
            ax.plot(wall_pressures[:, 0], wind_speed, label=str(area) + ' sq ft')
            # Append column of pressures for various wind speeds for this height:
            col_name = str(area)
            df_wcc[col_name] = wall_pressures[:, 0]
        print('percent change in effective area:')
        print(df_wcc.pct_change(axis=1))
        ax.legend()
        plt.ylim(90, max(wind_speed))
        plt.title('Mullion C&C bounds (+), Zones 4 and 5 for h = ' + str(h_bldg) + ' [ft]')
        plt.ylabel('Wind Speed [mph]')
        plt.xlabel('Pressure [psf]')
        plt.show()

    def run_sim_rcc(self, ref_exposure, ref_hbldg, ref_hstory, ref_pitch, ref_cat,  wind_speed, edition, ctype, parcel_flag, hpr, h_ocean, encl_class, plot_flag, save_flag):
        """
        Orchestrates generation of similitude parameters for the specified reference building, C&C type, code edition.

        Creates Zone tags and determines effective area of given ctype.
        Calculates the reference pressure for the reference building.
        Calculate C&C pressures at various wind speeds.
        Determines similitude parameters for variations in wind speed.
        Calculates C&C pressures at various wind speeds, building heights.
        Determines similitude parameters for variations in height.
        Calculate C&C pressures for various wind speeds, Exposure Categories.
        Determines similitude parameters for variations in Exposure Category.
        (Option) Generates plots of zone pressures for each variation consideration.
        (Option) Saves reference pressures and similitude parameters in .csv files

        Parameters:
            ref_exposure: A string providing the ASCE 7 Exposure Category for the reference building
            ref_hbldg: The height of a given reference building
            ref_hstory: The story height of the reference building
            ref_pitch: The roof pitch for a given reference building
            ref_cat: The Importance factor for a given reference building
            wind_speed: The wind speed the building is subject to
            edition: A string naming the edition of ASCE 7 wind loading provision for the building
            ctype: A string indicating the C&C type.
            parcel_flag: A flag indicating if the effective area will need to be estimated vs. user-defined
            hpr: A Boolean indicating if the location is in a hurricane-prone region (True/False, Yes/No)
            h_ocean: A Boolean identifying if building is at hurricane oceanline (ASCE 7-88 and 7-93)
            encl_class: A string with ASCE 7 Enclosure Class ('Enclosed', 'Partial', 'Open')
            plot_flag: A Boolean to activate/deactivate plots (True/False)
            save_flag: A Boolean to indicate if files for the use case need to be generated (True/False)
        """
        # VARIATION 1: Reference building at various wind speeds:
        # Get the effective wind area for the C&C type:
        area_eff = self.get_rarea(ctype, parcel_flag, ref_hstory)
        # Create an empty list to hold all DataFrames:
        edr_list = list()
        # Create an empty DataFrame to hold reference pressures:
        dfr_pref = pd.DataFrame()
        for ed in edition:
            # Create a new dataframe for each edition:
            df_rcc = pd.DataFrame(columns=['Zone 1+', 'Zone 2+', 'Zone 3+', 'Zone 1-', 'Zone 2-', 'Zone 3-'])
            # Set up plotting
            if plot_flag:
                fig, ax = plt.subplots()
            else:
                pass
            emp_list = []
            for area in area_eff:
                # Create a new dataframe for each edition:
                df_rcc = pd.DataFrame(columns=['Zone 1+', 'Zone 2+', 'Zone 3+', 'Zone 1-', 'Zone 2-', 'Zone 3-'])
                for speed in wind_speed:
                    # Calculate the pressure across various wind speeds for each code edition:
                    rps = self.rcc_pressure(speed, ref_exposure, ed, ref_hbldg, ref_pitch, area, ref_cat, hpr, h_ocean, encl_class)
                    # Add values to Dataframe:
                    df_rcc = df_rcc.append({'Zone 1+': rps[0], 'Zone 2+': rps[1], 'Zone 3+': rps[2], 'Zone 1-': rps[3], 'Zone 2-': rps[4], 'Zone 3-': rps[5]}, ignore_index=True)
                # Plot the pressures for the areas:
                if plot_flag:
                    ax.plot(df_rcc['Zone 3-'], wind_speed)
                else:
                    pass
                emp_list.append(df_rcc['Zone 2-'])
            if plot_flag:
                plt.ylim(90, max(wind_speed))
                plt.ylabel('Wind Speed [mph]')
                plt.xlabel('Pressure [psf]')
                plt.title('Metal Deck C&C pressures (+), Zone 1, 2, and 3 for h_story = 9.0 ft')
                plt.show()
            else:
                pass
            print((emp_list[0]-emp_list[1])/emp_list[0])
            # Add DataFrame to list:
            edr_list.append(df_rcc)
            # Extract reference pressures:
            dfr_pref = dfr_pref.append(df_rcc.iloc[0], ignore_index=True)  # First row corresponds to pressures at min(wind_speed)
            # Plot Zone pressures for 1 case:
            if plot_flag:
                ax.plot(df_rcc['Zone 1+'], wind_speed)
                plt.ylim(90, max(wind_speed))
                plt.ylabel('Wind Speed [mph]')
                plt.xlabel('Pressure [psf]')
                plt.title(ctype + 'C&C pressures (+), Zones 4 and 5 for h_story = 9.0 ft')
                plt.show()
            else:
                pass
            # Uncomment to show the difference in pressure between zones and wind speeds for the typical effective wind area
            print('percent change between zones:', ed, df_rcc.pct_change(axis=1))
            print('percent change in wind speed:', ed, df_rcc.pct_change(axis=0))
        # Add column for reference pressures DataFrame:
        dfr_pref['Edition'] = edition
        dfr_pref.set_index('Edition', inplace=True)
        # Save the DataFrame to a .csv file for future reference:
        if save_flag:
            dfr_pref.to_csv('Roof_CC_ref_' + ctype + '.csv')
        else:
            pass
        # Determine the appropriate multiplier by comparing to reference wind speed pressure:
        # Note: Variation in wind speed is the same across zones:
        df_Vfactor = pd.DataFrame()
        for dframe in edr_list:
            # Use Zone 1 pressures to calculate pressure differences due to change in wind speed:
            col = dframe[dframe.columns[0]]
            vfactor_list = list()
            for index in range(0, len(col)):
                if index == 0:  # First index corresponds to pressure when V = min(wind_speed)
                    factor = 0.0
                elif col[index] == col[0]:
                    factor = 0.0
                else:
                    factor = (col[index] - col[0]) / col[0]
                vfactor_list.append(factor)
            vfactor_dict = {wind_speed[i]: vfactor_list[i] for i in range(len(vfactor_list))}  # Pairs each key (wind speed) with its corresponding factor
            # Add to DataFrame:
            df_Vfactor = df_Vfactor.append(vfactor_dict, ignore_index=True)
        # Set the index to the corresponding code editions:
        # Add column:
        df_Vfactor['Edition'] = edition
        df_Vfactor.set_index('Edition', inplace=True)
        # Save the DataFrame to a .csv file for future reference:
        if save_flag:
            df_Vfactor.to_csv('Roof_CC_v_'+ ctype+ '.csv')
        else:
            pass
        # VARIATION 2: Reference Building Story height, multiple stories, different wind speeds:
        # Define an array of building heights:
        h_bldg = np.arange(ref_hbldg * 1, ref_hbldg * 7, ref_hbldg)  # [ft], multiply by seven for parcels
        if ref_hstory > 9:
            # Take only values less than or equal to 60 ft:
            check = h_bldg <= 60  # [ft]
            h_bldg = h_bldg[check]
        else:
            pass
        # Percent change in pressure between heights is same for all Zones
        # Two groups: ASCE 7-95 and older vs. ASCE 7-98 and older, here we are going to collect all for easy access/comparison
        dfr_hfactor = pd.DataFrame()
        for ed in edition:
            # Set up a dataframe to compare values:
            dfrh = pd.DataFrame()
            # Set up a matplotlib figure:
            if plot_flag:
                fig3, ax3 = plt.subplots()
            else:
                pass
            for h in h_bldg:
                rps_arr = np.array([])
                for speed in wind_speed:
                    # Calculate the pressure across various wind speeds for each code edition:
                    rps = self.rcc_pressure(speed, ref_exposure, ed, h, ref_pitch, area_eff, ref_cat, hpr, h_ocean, encl_class)
                    rps_arr = np.append(rps_arr, rps[0])  # Zone 4+ since variation across heights is the same for all zones
                # Add values to DataFrame:
                col_name = str(h) + ' ft'
                dfrh[col_name] = rps_arr
                # Plot the results:
                if plot_flag:
                    ax3.plot(dfwh[col_name], wind_speed, label = str(h)+ ' ft')
                else:
                    pass
            # Plot the results:
            if plot_flag:
                ax3.legend()
                plt.title('Mullion Pressures (C&C) for Zone 4 (+) vs. Wind speed for various building heights')
                plt.ylabel('Wind Speed [mph]')
                plt.xlabel('Pressure [psf]')
                plt.ylim(90, max(wind_speed))
                plt.show()
            else:
                pass
            # Uncomment to show the percent change in pressure as height varies:
            #print('Percent change in pressure between heights:', ed, dfwh.pct_change(axis=1))
            # Determine the percent change in pressure (compared to reference height) for each code edition:
            row = dfrh.iloc[0]  # Get first row of each DataFrame to find variation with height (same for all wind speeds)
            factor_list = list()
            for index in range(0, len(row)):
                if index == 0:
                    factor = 0.0
                elif row[index] == row[0]:
                    factor = 0.0
                else:
                    factor = (row[index] - row[0]) / row[0]
                factor_list.append(factor)
            # Create a quick dictionary:
            factor_dict = {dfrh.columns[i]: factor_list[i] for i in range(len(factor_list))}
            dfr_hfactor = dfr_hfactor.append(factor_dict, ignore_index=True)

        # Set the index to the corresponding code editions:
        # Add column:
        dfr_hfactor['Edition'] = edition
        dfr_hfactor.set_index('Edition', inplace=True)
        # Save the DataFrame to a .csv file for future reference:
        dfr_hfactor.to_csv('Roof_CC_h_' + ctype + '.csv')

        # Variation 3: Different building heights (same h_story), different wind speeds, different exposures:
        exposures = ['B', 'C', 'D']
        # Set up an empty list to store the dataframes:
        expr_list = list()
        for ed in edition:
            # Set up DataFrame to save pressure difference across exposure categories for various heights:
            dfr_Efactor = pd.DataFrame(columns=exposures)
            for h in h_bldg:
                dfrE = pd.DataFrame()
                # fig4, ax4 = plt.subplots()
                for exp in exposures:
                    rps_arr = np.array([])
                    for speed in wind_speed:
                        rps = self.rcc_pressure(speed, exp, ed, h, ref_pitch, area_eff, ref_cat, hpr, h_ocean, encl_class)
                        rps_arr = np.append(rps_arr, rps[1])
                    # Add values to DataFrame:
                    dfrE[exp] = rps_arr
                    # Plot the results (Exposures B, C, D for one height:
                    # ax4.plot(dfwE[exp], wind_speed, label=exp)
                # Plot the results:
                # ax4.legend()
                # plt.title('Mullion pressures (C&C, Zone 4+) and h = '+str(h)+ ' ft')
                # plt.ylabel('Wind Speed [mph]')
                # plt.xlabel('Pressure [psf]')
                # plt.ylim(90, max(wind_speed))
                # plt.show()
                # Check the percent change between Exposure categories:
                # print('percent change in pressure by Exposure Category by h:', h, exp)
                # print(dfwE.pct_change(axis=1))
                # Calculate the percent change from Exposure B:
                row = dfrE.iloc[0]
                factor_list = list()
                for index in range(0, len(row)):
                    if index == 0:
                        factor = 0.0
                    elif row[index] == row[0]:
                        factor = 0.0
                    else:
                        factor = (row[index] - row[0]) / row[0]
                    factor_list.append(factor)
                dfr_Efactor = dfr_Efactor.append({'B': factor_list[0], 'C': factor_list[1], 'D': factor_list[2]}, ignore_index=True)
            # Set the index to the corresponding building heights:
            # Add column:
            dfr_Efactor['Height in ft'] = h_bldg
            dfr_Efactor.set_index('Height in ft', inplace=True)
            # Store the DataFrame of Exposure factors:
            expr_list.append(dfr_Efactor)
            # Save the DataFrame for this code edition to a .csv file for future reference:
            dfr_Efactor.to_csv('Roof_CC_exp_' + ctype + '_' + str(ref_hstory) + 'ft_'+ ed[-2:]+'.csv')
        # Extra code to inform future considerations of variation in wind speed for C&C components:
        # Reference Building with range of effective wind areas using typical practice:
        #df_rcc = pd.DataFrame()
        # Set up array of effective areas:
        #area_eff = np.array([27, 45, 54, 90])  # [ft^2]
        # Set up empty numpy arrays to store wall and roof pressures:
        #roof_pressures = np.empty((0, 4))
        #count = 0
        #fig, ax = plt.subplots()
        #edition = 'ASCE 7-10'

        #for area in area_eff:
            #roof_pressures = np.empty((0, 4))
            #for speed in wind_speed:
                #rps = pressures.rcc_capacity(speed, ref_exposure, edition, ref_hbldg, area, cat)
                # Add to our empty array:
                #roof_pressures = np.append(roof_pressures, np.array([wps]), axis=0)
            #count = count + 1
            #line = ax.plot(roof_pressures[:, 0], wind_speed, label=str(area) + ' sq ft')
            # Append column of pressures for various wind speeds for this height:
            #col_name = str(area)
            #df_rcc[col_name] = roof_pressures[:, 0]
            # params = curve_fit(func, roof_pressures[:,3], wind_speed)
            # [a, b, c] = params[0]
            # fit_curve = ax.plot(roof_pressures[:, 3], func(roof_pressures[:,3], a, b, c), label=str(area))

        #print('percent change in effective area:')
        #print(df_rcc.pct_change(axis=1))
        #ax.legend()
        #plt.ylim(90, max(wind_speed))
        #plt.title('Roof C&C bounds (+), Zones 4 and 5 for h = ' + str(h_bldg) + ' [ft]')
        #plt.ylabel('Wind Speed [mph]')
        #plt.xlabel('Pressure [psf]')
        #plt.show()
    def get_ctype(self, component):
        # Determine the ctype for the component:
        if isinstance(component, Wall):
            wall_ctype = ['masonry', 'masonry and metal', 'masonry and siding', 'window glass and masonry',
                      'steel frame and masonry', 'concrete panels', 'window glass and concrete', 'concrete and siding',
                      'pre-cast concrete panels', 'brick, stone, or stucco', 'concrete block or poured concrete']
            cwall_ctype = ['window/vision glass', 'decor./construction glass', 'window and construction glass',
                       'window or vision glass', 'decorative or construction glass']
            if component.hasType.lower() in wall_ctype:
                ctype = 'wall'
            elif component.hasType.lower() in cwall_ctype:
                ctype = 'glass panel'
            else:
                print('C&C type currently not supported')
                ctype = None
        elif isinstance(component, Roof):
            if component.hasPitch <= 2/12:
                ctype = 'flat roof cover'
            else:
                # Determine the ctype for the component:
                mtl_ctype = ['metal surfacing', 'built-up', 'built-up and metal']
                if component.hasCover.lower() in mtl_ctype:
                    ctype = 'metal deck'
                else:
                    print('C&C type currently not supported')
                    ctype = None
        return ctype


    def get_warea(self, ctype, parcel_flag, h_story):
        # Determine the effective area for a wall C&C:
        if ctype == 'mullion':
            if parcel_flag:
                if h_story <= 15:  # [ft]
                    area_eff = h_story*5  # [ft^2]
                else:
                    area_eff = h_story*h_story/3  # [ft^2]
            else:
                pass
        elif ctype == 'glass panel':
            if parcel_flag:
                area_eff = (h_story/2)*5  # [ft^2]
            else:
                pass
        elif ctype == 'wall':  # Later change to: if ctype in wall list
            area_eff = h_story*h_story/3  # [ft^2]
        elif ctype is None:
            print('C&C type currently not supported')

        return area_eff

    def get_rarea(self, ctype, parcel_flag, h_story):
        # Determine the effective area for roof C&C:
        if ctype == 'Metal deck':
            if parcel_flag:
                area_eff = [8.33, 16]  # [ft^2]
            else:
                pass
        elif ctype is None:
            print('C&C type currently not supported')
        return area_eff


    def ref_bldg(self):
        # Reference building parameters:
        ref_exposure = 'B'
        ref_hstory = 9 # [ft]
        ref_hbldg = 9 # [ft]
        ref_pitch = 6  # Choose a roof pitch <= 10 and (7) degrees
        ref_cat = 2 # Category for Importance Factor
        hpr = True  # Will later need to create the logic for these designations
        h_ocean = True # The entire Bay County is within 100 miles of the ocean
        encl_class = 'Enclosed'
        ref_speed = 70 # [mph]
        return ref_exposure, ref_hstory, ref_hbldg, ref_pitch, ref_speed, ref_cat, hpr, h_ocean, encl_class

    def populate_sim_parameters(self):
        # Run this function to output all of the files related to initial development:
        # This includes:
        # (1) Roof MWFRS for use case 1-4, all code editions
        # (2) Wall C&C for mullion, glass panel, wall, all code editions (except ASCE 7-93)
        # Define a range of wind speed values:
        wind_speed = np.arange(70, 185, 5)  # [mph]
        # Populate the reference building attributes:
        ref_exposure, ref_hstory, ref_hbldg, ref_pitch, ref_speed, ref_cat, hpr, h_ocean, encl_class = self.ref_bldg()
        # (1) Roof MWFRS for use case 1-4, all code editions
        # Create a vector of editions:
        edition = ['ASCE 7-95', 'ASCE 7-98', 'ASCE 7-10', 'ASCE 7-16']
        # Define use cases:
        use_case = [1, 2]
        # Populate similitude parameters for each case of Roof MWFRS:
        for case in use_case:
            self.run_sim_rmwfrs(ref_exposure, ref_hbldg, ref_pitch, ref_cat, wind_speed, edition, case, hpr, h_ocean, encl_class, plot_flag=False, save_flag=False)
        # ASCE 7-93/88 use cases
        edition = ['ASCE 7-93']
        # Define use cases:
        use_case = [3, 4]
        # Populate similitude parameters for each case of Roof MWFRS:
        for case in use_case:
            self.run_sim_rmwfrs(ref_exposure, ref_hbldg, ref_pitch, ref_cat, wind_speed, edition, case, hpr, h_ocean, encl_class, plot_flag=False, save_flag=False)
        # (2) Wall C&C for mullion, glass panel, wall, all code editions (except ASCE 7-93)
        # Create a vector of editions:
        edition = ['ASCE 7-95', 'ASCE 7-98', 'ASCE 7-10', 'ASCE 7-16']
        # Determine the effective area using typical practice:
        parcel_flag = True
        # C&C Types:
        ctype = ['mullion', 'glass panel', 'wall']
        for component in ctype:
            self.run_sim_wcc(ref_exposure, ref_hbldg, ref_hstory, ref_pitch, ref_cat, wind_speed, edition, component, parcel_flag, hpr, h_ocean, encl_class, plot_flag=False, save_flag=False)


# Plotting: % change in wind pressure vs. change in height
#pcalc = PressureCalc()
#area_eff = [50, 20, 50, 100]
#wind_speed = np.arange(100, 150, 5)
#h_bldg = 13.1234
#heights = np.arange(h_bldg*5, h_bldg*9, h_bldg)
#ref_height = round(h_bldg*6, 3)
#pitch = 0
#cat = 2
#hpr = True
#h_ocean = True
#encl_class = 'Enclosed'
#tpu_flag = False
#exposure = 'C'
#edition = 'ASCE 7-05'
#area_list = []
#for area in area_eff:
 #   rcc_dict = {}
  #  for h in heights:
   #     rcc_list = []
    #    for speed in wind_speed:
     #       rccs = pcalc.rcc_pressure(speed, exposure, edition, h, pitch, area, cat, hpr, h_ocean, encl_class, tpu_flag)
      #      rcc_list.append(rccs[-1])
       # rcc_dict[h] = rcc_list
#    area_list.append(rcc_dict)
# Print the pct_change between the base height
#df = pd.DataFrame(area_list[3])
#col_names = {}
#for h in range(0, len(heights)):
#    col_names[df.columns[h]] = round(heights[h],3)
#df = df.rename(columns=col_names)
#change_dict = {}
#for col in df.columns:
#    if col == round(ref_height,3):
#        change_dict[col] = 0
#    else:
#        change_dict[col] = (df[col][0] - df[ref_height][0])/df[ref_height][0]
#print(change_dict)
# Plot pressure vs. wind speed for various heights:
#from matplotlib import rcParams
#rcParams['font.family'] = "Times New Roman"
#rcParams.update({'font.size': 28})
#fig, axs = plt.subplots(2, 2)
#for d in range(0, len(area_list)):
    # Plot the pressure vs. wind speed for all heights for one effective area
#    if d == 0:
#        count = 1*5
#        for key in area_list[d]:
#            h_label = 4*(count)  # [m]
#            plt.plot(wind_speed/2.237, np.array(area_list[d][key])/20.885, label=str(h_label)+' m')
#            count += 1
#        plt.xlabel('Wind Speed [m/s]')
#        plt.ylabel('Pressure [kN/$\mathregular{m^2}$]')
        #axs[0,0].set_ylabel('Pressure [kN/$m^2$]')
#        plt.legend()
#        plt.show()
   # elif d == 1:
    #    for key in area_list[d]:
     #       axs[0, 1].plot(wind_speed, area_list[d][key])
    #elif d == 2:
     #   for key in area_list[d]:
      #      axs[1, 0].plot(wind_speed, area_list[d][key])
    #elif d == 3:
     #   for key in area_list[d]:
      #      axs[1, 1].plot(wind_speed, area_list[d][key])
#plt.show()
#a = 0

#pcalc = PressureCalc()
#p=pcalc.wcc_pressure(134, 'B', 'ASCE 7-16', 52.5, 0, 75, 2, True, True, 'Enclosed', False)
#print(np.array(p)/0.020885)

#wind_speed = np.arange(70, 185, 5)
#ref_exposure, ref_hstory, ref_hbldg, ref_pitch, ref_speed, ref_cat, hpr, h_ocean, encl_class = pressures.ref_bldg()
#edition = ['ASCE 7-95', 'ASCE 7-98', 'ASCE 7-10', 'ASCE 7-16']
#parcel_flag = True
#ctype = 'Metal deck'
#rcc = pressures.run_sim_rcc(ref_exposure, ref_hbldg, ref_hstory, ref_pitch, ref_cat,  wind_speed, edition, ctype, parcel_flag, hpr, h_ocean, encl_class)