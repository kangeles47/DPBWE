#from BIM import Parcel
import numpy as np
import random #switch later

class SurveyData:


    def run(self, parcel):
        # Check what survey this parcel needs data from:
        if parcel.is_comm:
            survey = 'CBECS'
        else:
            survey = 'RECS - currently not supported'

        print(survey)

        # Determine the census division for the CBECS and RECS surveys:
        if survey == 'CBECS' or 'RECS':
            census_div = self.census_division(parcel)

        #Now call the function that populates building attributes using the CBECS:
        if survey == 'CBECS':
            self.CBECS(census_div, parcel)

    def census_division(self, parcel):
        # Census division for CBECS/RECS:
        if parcel.state == 'FL' or 'DE' or 'DC' or 'GA' or 'MD' or 'NC' or 'SC' or 'VA' or 'WV':
            census_div = 'South Atlantic'
            census_region = 'South'
            print(census_div)
        elif parcel.state == 'AL' or 'KY' or 'MS' or 'TN':
            census_div = 'East South Central'
            census_region = 'South'
        elif parcel.state == 'AR' or 'LA' or 'OK' or 'TX':
            census_div = 'West South Central'
            census_region = 'South'
        return census_div


    def CBECS(self, census_div, parcel):
        # Determine survey year and populate type attributes:
        if parcel.yr_built > 2012 and parcel.yr_built <= 2018:
            data_yr = 2018
        elif parcel.yr_built <= 2012 and parcel.yr_built > 2003:
            data_yr = 2012
        elif parcel.yr_built <= 2003 and parcel.yr_built > 1999:
            data_yr = 2003
            # Pull the building data relevant to this survey year:
            if census_div == 'South Atlantic':
                # Roof attributes:
                roof_type = ['Builtup', 'Shingles (Not Wood)', 'Metal Surfacing', 'Synthetic or Rubber',
                             'Slate or Tile']
                roof_weights = [211, 234, 244, 78, 66]
                parcel.roof.cover = random.choices(roof_type, roof_weights)

                # Wall attributes:
                wall_type = ['Brick, Stone, or Stucco', 'Concrete (Block or Poured)', 'Concrete Panels',
                             'Siding or shingles', 'Metal Panels']
                wall_weights = [418, 175, 16, 117, 136]
                choice = random.choices(wall_type, wall_weights)

                for lst in range(0, 4):  # starting with four walls per floor
                    for index in range(0, len(parcel.walls)):  # for every list (story)
                        parcel.walls[index][lst].type = choice

                # Window attributes
                window_type = ['Multipaned windows', 'Tinted Window Glass', 'Reflective Window Glass']
                window_weights = [379, 294, 53]
                parcel.windows.type = random.choices(window_type, window_weights)

            else:
                print('census division not currently supported')
        elif parcel.yr_built <= 1999 and parcel.yr_built > 1995:
            data_yr = 1999
        elif parcel.yr_built <= 1995 & parcel.yr_built > 1992:
            data_yr = 1995
        elif parcel.yr_built <= 1992 & parcel.yr_built > 1989:
            data_yr = 1992
        elif parcel.yr_built <= 1989 & parcel.yr_built > 1986:
            data_yr = 1989
        elif parcel.yr_built <= 1986 & parcel.yr_built > 1983:
            data_yr = 1986
        elif parcel.yr_built <= 1983 & parcel.yr_built > 1979:
            data_yr = 1983
        elif parcel.yr_built <= 1979:
            data_yr = 1979
        print(data_yr)

#Let's play with the file:
#test = Parcel('12345', 5, 'Hotel', 2002, "801 10th CT E Panama City 32401",'3200')
#b = NatlSurveyData(test)
