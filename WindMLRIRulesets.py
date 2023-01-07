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

import random
import numpy as np
import datetime


def MLRI_config(BIM):
    """
    Rules to identify a HAZUS MLRI configuration based on BIM data
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

    year = BIM['YearBuilt'] # just for the sake of brevity

    # MR
    MR = True

    # Shutters
    shutters = False

    # Metal RDA
    # 2001 FBC: Section 1508.8.4 - Attachment.
    # Metal roofing shall be secured in accordance with manufacturer's installation instructions.
    # 2001 FBC: Section 1519.7.2 - Steel decks shall be welded or mechanically attached to the
    # structure in compliance with the design pressure requirements set forth in Chapter 16 (HVHZ).
    # 2001 FBC: Section 1523.6.5.2.4 - Metal shingles/panels --> this section outlines various testing
    # requirements to ensure proper resistances for metal roofing. Asssume this corresponds to a superior
    # roof deck attachment in HVHZ.
    if BIM['YearBuilt'] < 2001:
        if BIM['HVHZ']:
            MRDA = 'sup'  # superior
        else:
            MRDA = 'std'  # standard
    else:
        MRDA = 'std'  # standard

    # Roof cover (HAZUS) and quality
    roof_cover = ''
    # First try with assessor-reported roof cover:
    if BIM['RoofCover'].lower() == 'SINGLE PLY':
        roof_cover = 'spm'
    elif BIM['RoofCover'].upper() == 'BUILT-UP':
        roof_cover = 'bur'
    # Roof quality:
    if len(roof_cover) > 0:
        if BIM['RoofShape'] in ['gab', 'hip']:
            roof_quality = 'god'
        else:
            if year >= 1975 and roof_cover == 'spm':
                if BIM['year_built'] >= (datetime.datetime.now().year - 35):
                    roof_quality = 'god'
                else:
                    roof_quality = 'por'
            else:
                if BIM['year_built'] >= (datetime.datetime.now().year - 30):
                    roof_quality = 'god'
                else:
                    roof_quality = 'por'
    else:
        # Default rulesets:
        if BIM['RoofShape'] in ['gab', 'hip']:
            roof_cover = 'nav'
            roof_quality = 'god' # default supported by HAZUS
        else:
            if year >= 1975:
                roof_cover = 'spm'
                if BIM['year_built'] >= (datetime.datetime.now().year - 35):
                    roof_quality = 'god'
                else:
                    roof_quality = 'por'
            else:
                # year < 1975
                roof_cover = 'bur'
                if BIM['year_built'] >= (datetime.datetime.now().year - 30):
                    roof_quality = 'god'
                else:
                    roof_quality = 'por'

    bldg_config = f"MLRI_" \
                  f"{roof_quality}_" \
                  f"{int(shutters)}_" \
                  f"{int(MR)}_" \
                  f"{MRDA}_" \
                  f"{int(BIM['terrain'])}"
    return bldg_config