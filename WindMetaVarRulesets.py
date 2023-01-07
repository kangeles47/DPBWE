# Copyright (c) 2022 University of Notre Dame
#
# This file extends the original rulesets developed under DOI: https://doi.org/10.17603/ds2-83ca-r890 as part of the SimCenter Backend Applications
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice,
# this list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice,
# this list of conditions and the following disclaimer in the documentation
# and/or other materials provided with the distribution.
#
# 3. Neither the name of the copyright holder nor the names of its contributors
# may be used to endorse or promote products derived from this software without
# specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#
# You should have received a copy of the BSD 3-Clause License along with
# this file. If not, see <http://www.opensource.org/licenses/>.
#
# Contributors:
# Karen Angeles
#
# Based on rulesets developed by:
# Karen Angeles

import numpy as np
from math import sqrt


def parse_BIM(BIM):
    """
    Parses the information provided in the BIM model.

    The attributes below list the expected metadata in the BIM file:
    Year Built: Building Year of Construction
    DWSII: The ultimate design wind speed, in mph
    county: The name of the Florida county the asset resides in (not case-sensitive)
    FloodZone: The FEMA flood zone.
    city: The name of the city the asset resides in
    lulc: The LULC category (see rulesets below for additional resources)

    Returns
    -------
    BIM: dictionary
        Parsed building characteristics.
    """

    # Hurricane-Prone Region (HPR)
    # Areas vulnerable to hurricane, defined as the U.S. Atlantic Ocean and
    # Gulf of Mexico coasts where the ultimate design wind speed, V_ult is
    # greater than a pre-defined limit.
    if BIM['YearBuilt'] > 2012:
        # The limit is 115 mph (ultimate wind speed, V_ult) in 2010-2017 FBC (see Section 1609.2)
        HPR = BIM['DWSII'] > 115.0
    else:
        # The limit is 90 mph (basic wind speed, V_asd) in 2001-2009 FBC
        # Conversion: V_asd = V_ult*sqrt(0.6)
        HPR = BIM['DWSII'] > 90.0/sqrt(0.6)
    BIM['hpr'] = HPR

    # High-velocity hurricane zone (HVHZ):
    # Chapter 2 in 2001-2017 FBC defines HVHZ zone as Broward and Dade Counties. Note that before the FBC, these counties adhered to the South Florida Building Code (SFBC)
    if 'BROWARD' in BIM['county'].upper() or 'DADE' in BIM['county'].upper():
        BIM['hvhz'] = True
    else:
        BIM['hvhz'] = False

    # Wind Borne Debris
    # (Section 202 - FBC 2017 and 2014, Section 1609.2 - FBC 2010)
    # Areas within hurricane-prone regions are affected by debris if one of
    # the following two conditions holds:
    # (1) Within 1 mile (1.61 km) of the coastal mean high water line where
    # the ultimate design wind speed is 130 mph or greater. (flood_lim)
    # (2) In areas where the ultimate design wind speed is greater than 140 mph (general_lim)
    # The flood_lim and general_lim limits depend on the year of construction
    panhandle_flag = False  # variable to enact Panhandle WBD exemption
    panhandle_counties = ['GULF', 'BAY', 'WALTON', 'OKALOOSA', 'SANTA ROSA', 'ESCAMBIA']
    if BIM['YearBuilt'] > 2011:
        # In 2010 FBC - present:
        flood_lim = 130.0  # mph
        general_lim = 140.0  # mph
    elif BIM['YearBuilt'] <= 2011:
        # Section 1609.2 - FBC 2007
        # Areas within hurricane-prone regions located in accordance with one of the following:
        # (1) Within 1 mile (1.61 km) of the coastal mean high water line where the basic wind speed, Vasd, is 110 mph (48m/s) or greater.
        # (2) In areas where the basic wind speed is 120 mph (53 m/s) or greater.
        # Conversion: V_asd = V_ult*sqrt(0.6)
        flood_lim = 110/sqrt(0.6)  # mph
        general_lim = 120.0/sqrt(0.6)  # mph
        if BIM['YearBuilt'] <= 2007:
            # Check for Panhandle exemption: Section 1609.2 - FBC 2004, Section 1606.1.5 - FBC 2001
            # Areas within hurricane-prone regions located in accordance with one of the following:
            # (1) Within 1 mile (1.61 km) of the coastal mean high water line where the basic wind speed, Vasd, is 110 mph (48m/s) or greater.
            # (2) Areas where the basic wind speed is 120 mph (53 m/s) or greater except from the eastern border of Franklin County to the Florida-Alabama line where the region includes areas only 1 mile of the coast.
            if any(county in BIM['county'].upper() for county in panhandle_counties):
                panhandle_flag = True
            else:
                pass
        else:
            pass
    # Determine if in WBD region:
    if not HPR:
        WBD = False
    else:
        # Applicable flood zones for the Bay County include the following: A, AE, AH, AO, VE
        # Bay County, FL FEMA Flood Zones can easily be viewed at:
        # https://www.baycountyfl.gov/508/FEMA-Flood-Zones
        if panhandle_flag:
            if (BIM['FloodZone'].startswith('A') or BIM['FloodZone'].startswith('V')) and BIM['DWSII'] >= general_lim:
                WBD = True
            else:
                WBD = False
        else:
            WBD = (((BIM['FloodZone'].startswith('A') or BIM['FloodZone'].startswith('V')) and
                    BIM['DWSII'] >= flood_lim) or (BIM['DWSII'] >= general_lim))
        # Note: here if first criteria is met, this enforces 1-mi boundary for panhandle exemption.
        # In the future, it would be better to have an actually polygon or line that creates a boundary to easily query
    BIM['WBD'] = WBD
    # Terrain
    # open (0.03) = 3
    # light suburban (0.15) = 15
    # suburban (0.35) = 35
    # light trees (0.70) = 70
    # trees (1.00) = 100
    # For purposes of case study, set default to light suburban (0.15).
    # In the future, robust rulests can be formalized by consulting LULC categories for FL
    # https://geodata.dep.state.fl.us/datasets/FDEP::statewide-land-use-land-cover/about
    # Note that, for coastal cities, it may be more appropriate to designate open terrain conditions:
    coastal_cities_fl = ['MEXICO BEACH', 'PANAMA CITY BEACH']  # Add to list as rulesets get expanded for other FL regions
    if BIM['LULC'] == 1400:  # Commercial and services
        terrain = 35  # suburban
    elif BIM['LULC'] == 1330:  # High density, multiple dwelling units, low rise
        terrain = 35
    elif BIM['LULC'] == 1210 or BIM['LULC'] == 1740:  # Medium density, fixed single family units or medical/health care
        terrain = 15  # light suburban
    else:
        # Check for coastal cities:
        if any(city == BIM['city'].upper() for city in coastal_cities_fl):
            terrain = 3
        else:
            # Assume light, suburban terrain:
            terrain = 15  # Default value
    BIM['terrain'] = terrain

    return BIM
