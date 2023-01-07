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

from WindMetaVarRulesets import parse_BIM
from WindClassRulesets import building_class
from WindWSFRulesets import WSF_config
from WindWMUHRulesets import WMUH_config
from WindMECBRulesets import MECB_config
from WindSECBRulesets import SECB_config
from WindSPMBRulesets import SPMB_config


def auto_populate(BIM):
    """
    Populates the DL model for hurricane (wind) loss assessments in Bay County, FL

    Assumptions:
    - Everything relevant to auto-population is provided in the Buiding
    Information Model (BIM). (Asset Representation Module in R2D).
    - The information expected in the BIM file is described in the parse_BIM
    method.

    Parameters
    ----------
    BIM: dictionary
        Contains the information that is available about the asset and will be
        used to auto-populate the damage and loss model.

    Returns
    -------
    BIM_ap: dictionary
        Contains the extended BIM data.
    DL_ap: dictionary
        Contains the auto-populated loss model.
    """

    # parse the BIM data
    BIM_ap = parse_BIM(BIM)

    # identify the building class
    bldg_class = building_class(BIM_ap)
    BIM_ap.update({'HazusClassW': bldg_class})

    # prepare the building configuration string
    if bldg_class == 'WSF':
        bldg_config = WSF_config(BIM_ap)
    elif bldg_class == 'WMUH':
        bldg_config = WMUH_config(BIM_ap)
    elif bldg_class == 'MECB':
        bldg_config = MECB_config(BIM_ap)
    elif bldg_class == 'SECB':
        bldg_config = SECB_config(BIM_ap)
    elif bldg_class == 'SPMB':
        bldg_config = SPMB_config(BIM_ap)
    else:
        raise ValueError(
            f"Building class {bldg_class} not recognized by the "
            f"auto-population routine."
        )
    print(bldg_config)
    DL_ap = {
        '_method'      : 'HAZUS MH HU',
        'LossModel'    : {
            'DecisionVariables': {
                "ReconstructionCost": True
            },
            'ReplacementCost'  : 100
        },
        'Components'   : {
            bldg_config: [{
                'location'       : '1',
                'direction'      : '1',
                'median_quantity': '1.0',
                'unit'           : 'ea',
                'distribution'   : 'N/A'
            }]
        }
    }
    # Note: might needs to add some "Combinations field: see auto_HU_LA"
    return BIM_ap, DL_ap