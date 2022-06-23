import random
import numpy as np
import datetime


def wmuh_config(BIM):
    """
    Rules to identify a HAZUS WMUH configuration based on BIM data
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

    # Secondary Water Resistance (SWR)
    # SWR = 0 # Default
    # 2017 FBC: Section 1518.4 - Lists underlayment requirements for prepared roof coverings in HVHZ.
    # Included in this list is a double layer of an ASTM D226 Type I underlayment. It is assumed that the
    # listed single layer options are equivalent. Assume swr for WMUH with asphalt shingles and in HVHZ.
    # Note that similar underlayment requirements are seen starting from 2001 FBC.
    swr = int(False)  # Default value
    if BIM['year_built'] > 2001:
        if BIM['roof_shape'] == 'flt':
            swr = 'null' # because SWR is not a question for flat roofs
        elif BIM['roof_shape'] in ['gab','hip']:
            if BIM['hvhz']:
                swr = int(True)
            else:
                swr = int(random.random() < 0.6)
    elif 1979 < BIM['year_built'] <= 2001:
        if BIM['roof_shape'] == 'flt':
            swr = 'null' # because SWR is not a question for flat roofs
        elif (BIM['roof_shape'] == 'gab') or (BIM['roof_shape'] == 'hip'):
            # 1988 SFBC: Section 3402.3 - For asphalt shingles, the following underlayment is required:
            # 30 lb felt underlayment, fastened through tin-caps placed 18" o.c. both ways.
            # Consulting newer code editions, this description is not considered SWR in an HVHZ region.
            if BIM['hvhz']:
                swr = int(False)
            else:
                # Come back and check SWR requirements in SBC:
                if BIM['roof_slope'] < 0.33:
                    swr = int(True)
                else:
                    swr = int(BIM['avg_jan_temp'] == 'below')
    else:
        # year <= 1979
        if BIM['roof_shape'] == 'flt':
            swr = 'null' # because SWR is not a question for flat roofs
        else:
            # Use human subjects data from NC:
            swr = int(random.random() < 0.3)

    # Roof cover & Roof quality
    # Roof cover and quality do not apply to gable and hip roofs
    if BIM['roof_shape'] in ['gab', 'hip']:
        roof_cover = 'null'
        roof_quality = 'null'
    # Chapter 15 in the FBC (2001-2017) addresses Built Up Roofs and Single Ply Membranes. However, the FBC
    # only addresses installation and material standards of different roof covers, but not in what circumstance
    # each must be used. # SPMs started being used in the 1960s, but different types continued to be
    # developed through the 1980s. Today, single ply membrane roofing is the most popular flat roof option.
    # BURs have been used for over 100 years, and although they are still used today, they are used less than SPMs.
    # Since there is no available ruleset to be taken from the FBC, the ruleset is based off this information.
    # We assume that all flat roofs built before 1975 are BURs and all roofs built after 1975 are SPMs.

    # Nothing in the FBC or in the Hazus manual specifies what
    # constitutes “good” and “poor” roof conditions, so ruleset is dependant
    # on the age of the roof and average lifespan of BUR and SPM roofs.
    # We assume that the average lifespan of a BUR roof is 30 years and the
    # average lifespan of a SPM is 35 years. Therefore, BURs installed before
    # 1990 are in poor condition, and SPMs installed before 1985 are in poor
    # condition.
    else:
        if BIM['year_built'] >= 1975:
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

    # Roof Deck Attachment (RDA)
    # 2017/2014 FBC: Section 2322.2.5 - requires 8d nails, 6"/6" spacing for roof sheathing in HVHZ
    # 2017/2014 FBC: Table 2304.10.1 - Use of 8d nails requires 6"/12" spacing for all roof sheathing thicknesses.
    # Other nailing options also mentioned, but assume that 8d nails are used.
    if BIM['year_built'] > 2014:
        if BIM['hvhz']:
            rda = '8s'  # 8d @ 6"/6" 'D'
        else:
            rda = '8d'  # 8d @ 6"/12" 'B'
    elif 2007 < BIM['year_built'] <= 2014:
        # 2007 to 2010 FBC: Section 2322.2.5 - Requires 8d nails, 6"/6" spacing for roof sheathing in HVHZ.
        # 2007 to 2010 FBC: Table 2304.9.1 or 2304.10.1 (respectively) - 8d nails with 6"/6" spacing required
        # for roofs in basic wind speeds between 110-140 mph (exposure B). 8d nails with 6"/12" spacing listed as
        # an option for sheathing thicknesses <= 1/2" and > 19/32".
        if BIM['hvhz']:
            rda = '8s'
        else:
            if BIM['V_ult'] > 142.0:
                rda = '8s'
            else:
                rda = '8d'
    elif 2001 < BIM['year_built'] <= 2007:
        # 2001/2004 FBC: Section 2322.2.4 and 2322.2.5 - Requires 8d nails, 6"/6" spacing for roof sheathing in HVHZ.
        # 2001/2004 FBC: Table 2306.1/Table 2304.9.1 - Requires 8d nails, 6"/12" spacing for roof sheathing.
        if BIM['hvhz']:
            rda = '8s'
        else:
            rda = '8d'
    elif 1994 < BIM['year_built'] <= 2001:
        # 1994 SFBC: Section 2909.2 - Requires 8d nails with 6"/6" spacing for roof sheathing. (HVHZ)
        # 1973 SBC: Table 1704.1 - Requires 6d nails with 6"/12" spacing for sheathing thicknesses <= 1/2".
        # 8d nails with 6"/12" spacing for sheathing of >= 5/8" thickness. With no way to determine actual
        # sheathing thickness assign as a random variable for regions outside of HVHZ.
        if BIM['hvhz']:
            rda = '8s'
        else:
            if random.random() <= 0.5:
                rda = '6d'
            else:
                rda = '8d'
    else:
        # 1992 SFBC: Section 2909.2 - Indicates that 8d nails be used for roof sheathing 5/8", 3/4", and 7/8" thick.
        # 6d nails be used for minimum 1/2" thick sheathing. 6"/12" spacing required for both applications.
        # Same requirement is seen starting in 1957 SFBC.
        # 1973 SBC: Table 1704.1 - Requires 6d nails with 6"/12" spacing for roof sheathing <= 1/2" thick.
        # 8d nails with 6"/12" spacing required for roof sheathing >= 5/8" thick. There are no clear requirements that
        # indicate a change of connector at a certain wind speed.
        # With no way to determine actual sheathing thickness for HVHZ/non-HVHZ regions, assign using a random variable.
        if random.random() <= 0.5:
            rda = '6d'
        else:
            rda = '8d'

    # Roof-Wall Connection (RWC)
    # IRC 2000-2015:
    # 1507.2.8.1 High Wind Attachment. Underlayment applied in areas subject
    # to high winds (Vasd greater than 110 mph as determined in accordance
    # with Section 1609.3.1) shall be applied with corrosion-resistant
    # fasteners in accordance with the manufacturer’s instructions. Fasteners
    # are to be applied along the overlap not more than 36 inches on center.
    # Underlayment installed where Vasd, in accordance with section 1609.3.1
    # equals or exceeds 120 mph shall be attached in a grid pattern of 12
    # inches between side laps with a 6-inch spacing at the side laps.
    if BIM['year_built'] > 2001:
        if BIM['V_ult'] > 142.0:
            RWC = 'strap'  # Strap
        else:
            RWC = 'tnail'  # Toe-nail
    # BOCA 1996 and earlier:
    # There is no mention of straps or enhanced tie-downs of any kind in the
    # BOCA codes, and there is no description of these adoptions in IBHS
    # reports or the New Jersey Construction Code Communicator .
    # Although there is no explicit information, it seems that hurricane straps
    # really only came into effect in Florida after Hurricane Andrew (1992),
    # and likely it took several years for these changes to happen. Because
    # Florida is the leader in adopting hurricane protection measures into
    # codes and because there is no mention of shutters or straps in the BOCA
    # codes, it is assumed that New Jersey did not adopt these standards until
    # the 2000 IBC.
    else:
        RWC = 'tnail'  # Toe-nail

    # Shutters
    # IRC 2000-2015:
    # 1609.1.2 Protection of Openings. In wind-borne debris regions, glazing in
    # buildings shall be impact resistant or protected with an impact-resistant
    # covering meeting the requirements of an approved impact-resistant
    # covering meeting the requirements of an approved impact-resistant
    # standard.
    # Exceptions: Wood structural panels with a minimum thickness of 7/16 of an
    # inch and a maximum panel span of 8 feet shall be permitted for opening
    # protection in buildings with a mean roof height of 33 feet or less that
    # are classified as a Group R-3 or R-4 occupancy.
    # Earlier IRC editions provide similar rules.
    if year >= 2000:
        shutters = BIM['WBD']
    # BOCA 1996 and earlier:
    # Shutters were not required by code until the 2000 IBC. Before 2000, the
    # percentage of commercial buildings that have shutters is assumed to be
    # 46%. This value is based on a study on preparedness of small businesses
    # for hurricane disasters, which says that in Sarasota County, 46% of
    # business owners had taken action to wind-proof or flood-proof their
    # facilities. In addition to that, 46% of business owners reported boarding
    # up their businesses before Hurricane Katrina. In addition, compliance
    # rates based on the Homeowners Survey data hover between 43 and 50 percent.
    else:
        if BIM['WBD']:
            shutters = random.random() < 0.46
        else:
            shutters = False

    # Stories
    # Buildings with more than 3 stories are mapped to the 3-story configuration
    stories = min(BIM['stories'], 3)

    bldg_config = f"WMUH" \
                  f"{int(stories)}_" \
                  f"{BIM['roof_shape']}_" \
                  f"{roof_cover}_" \
                  f"{roof_quality}_" \
                  f"{swr}_" \
                  f"{rda}_" \
                  f"{RWC}_" \
                  f"{int(shutters)}_" \
                  f"{int(BIM['terrain'])}"

    return bldg_config