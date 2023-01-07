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


def auto_populate(BIM):
    """
    Populates the DL model for hurricane (wind) damage assessments in Bay County, FL
    Compatible with pre- and post-FBC fragility models described in:

    Angeles, K., and Kijewski-Correa, T. (2022). "Bayesian data integration framework for the development of
    component-level fragilities derived from multiple post-disaster datasets." Structural Safety, 99(102260).
    https://doi.org/10.1016/j.strusafe.2022.102260

    Assumptions:
    - (IMPORTANT) Buildings in Asset Description are all compatible with sample building characteristics as described in
        Angeles and Kijewski-Correa (2022). If this is NOT the case, uncomment the block of code beginning at Line 90 to
        automatically parse information in BIM and establish similitude.
    - Everything relevant to auto-population is provided in the Building
    Information Model (BIM).
    - The information expected in the BIM file is described in the parse_BIM
    method.

    Parameters
    ----------
    BIM: dictionary
        Contains the information that is available about the asset and will be
        used to auto-populate the damage and loss model.

        (Option 1): For buildings that are already confirmed to be similar to sample buildings used in Angeles and
        Kijewski-Correa (2022), only the roof cover year of construction is required.

        (Option 2): Otherwise, the following information is needed: roof cover year of construction, state, county,
        occupancy, building height, roof shape, and roof slope. (Note: state and county are used to verify regionality)


    Returns
    -------
    BIM_ap: dictionary
        Contains the extended BIM data.
    DL_ap: dictionary
        Contains the auto-populated loss model.
    """

    # parse the BIM data
    BIM_ap = parse_BIM(BIM)

    # ---------------------Option 1: Compatible Asset Description------------------------------------
    # -----------------------------------------------------------------------------------------------

    # Execute simple year_built query to figure out if Pre_FBC or FBC construction:
    if BIM_ap['RCYearBuilt'] < 2002:
        component_config = 'WSF_Pre_FBC'
    else:
        component_config = 'WSF_FBC'

    # # --------------------Option 2: Full query of Asset Description----------------------------------
    # # --------------Uncomment below for a full query of the asset description:-----------------------
    # # -----------------------------------------------------------------------------------------------
    # 
    # # --------------------Preliminary query to see if this building is in Florida and in the Bay County-----------------
    # # Print warnings if otherwise:
    # if BIM_ap['state'].upper() == 'FL' or BIM_ap['state'].upper() == 'FLORIDA':
    #     state = True
    # else:
    #     state = False
    #     print("WARNING: Custom fragilities are developed using sample buildings from Florida's Bay County. Use at "
    #           "modeler's discretion.")
    # if 'BAY' in BIM_ap['county'].upper():
    #     county = True
    # else:
    #     county = False
    #     print("WARNING: Custom fragilities are developed using sample buildings from Florida's Bay County. Use at "
    #           "modeler's discretion.")
    #
    # # ---------------------------------------------Verify roof cover type:---------------------------------------------
    # if BIM_ap['RoofCover'].upper() == 'ENG SHINGL' or 'ASPHALT' in BIM_ap['RoofCover'].upper():
    #     rcover = True
    # else:
    #     rcover = False
    #     print('Custom fragilities are for asphalt shingle roof covers only. Modify IF statement if identifier for'
    #           'this county is different than those provided.')
    #
    # # ---------------------------------------------Verify occupancy type:-----------------------------------------------
    # if 'SINGLE' in BIM_ap['OccupancyClass'].upper():
    #     occ = True
    # else:
    #     occ = False
    #     print('Custom fragilities are for single family occupancies only. Modify IF statement is identifier is '
    #           'different that those provided.')
    #
    # # -------------------------------------------Verify building height:------------------------------------------------
    # # Note - building heights were estimated using DOE's residential reference buildings. Stories
    # # estimate can also be used when no building height data is available, to modeler's discretion.
    # if (3.35*3.281) <= BIM_ap['BldgHeight'] <= (10*3.281):
    #     height = True
    # else:
    #     height = False
    #     print('Custom fragilities are for single family homes with height between 3.35-10 m.')
    #
    # # ------------------------- Load path-related queries (based on Wind loading provisions in ASCE 7):-----------------
    # # (1) Check that roof was constructed before ASCE 7 2016:
    # if BIM_ap['RCYearBuilt'] < 2016:
    #     ryear = True
    # else:
    #     ryear = False
    #     print('Roof constructed using ASCE 7-16 provisions. Does not fit roof pressure zone use case used to develop '
    #           'these custom fragilities.')
    # # (2) Roof shape:
    # if 'gab' in BIM_ap['RoofShape'].lower() or 'hip' in BIM_ap['RoofShape'].lower():
    #     rshape = True
    # else:
    #     rshape = False
    #     print('Custom fragilities are for gable or hip roof shapes only.')
    #
    # # (3) Roof Slope:
    # if 0.12 < BIM_ap['RoofSlope'] <= 0.51:
    #     rslope = True
    # else:
    #     rslope = False
    #     print('Custom fragilities are for roof pitches between 7-27.')
    #
    # # (4) Pressure zone:
    # if rshape and rslope and ryear:
    #     zone = True
    # else:
    #     zone = False
    #     print('Building roof pressure zone use case is incompatible.')
    #
    # # ---------------------------------------Compile component fragility identifier:-----------------------------------
    # if state & county & rcover & occ & height & ryear & rshape & rslope & zone:
    #     if BIM_ap['RCYearBuilt'] < 2002:
    #         component_config = 'WSF_Pre_FBC'
    #     else:
    #         component_config = 'WSF_FBC'
    # else:
    #     component_config = 'Not compatible with these custom fragilities'
    #
    # # ------------------------------------------------------------------------------------------------------------------
    # # ------------------------------------- End of Option 2 Code Block -------------------------------------------------

    # Compile information for DL module:
    DL_ap = {
        '_method'      : 'HAZUS MH HU',
        'LossModel'    : {
            'DecisionVariables': {
                "ReconstructionCost": True
            },
            'ReplacementCost'  : 100
        },
        'Components'   : {
            component_config: [{
                'location'       : '1',
                'direction'      : '1',
                'median_quantity': '1.0',
                'unit'           : 'ea',
                'distribution'   : 'N/A'
            }]
        }
    }
    return BIM_ap, DL_ap