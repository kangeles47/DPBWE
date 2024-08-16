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


def MERB_config(BIM):
    """
    Rules to identify a HAZUS MERB configuration based on BIM data
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

    year = BIM['YearBuilt'] # just for the sake of brevity

    # Roof cover
    if BIM['RoofShape'] in ['gab', 'hip']:
        roof_cover = 'bur'
        # no info, using the default supoorted by HAZUS
    else:
        if year >= 1975:
            roof_cover = 'spm'
        else:
            # year < 1975
            roof_cover = 'bur'

    # shutters
    if year >= 2000:
        shutters = BIM['WBD']
    else:
        if BIM['WBD']:
            shutters = random.random() < 0.45
        else:
            shutters = False

    # Wind Debris (widd in HAZSU)
    # HAZUS A: Res/Comm, B: Varies by direction, C: Residential, D: None
    WIDD = 'C' # residential (default)
    if BIM['OccupancyClass'] in ['RES1', 'RES2', 'RES3A', 'RES3B', 'RES3C',
                                 'RES3D']:
        WIDD = 'C' # residential
    elif BIM['OccupancyClass'] == 'AGR1':
        WIDD = 'D' # None
    else:
        WIDD = 'A' # Res/Comm

    # Metal RDA
    # 1507.2.8.1 High Wind Attachment.
    # Underlayment applied in areas subject to high winds (Vasd greater
    # than 110 mph as determined in accordance with Section 1609.3.1) shall
    #  be applied with corrosion-resistant fasteners in accordance with
    # the manufacturer’s instructions. Fasteners are to be applied along
    # the overlap not more than 36 inches on center.
    if BIM['DWSII'] > 142:
        MRDA = 'std'  # standard
    else:
        MRDA = 'sup'  # superior

    # Window area ratio
    if BIM['WindowArea'] < 0.33:
        WWR = 'low'
    elif BIM['WindowArea'] < 0.5:
        WWR = 'med'
    else:
        WWR = 'hig'

    if BIM['NumberOfStories'] <= 2:
        bldg_tag = 'MERBL'
    elif BIM['NumberOfStories'] <= 5:
        bldg_tag = 'MERBM'
    else:
        bldg_tag = 'MERBH'

    bldg_config = f"{bldg_tag}" \
                  f"{roof_cover}_" \
                  f"{WWR}_" \
                  f"{int(shutters)}_" \
                  f"{WIDD}_" \
                  f"{MRDA}_" \
                  f"{int(BIM['Terrain'])}"
    return bldg_config