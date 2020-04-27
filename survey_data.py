#from BIM import Parcel
import numpy as np
import random #switch later
import pandas as pd

class SurveyData:


    def run(self, parcel):
        # Check what survey this parcel needs data from:
        if parcel.is_comm:
            self.survey = 'CBECS'
        else:
            self.survey = 'RECS - currently not supported'

        print(self.survey)

        # Determine the census division for the CBECS and RECS surveys:
        #if self.survey == 'CBECS' or 'RECS':
            #census_div = self.census_division(parcel)

        #Now call the function that populates building attributes using the CBECS:
        if self.survey == 'CBECS':
            #self.CBECS(census_div, parcel)
            self.cbecs_attrib(parcel)

    def census_division(self, parcel):
        # Census division for CBECS/RECS:
        if parcel.state == 'FL' or 'DE' or 'DC' or 'GA' or 'MD' or 'NC' or 'SC' or 'VA' or 'WV':
            census_div = 5 # South Atlantic
            census_region = 'South'
        elif parcel.state == 'AL' or 'KY' or 'MS' or 'TN':
            census_div = 6 # East South Central
            census_region = 'South'
        elif parcel.state == 'AR' or 'LA' or 'OK' or 'TX':
            census_div = 7 # West South Central
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
                roof_choice = random.choices(roof_type, roof_weights)
                parcel.roof.cover = roof_choice[0]

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
                #parcel.windows.type = random.choices(window_type, window_weights)

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


    def cbecs_attrib(self, parcel):
        # First I need to know what survey I need to access and the year constructed tag (for filtering later):
        if parcel.yr_built <= 1989 and parcel.yr_built > 1986:
            data_yr = '1989'
            # Year constructed tag:
            if parcel.yr_built >= 1987 and parcel.yr_built <= 1989:
                value_yrconc = 9
            elif parcel.yr_built >= 1984 and parcel.yr_built <= 1986:
                value_yrconc = 8
            elif parcel.yr_built >= 1980 and parcel.yr_built <= 1983:
                value_yrconc = 7
            elif parcel.yr_built >= 1970 and parcel.yr_built <= 1979:
                value_yrconc = 6
            elif parcel.yr_built >= 1960 and parcel.yr_built <= 1969:
                value_yrconc = 5
            elif parcel.yr_built >= 1946 and parcel.yr_built <= 1959:
                value_yrconc = 4
            elif parcel.yr_built >= 1920 and parcel.yr_built <= 1945:
                value_yrconc = 3
            elif parcel.yr_built >= 1900 and parcel.yr_built <= 1919:
                value_yrconc = 2
            elif parcel.yr_built <= 1899:
                value_yrconc = 1
            else:
                print('CBECS year constructed code not supported')

        elif parcel.yr_built <= 2003 and parcel.yr_built > 1999:
            data_yr = '2003'
            # Populate tags for year constructed and square footage:
            # Year constructed tag:
            if parcel.yr_built == 2004:
                value_yrconc = 9
            elif parcel.yr_built >= 2000 and parcel.yr_built <= 2003:
                value_yrconc = 8
            elif parcel.yr_built >= 1990 and parcel.yr_built <= 1999:
                value_yrconc = 7
            elif parcel.yr_built >= 1980 and parcel.yr_built <= 1989:
                value_yrconc = 6
            elif parcel.yr_built >= 1970 and parcel.yr_built <= 1979:
                value_yrconc = 5
            elif parcel.yr_built >= 1960 and parcel.yr_built <= 1969:
                value_yrconc = 4
            elif parcel.yr_built >= 1946 and parcel.yr_built <= 1959:
                value_yrconc = 3
            elif parcel.yr_built >= 1920 and parcel.yr_built <= 1945:
                value_yrconc = 2
            elif parcel.yr_built < 1920:
                value_yrconc = 1
            else:
                print('Year Built not supported')

        print(value_yrconc)

        # Square footage tag:
        if parcel.sq_ft <= 1000:
            value_sq_ft = 1
        elif parcel.sq_ft > 1000 and parcel.sq_ft <= 5000:
            value_sq_ft = 2
        elif parcel.sq_ft > 5000 and parcel.sq_ft <= 10000:
            value_sq_ft = 3
        elif parcel.sq_ft > 10000 and parcel.sq_ft <= 25000:
            value_sq_ft = 4
        elif parcel.sq_ft > 25000 and parcel.sq_ft <= 50000:
            value_sq_ft = 5
        elif parcel.sq_ft > 50000 and parcel.sq_ft <= 10000:
            value_sq_ft = 6
        elif parcel.sq_ft > 100000 and parcel.sq_ft <= 20000:
            value_sq_ft = 7
        elif parcel.sq_ft > 200000 and parcel.sq_ft <= 500000:
            value_sq_ft = 8
        elif parcel.sq_ft > 500000 and parcel.sq_ft <= 1000000:
            value_sq_ft = 9
        elif parcel.sq_ft > 1000000:
            value_sq_ft = 10
        else:
            print('CBECS square footage code not determined')

        # Census division tag:
        if parcel.state == 'FL' or 'DE' or 'DC' or 'GA' or 'MD' or 'NC' or 'SC' or 'VA' or 'WV':
            census_div = 5  # South Atlantic
            print(census_div)
        elif parcel.state == 'AL' or 'KY' or 'MS' or 'TN':
            census_div = 6  # East South Central
        elif parcel.state == 'AR' or 'LA' or 'OK' or 'TX':
            census_div = 7  # West South Central

        # Read in the .csv file:
        CBECS_data = pd.read_csv('C:/Users/Karen/Desktop/1989_CBECS.csv')
        #CBECS_data = pd.read_csv(data_yr + 'CBECS.csv')


        #Filter the dataset according to census division, year constructed, and square footage:
        CBECS_data = CBECS_data.loc[(CBECS_data['CENDIV4'] == census_div) & (CBECS_data['YRCONC4'] == value_yrconc) & (CBECS_data['SQFTC4'] == value_sq_ft)]


        wall_options = CBECS_data['WLCNS4'].unique()
        roof_options = CBECS_data['RFCNS4'].unique()

        wall_weights = []
        roof_weights = []

        for option in wall_options:
            wall_weights.append(CBECS_data.loc[CBECS_data['WLCNS4'] == option, 'ADJWT4'].sum())

        for option in roof_options:
            roof_weights.append(CBECS_data.loc[CBECS_data['RFCNS4'] == option, 'ADJWT4'].sum())

        # Choose wall and roof descriptions:
        wall_choice = random.choices(wall_options,wall_weights)[0]
        roof_choice = random.choices(roof_options,roof_weights)[0]

        if wall_choice == 1:
            choice = 'Window/vision glass'
        elif wall_choice == 2:
            choice = 'Decor./construction glass'
        elif wall_choice == 3:
            choice = 'Concrete panels'
        elif wall_choice == 4:
            choice = 'Masonry'
        elif wall_choice == 5:
            choice = 'Siding/shingles/shakes'
        elif wall_choice == 6:
            choice = 'Metal panels'
        elif wall_choice == 7:
            choice = 'Other'
        elif wall_choice == 8:
            choice = 'Masonry & metal'
        elif wall_choice == 9:
            choice = 'Masonry & siding'
        elif wall_choice == 10:
            choice = 'Window glass & masonry'
        elif wall_choice == 11:
            choice = 'Window glass & concrete'
        elif wall_choice == 12:
            choice = 'Window glass & concrete'
        elif wall_choice == 13:
            choice = 'Window & construction glass'
        elif wall_choice == 14:
            choice = 'Steel frame & masonry'
        elif wall_choice == 15:
            choice = 'Window glass & metal'
        elif wall_choice == 16:
            choice = 'Concrete & siding'
        else:
            print('Wall construction not supported')

        print(choice)

        for lst in range(0, 4):  # starting with four walls per floor
            for index in range(0, len(parcel.walls)):  # for every list (story)
                parcel.walls[index][lst].type = choice

        if roof_choice == 1:
            parcel.roof.cover = 'Wooden materials'
        elif roof_choice == 2:
            parcel.roof.cover = 'Slate or tile'
        elif roof_choice == 3:
            parcel.roof.cover = 'Shingles (not wood)'
        elif roof_choice == 4:
            parcel.roof.cover = 'Built-up'
        elif roof_choice == 5:
            parcel.roof.cover = 'Metal surfacing'
        elif roof_choice == 6:
            parcel.roof.cover = 'Single/multiple ply'
        elif roof_choice == 7:
            parcel.roof.cover = 'Concrete roof'
        elif roof_choice == 8:
            parcel.roof.cover = 'Other'
        elif roof_choice == 9:
            parcel.roof.cover = 'Metal & rubber'
        elif roof_choice == 10:
            parcel.roof.cover = 'Cement & asphalt'
        elif roof_choice == 11:
            parcel.roof.cover = 'Composite'
        elif roof_choice == 12:
            parcel.roof.cover = 'Glass'
        elif roof_choice == 13:
            parcel.roof.cover = 'Shingles & metal'
        elif roof_choice == 14:
            parcel.roof.cover = 'Slate & built-up'
        elif roof_choice == 15:
            parcel.roof.cover = 'Built-up & metal'
        elif roof_choice == 16:
            parcel.roof.cover = 'Built-up & s/m ply'
        else:
            print('Roof construction not supported')



#Let's play with the file:
#test = Parcel('12345', 5, 'Hotel', 2002, "801 10th CT E Panama City 32401",'3200')
#b = NatlSurveyData(test)
