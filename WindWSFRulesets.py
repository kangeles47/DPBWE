import random
import datetime


def WSF_config(BIM):
    """
    Rules to identify a HAZUS WSF configuration based on building data
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

    # Secondary Water Resistance (SWR)
    swr = False
    if BIM['RoofReplaceYear'] > 2008:
        swr = True
    else:
        if BIM['YearBuilt'] > 2008:  # swr required in single family homes upon 2009 supplement to 2007 FBC
            swr = True
        elif 2007 < BIM['YearBuilt'] <= 2008:
            if BIM['hvhz']:  # between 2007-2008, swr required in HVHZ and outside HVHZ
                swr = True
            else:
                if (2/12) <= BIM['RoofSlope'] < (4/12):  # swr required for some sloped roofs
                    swr = True  # Based off of roof retrofit provisions in 2007 FBC - Existing buildings
                else:
                    # For roof slopes >= 4/12 and not in HVHZ, use homeowner
                    # compliance data from NC Coastal Homeowner Survey (2017) to capture potential
                    # human behavior (% of sealed roofs in NC dataset).
                    swr = random.random() < 0.6
        elif 2001 < BIM['YearBuilt'] <= 2007:
            # For buildings built before enactment of FBC, SWR is based on homeowner
            # compliance data from NC Coastal Homeowner Survey (2017) to capture potential
            # human behavior (% of sealed roofs in NC dataset).
            swr = random.random() < 0.6
        else:
            # According to 903.2 in the 1995 CABO, for roofs with slopes between
            # 2:12 and 4:12, an underlayment consisting of two layers of No. 15
            # felt must be applied. In severe climates (less than or equal to 25
            # degrees Fahrenheit average in January), these two layers must be
            # cemented together.
            # According to 903.3 in the 1995 CABO, roofs with slopes greater than
            # or equal to 4:12 shall have an underlayment of not less than one ply
            # of No. 15 felt.
            #
            # Similar rules are prescribed in CABO 1992, 1989, 1986, 1983
            #
            # Since low-slope roofs require two layers of felt, this is taken to
            # be secondary water resistance. This ruleset is for asphalt shingles.
            # Almost all other roof types require underlayment of some sort, but
            # the ruleset is based on asphalt shingles because it is most
            # conservative.
            if BIM['RoofShape'].lower() == 'flt':  # note there is actually no 'flat'
                swr = True
            elif BIM['RoofShape'].lower() == 'gab' or BIM['RoofShape'].lower() == 'hip':
                if BIM['RoofSlope'] <= 0.17:
                    swr = True
                elif 0.17 < BIM['RoofSlope'] < 0.33:
                    swr = (BIM['avg_jan_temp'].lower() == 'below')
                elif BIM['RoofSlope'] >= 0.33:
                    swr = False

    # Roof Deck Attachment (RDA)
    rda = '6d' # Default (aka A) in Reorganized Rulesets - WIND
    if BIM['RoofReplaceYear'] > 2008:
        rda = '8s'
    else:
        if BIM['YearBuilt'] > 2001:
            # Table R602.2(1) of 2007 FBCR requires 8d nails with 6"/12" spacing for Vasd less that 100 mph
            # 8d nails with 6"/6" spacing for Vasd > 100 mph.
            if BIM['DWSII'] > 130:
                rda = '8s'
            else:
                rda = '8d'  # 8d @ 6"/12" ('B' in the Reorganized Rulesets - WIND)
        elif 1994 < BIM['YearBuilt'] <= 2001:
            # 1994 SFBC: Section 2909.2 - Requires 8d nails with 6"/6" for roof sheathing (HVHZ)
            # 1995 CABO: Table 602.3a - 8d or 6d nails at 6"/12" depending on sheathing thickness.
            # Assign as RV for buildings outside of HVHZ.
            if BIM['hvhz']:
                rda = '8s'
            else:
                if random.random() <= 0.5:
                    rda = '6d'  # 6d @ 6"/12" ('A' in the Reorganized Rulesets - WIND)
                else:
                    rda = '8d'  # 8d @ 6"/12" ('B' in the Reorganized Rulesets - WIND)
        else:
            # year <= 1994
            # SFBC and CABO both designate nailing based on sheathing thickness
            # See e.g., 1992 SFBC: Section 2909.2 and 1992 CABO: Table R-402.3a.
            # With no way to determine actual sheathing thickness, assign as random variable:
            if random.random() <= 0.5:
                rda = '6d'  # 6d @ 6"/12" ('A' in the Reorganized Rulesets - WIND)
            else:
                rda = '8d'  # 8d @ 6"/12" ('B' in the Reorganized Rulesets - WIND)

    # Roof-Wall Connection (RWC)
    # 2001 FBC: Section 2321.1 - Anchorage shall be continuous from the
    # foundation to the roof and shall satisfy the uplift requirements of Section 1620.
    # 2001 FBC: Section 2321.6.1 indicates that steel straps must be used in HVHZ to connect wood to wood.
    # Documentation from FL's State Board of Administration indicate that straps became the standard for Floridian
    # construction after Hurricane Andrew in 1992.
    # Assume that if classified as HPR, then enhanced connection would be used.
    if BIM['RoofReplaceYear'] > 2008:
        rwc = 'strap'
    else:
        if BIM['YearBuilt'] > 1992:
            if BIM['hpr']:
                rwc = 'strap'  # Strap
            else:
                rwc = 'tnail'  # Toe-nail
        # HAZUS-HM documentation states that tie down straps have been required for rwc in Dade and Broward counties since
        # the inception of the SFBC in the late 1950's. In Palm Beach County, rwc have been straps since late 1970's.
        elif 1957 < BIM['YearBuilt'] <= 1992:
            if BIM['hvhz']:
                rwc = 'strap'  # Strap
            else:
                if BIM['YearBuilt'] > 1976 and BIM['county'].lower() == 'palm beach':
                    rwc = 'strap'
                else:
                    rwc = 'tnail'
        else:
            rwc = 'tnail'  # Assume all remaining construction uses toe-nails for rwc

    # Shutters
    # FBCR 2000-2015:
    # R301.2.1.2 in 2207-2017 FBCR says protection of openings required for buildings located in WBD regions,
    # mentions impact-rated protection for glazing, impact-resistance for garage door glazed openings, and finally
    # states that wood structural panels with a thickness > 7/16" and a span <8' can be used, as long as they are
    # precut, attached to the framing surrounding the opening, and the attachments are resistant to corrosion
    # and are able to resist component and cladding loads;
    # Earlier FBC editions provide similar rules.
    # Note that previous logic to designate meta-variable WBD will ensure Panhandle exemption for construction built
    # between 2001 and 2007 FBC.
    shutters = False  # default value
    if BIM['YearBuilt'] > 2001:
        shutters = BIM['WBD']
    elif 1994 < BIM['YearBuilt'] <= 2001:
        # 1994 SFBC: Section 3501.1 - Specifies that exterior wall cladding, surfacing and glazing within
        # lowest 30 ft of structure must be sufficiently strong to resist large missile impact test; > 30 ft
        # must be able to resist small missile impact test
        # Since homes outside of HVHZ would have been built following CABO, it is assumed that no shutter protection
        # was not required; use human subjects data to designate statistical description.
        if BIM['hvhz']:
            shutters = True
        else:
            if BIM['WBD']:
                shutters = random.random() < 0.45
    else:
        # 1992 SFBC: Section 3513 - Storm shutters are not required for glass glazing
        # Since homes outside of HVHZ would have been built following CABO, it is assumed that no shutter protection
        # was not required; use human subjects data to designate statistical description.
        if BIM['WBD']:
            shutters = random.random() < 0.45

    # Garage
    # As per FBC 2001 Section 1606.1.4 through FBCR 2017 Section R301.2.1.2:
    # Garage door glazed opening protection for windborne debris shall meet the
    # requirements of an approved impact-resisting standard or ANSI/DASMA 115.
    # Exception: Wood structural panels with a thickness of not less than 7/16
    # inch and a span of not more than 8 feet shall be permitted for opening
    # protection. Panels shall be predrilled as required for the anchorage
    # method and shall be secured with the attachment hardware provided.
    # Permitted for buildings where the ultimate design wind speed is 180 mph
    # or less.
    #
    # Average lifespan of a garage is 30 years, so garages that are not in WBD
    # (and therefore do not have any strength requirements) that are older than
    # 30 years are considered to be weak, whereas those from the last 30 years
    # are considered to be standard.
    if BIM['Garage'] == -1:  # -1 used to designate no garage data
        # no garage data, using the default "standard"
        garage = 'std'
        shutters = False  # HAZUS ties standard garage to w/o shutters
    else:
        if BIM['YearBuilt'] > 2001:
            if shutters:
                if BIM['Garage'] < 1:
                    garage = 'no'
                else:
                    garage = 'sup'  # SFBC 1994
                    shutters = True  # HAZUS ties SFBC 1994 to with shutters
            else:
                if BIM['Garage'] < 1:
                    garage = 'no' # None
                else:
                    garage = 'std' # Standard
                    shutters = False  # HAZUS ties standard garage to w/o shutters
        elif BIM['YearBuilt'] > (datetime.datetime.now().year - 30):
            if BIM['Garage'] < 1:
                garage = 'no'  # None
            else:
                garage = 'std'  # Standard
                shutters = False  # HAZUS ties standard garage to w/o shutters
        else:
            # year <= current year - 30
            if BIM['Garage'] < 1:
                garage = 'no'  # None
            else:
                garage = 'wkd'  # Weak
                shutters = False  # HAZUS ties weak garage to w/o shutters

    # building configuration tag
    bldg_config = f"WSF" \
                  f"{int(min(BIM['NumberOfStories'],2))}_" \
                  f"{BIM['RoofShape']}_" \
                  f"{int(swr)}_" \
                  f"{rda}_" \
                  f"{rwc}_" \
                  f"{garage}_" \
                  f"{int(shutters)}_" \
                  f"{int(BIM['terrain'])}"
    return bldg_config
