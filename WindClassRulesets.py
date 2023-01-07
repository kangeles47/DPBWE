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


def building_class(BIM):
    """
    A function to identify HAZUS building class using occupancy and frame type information.

    :param BIM: dictionary
        Contains the information that is available about the asset and will be
        used to auto-populate the damage and loss model.
    :return:
        One of the standard building class labels from HAZUS (bldg_class) in auto-populate function

    """
    wmuh_occupancies = ['MULTI-FAMI (000300)', 'COOPERATIV (000500)', 'HOTELS AND (003900)']
    comm_eng_occupancies = ['OFFICE BLD (001700)', 'STORES, 1 (001100)', 'DRIVE-IN R (002200)']
    if BIM['OccupancyClass'] == 'SINGLE FAM (000100)':
        # Single family homes in HAZUS can only have hip or gable roofs
        if 'MASONRY' in BIM['FrameType']:
            return 'MSF'
        else:
            # Assume that this is a wood frame structural system
            return 'WSF'
    elif any(occ == BIM['OccupancyClass'] for occ in wmuh_occupancies):
        # Multi-family homes and Multi-unit hotel/motels:
        if 'STEEL' in BIM['FrameType']:  # engineered residential
            return 'SERB'  # Note: ruleset for SERB still needs to be formalized for FL
        elif 'CONCRETE' in BIM['FrameType']:  # engineered residential
            return 'CERB'
        else:
            if 'MASONRY' in BIM['FrameType'] and BIM['NumberOfStories'] < 4:
                return 'MMUH'  # Note: ruleset for MMUH still needs to be formalized for FL
            else:
                # Assume that this is a wood frame structural system
                return 'WMUH'
    else:
        spbm_occupancies = ['GYM (003350)', 'WAREHOUSE- (004800)']
        # Choose from remaining commercial occupancies:
        if 'STEEL' in BIM['FrameType']:  # engineered residential
            if any(occ == BIM['OccupancyClass'] for occ in spbm_occupancies) and BIM['NumberOfStories'] == 1:
                return 'SPMB'
            else:
                return 'SECB'
        elif 'CONCRETE' in BIM['FrameType']:  # engineered commercial
            return 'CECB'
        elif 'MASONRY' in BIM['FrameType'] and any(occ == BIM['OccupancyClass'] for occ in comm_eng_occupancies):
            return 'MECB'
        elif 'WOOD' in BIM['FrameType'] or 'NOT AVAILABLE' in BIM['FrameType']:
            return 'WMUH'  # model as a hotel/motel/multi-fam unit
        else:
            return 'WMUH'
