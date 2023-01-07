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

import datetime


def SPMB_config(BIM):
    """
    Rules to identify a HAZUS SPMB configuration based on BIM data
    Parameters
    ----------
    BIM: dictionary
        Information about the building characteristics.
    Returns
    -------
    config: str
        A string that identifies a specific configration within this buidling
        class.
    """

    # Roof Deck Age (~ Roof Quality)
    if BIM['year_built'] >= (datetime.datetime.now().year - 50):
        roof_quality = 'god'
    else:
        roof_quality = 'por'

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
    if BIM['year_built'] > 2001:
        shutters = BIM['WBD']
    elif 1994 < BIM['year_built'] <= 2001:
        # 1994 SFBC: Section 3501.1 - Specifies that exterior wall cladding, surfacing and glazing within
        # lowest 30 ft of structure must be sufficiently strong to resist large missile impact test; > 30 ft
        # must be able to resist small missile impact test
        # Since homes outside of HVHZ would have been built following CABO, it is assumed that no shutter protection
        # was enacted.
        if BIM['hvhz']:
            shutters = True
        else:
            shutters = False
    else:
        # 1992 SFBC: Section 3513 - Storm shutters are not required for glass glazing
        # Since homes outside of HVHZ would have been built following CABO, it is assumed that no shutter protection
        # was enacted.
        shutters = False

    # Metal RDA 2001 FBC: Section 1504.1 - Wind resistance of roofs. Roof decks and roof coverings shall be designed
    # for wind loads in accordance with Chapter 16 (structural design) and 1504.2, 1504.3, 1504.4. 2001 FBC: Section
    # 1508.8.4 - Attachment. Metal roofing shall be secured in accordance with manufacturer's installation
    # instructions.
    # HVHZ: 2001 FBC: Section 1519.7.2 - Steel decks shall be welded or mechanically attached to the
    # structure in compliance with the design pressure requirements set forth in Chapter 16. Section 1523.6.5.2.4
    # outlines various testing requirements to ensure proper resistance. Assume this corresponds to a superior roof
    # attachment in HVHZ.
    if BIM['year_built'] < 2001:
        if not BIM['hvhz']:
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

    if BIM['area'] <= 4000:
        bldg_tag = 'SPMBS'
    elif BIM['area'] <= 50000:
        bldg_tag = 'SPMBM'
    else:
        bldg_tag = 'SPMBL'

    bldg_config = f"{bldg_tag}_" \
                  f"{roof_quality}_" \
                  f"{int(shutters)}_" \
                  f"{mrda}_" \
                  f"{int(BIM['terrain'])}"
    return bldg_config