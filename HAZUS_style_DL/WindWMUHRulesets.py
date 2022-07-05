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

    # Secondary Water Resistance (swr)
    swr = 0  # Default
    # 2017 FBC: Section 1518.4 - Lists underlayment requirements for prepared roof coverings in HVHZ.
    # Included in this list is a double layer of an ASTM D226 Type I underlayment. It is assumed that the
    # listed single layer options are equivalent. Assume swr for WMUH with asphalt shingles and in HVHZ.
    # Note that similar underlayment requirements are seen starting from 2001 FBC.
    swr = int(False)  # Default value
    if BIM['year_built'] > 2001:
        if BIM['roof_shape'] == 'flt':
            swr = 'null'  # because SWR is not a question for flat roofs
        elif BIM['roof_shape'] in ['gab', 'hip']:
            if BIM['hvhz']:
                swr = int(True)
            else:
                # Use homeowner compliance data from NC Coastal Homeowner Survey (2017) to capture potential
                # human behavior (% of sealed roofs in NC dataset) that would lead to the installation of SWR
                # in regions outside of HVHZ.
                swr = int(random.random() < 0.6)
    elif 1979 < BIM['year_built'] <= 2001:
        if BIM['roof_shape'] == 'flt':
            swr = 'null'  # because SWR is not a question for flat roofs
        elif (BIM['roof_shape'] == 'gab') or (BIM['roof_shape'] == 'hip'):
            # 1988 SFBC: Section 3402.3 - For asphalt shingles, the following underlayment is required:
            # 30 lb felt underlayment, fastened through tin-caps placed 18" o.c. both ways.
            # Consulting newer code editions, this description is not considered SWR in an HVHZ region.
            if BIM['hvhz']:
                swr = int(False)
            else:
                # No access to Standard Building Code after 1976, so adopt BOCA-based ruleset for now:
                # BOCA code requires SWR for steep-slope roofs with winters at or below 25℉, according
                # to Section 1507.4. Asphalt shingles can be installed on roof slopes 2:12 and greater.
                # BUR is considered low-slope roofing.
                if BIM['roof_slope'] < 0.33:
                    swr = int(True)
                else:
                    swr = int(BIM['avg_jan_temp'] == 'below')
    else:
        # year <= 1979
        if BIM['roof_shape'] == 'flt':
            swr = 'null'  # because SWR is not a question for flat roofs
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

    # Roof-Wall Connection (rwc)
    # 2001-2017 FBC: Section 2321.6.1 indicates that steel straps must be used in HVHZ to connect wood to wood.
    # General construction requirements for load paths in wood frame construction (2004-2017 FBC Section 2304.10.6):
    # Requires sheet metal clamps, ties, or clips where wall framing members are not continuous from the foundation sill
    # to the roof to ensure continuous load path.
    # Documentation from FL's State Board of Administration indicate that straps became the standard for Floridian
    # construction after Hurricane Andrew in 1992.
    # It is understood that wind speed intensities throughout most of Florida would result in pressures that would
    # require the installation of metal straps in order for roof-to-wall connections to be deemed code-compliant.
    # Assume that if in HPR, straps are required (most of FL).
    if BIM['year_built'] > 1992:
        if BIM['hpr']:
            rwc = 'strap'  # Strap
        else:
            rwc = 'tnail'  # Toe-nail
    elif 1957 < BIM['year_built'] <= 1992:
        # HAZUS-HM documentation states that tie down straps have been required for rwc in Dade and Broward counties
        # since inception of the SFBC. In Palm Beach county, roof-wall tie downs have been required on every truss-wall
        # connections since the late 1970s. 1957 SFBC: Section 2905 - Wood-to-wood anchorage must be steel strap. See
        # Section 2908.6 in 1992 SFBC for similar requirements. 1973 Standard Building Code: Section 1205.3 - Indicates
        # that adequate anchorage of the roof to walls and columns is required to resist wind loads, but does not
        # specify the connection type. Assume toe-nail for any construction outside of HVHZ and for Palm Beach County
        # before 1976.
        if BIM['hvhz']:
            rwc = 'strap'
        else:
            if BIM['county'].upper() == 'PALM BEACH':
                if BIM['year_built'] > 1976:
                    rwc = 'strap'
                else:
                    rwc = 'tnail'
            else:
                rwc = 'tnail'
    else:
        rwc = 'tnail'  # Assume all remaining construction uses toe-nails for rwc

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

    # Stories
    # Buildings with more than 3 stories are mapped to the 3-story configuration
    stories = min(BIM['stories'], 3)

    bldg_config = f"W.MUH." \
                  f"{int(stories)}." \
                  f"{BIM['roof_shape']}." \
                  f"{roof_cover}." \
                  f"{roof_quality}." \
                  f"{swr}." \
                  f"{rda}." \
                  f"{rwc}." \
                  f"{int(shutters)}." \
                  f"{int(BIM['terrain'])}"

    return bldg_config
