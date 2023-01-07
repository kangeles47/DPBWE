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


def MECB_config(BIM):
    """
    Rules to identify a HAZUS MECB configuration based on BIM data
    Parameters
    ----------
    BIM: dictionary
        Information about the building characteristics.
    Returns
    -------
    config: str
        A string that identifies a specific configuration within this building
        class.
    """

    # Roof cover:
    # Chapter 15 in 2001-2017 FBC addresses Built Up Roofs and Single Ply Membranes.
    # However, the FBC only addresses installation and material standards of different roof covers,
    # but not in what circumstance each must be used.
    # Assign roof cover types considering roof shape and construction trends.
    if BIM['RoofShape'] in ['gab', 'hip']:
        roof_cover = 'bur'
        # Warning: HAZUS does not have N/A option for CECB, so here we use bur
    else:
        if BIM['YearBuilt'] >= 1975:
            roof_cover = 'spm'
        else:
            # year < 1975
            roof_cover = 'bur'

    # Shutters
    # Section 1609.1.4 in FBC 2007-2017 says protection of openings required for buildings located in WBD regions,
    # mentions impact-rated protection for glazing, impact-resistance for garage door glazed openings, and finally
    # states that wood structural panels with a thickness > 7/16" and a span <8' can be used, as long as they are
    # precut, attached to the framing surrounding the opening, and the attachments are resistant to corrosion
    # and are able to resist component and cladding loads;
    # FBC 2001/2004: Section 1606.1.4 states that exterior glazing < 60 ft in buildings is considered an opening in
    # WBD regions unless impact resistant glass or covering is provided. Section 1606.1.4.2 states that WBD region
    # requirements do not apply landward of designated contour line in Figure 1606.
    # Note that previous logic to designate meta-variable WBD will ensure Panhandle exemption for construction built
    # between 2001 and 2007 FBC.
    if BIM['YearBuilt'] > 2001:
        shutters = BIM['WBD']
    elif 1994 < BIM['YearBuilt'] <= 2001:
        # 1994 SFBC: Section 3501.1 - Specifies that exterior wall cladding, surfacing and glazing within
        # lowest 30 ft of structure must be sufficiently strong to resist large missile impact test; > 30 ft
        # must be able to resist small missile impact test
        # Since homes outside of HVHZ would have been built following CABO, it is assumed that no shutter protection
        # was enacted.
        if BIM['HVHZ']:
            shutters = True
        else:
            shutters = False
    else:
        # 1992 SFBC: Section 3513 - Storm shutters are not required for glass glazing
        # Since homes outside of HVHZ would have been built following CABO, it is assumed that no shutter protection
        # was enacted.
        shutters = False

    # Wind Debris (widd in HAZUS)
    # HAZUS A: Res/Comm, B: Varies by direction, C: Residential, D: None
    widd = 'C'  # residential (default)
    if BIM['OccupancyClass'] in ['SINGLE FAM (000100), MULTI-FAMI (000300), COOPERATIV (000500)']:
        widd = 'C'  # residential
    elif BIM['OccupancyClass'] in ['VACANT/XFO (000070), VACANT (000000), VACANT COM (001000), VACANT COM (001070), '
                                    'NO AG ACRE (009900)']:
        widd = 'D'  # None
    else:
        widd = 'A'  # Res/Comm

    # Window area ratio
    if BIM['WindowArea'] < 0.33:
        wwr = 'low'
    elif BIM['WindowArea'] < 0.5:
        wwr = 'med'
    else:
        wwr = 'hig'

    # Metal RDA 2001 FBC: Section 1504.1 - Wind resistance of roofs. Roof decks and roof coverings shall be designed
    # for wind loads in accordance with Chapter 16 (structural design) and 1504.2, 1504.3, 1504.4. 2001 FBC: Section
    # 1508.8.4 - Attachment. Metal roofing shall be secured in accordance with manufacturer's installation
    # instructions.
    # HVHZ: 2001 FBC: Section 1519.7.2 - Steel decks shall be welded or mechanically attached to the
    # structure in compliance with the design pressure requirements set forth in Chapter 16. Section 1523.6.5.2.4
    # outlines various testing requirements to ensure proper resistance. Assume this corresponds to a superior roof
    # attachment in HVHZ.
    if BIM['YearBuilt'] < 2001:
        if not BIM['HVHZ']:
            mrda = 'std'  # standard
        else:
            mrda = 'sup'  # superior
    else:
        # 1973 SBC - Section 1505 lists various AISC-SJI standards for OWSJ construction but no additional information
        # regarding deck attachment.
        # HVHZ: SFBC (e.g., see 1988 SFBC - Section 2809.3(c)) simply states that sheets must be able to resist uplift
        # and diaphragm forces.
        # Assume all connections before FBC are standard.
        mrda = 'std'

    # Window area ratio
    if BIM['WindowArea'] < 0.33:
        wwr = 'low'
    elif BIM['WindowArea'] < 0.5:
        wwr = 'med'
    else:
        wwr = 'hig'

    if BIM['NumberOfStories'] <= 2:
        bldg_tag = 'MECBL'
    elif BIM['NumberOfStories'] <= 5:
        bldg_tag = 'MECBM'
    else:
        bldg_tag = 'MECBH'

    bldg_config = f"{bldg_tag}_" \
                  f"{roof_cover}_" \
                  f"{wwr}_" \
                  f"{int(shutters)}_" \
                  f"{widd}_" \
                  f"{mrda}_" \
                  f"{int(BIM['Terrain'])}"
    return bldg_config