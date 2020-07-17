import random #switch later
import pandas as pd

class SurveyData:


    def run(self, parcel):
        # Check what survey this parcel needs data from:
        if parcel.is_comm:
            self.isSurvey = 'CBECS'
        else:
            self.isSurvey = 'RECS - currently not supported'

        # Determine the census division for the CBECS and RECS surveys:
        if self.isSurvey == 'CBECS' or self.isSurvey == 'RECS':
            census_div = self.get_census_division(parcel)

        # Call function that populates building attributes using the CBECS:
        if self.isSurvey == 'CBECS':
            self.cbecs_attrib(census_div, parcel)
        else:
            pass

    def get_census_division(self, parcel):
        # Census division for CBECS/RECS:
        sa_list = ['FL', 'DE', 'DC', 'GA', 'MD', 'NC', 'SC', 'VA', 'WV']
        if parcel.hasLocation['State'] in sa_list:
            census_div = 5  # South Atlantic
            census_region = 'South'
        else:
            esc_list = ['AL', 'KY', 'MS', 'TN']
            if parcel.hasLocation['State'] in esc_list:
                census_div = 6  # East South Central
                census_region = 'South'
            else:
                wsc_list = ['AR', 'LA', 'OK', 'TX']
                if parcel.hasLocation['State'] in wsc_list:
                    census_div = 7  # West South Central
                    census_region = 'South'
                else:
                    print('Census division/region currently not supported')
        return census_div

    def cbecs_attrib(self, census_div, parcel):
        # INFO: CBECS datasets are available for years: 2018, 2012, 2003, 1999, 1995, 1992, 1989, 1986, 1983, and 1979
        # For in this code, we are interested in accessing information for the following building attributes:
        # (1) Primary exterior wall material, (2) Primary roofing material, and (3) Window type
        # To access attributes (1)-(3) code does the following:
        # (1) Identify survey year and corresponding year identifier (this is for semantic translation purposes)
        # (2) Populate values for Year Constructed and Square Footage to filter microdata
        # (3) Conduct a random choice to assign attributes to the parcel

        # Find the dataset year, corresponding year identifier, and value for "Year Constructed" tag:
        if 1989 >= parcel.hasYearBuilt > 1986:
            data_yr = 1989
            yr_id = '4'
            # Value for Year Constructed tag:
            if 1987 <= parcel.hasYearBuilt <= 1989:
                value_yrconc = 9
            elif 1984 <= parcel.hasYearBuilt <= 1986:
                value_yrconc = 8
            elif 1980 <= parcel.hasYearBuilt <= 1983:
                value_yrconc = 7
            elif 1970 <= parcel.hasYearBuilt <= 1979:
                value_yrconc = 6
            elif 1960 <= parcel.hasYearBuilt <= 1969:
                value_yrconc = 5
            elif 1946 <= parcel.hasYearBuilt <= 1959:
                value_yrconc = 4
            elif 1920 <= parcel.hasYearBuilt <= 1945:
                value_yrconc = 3
            elif 1900 <= parcel.hasYearBuilt <= 1919:
                value_yrconc = 2
            elif parcel.hasYearBuilt <= 1899:
                value_yrconc = 1
            else:
                print('CBECS year constructed code not supported')
        elif 2003 >= parcel.hasYearBuilt > 1999:
            data_yr = 2003
            yr_id = '8'
            # Value for Year Constructed Tag
            if parcel.hasYearBuilt == 2004:
                value_yrconc = 9
            elif 2000 <= parcel.hasYearBuilt <= 2003:
                value_yrconc = 8
            elif 1990 <= parcel.hasYearBuilt <= 1999:
                value_yrconc = 7
            elif 1980 <= parcel.hasYearBuilt <= 1989:
                value_yrconc = 6
            elif 1970 <= parcel.hasYearBuilt <= 1979:
                value_yrconc = 5
            elif 1960 <= parcel.hasYearBuilt <= 1969:
                value_yrconc = 4
            elif 1946 <= parcel.hasYearBuilt <= 1959:
                value_yrconc = 3
            elif 1920 <= parcel.hasYearBuilt <= 1945:
                value_yrconc = 2
            elif parcel.hasYearBuilt < 1920:
                value_yrconc = 1
            else:
                print('Year Built not supported')
        elif 2012 >= parcel.hasYearBuilt > 2003:
            data_yr = 2012
            yr_id = None
            # Value for Year Constructed Tag
            if 2010 <= parcel.hasYearBuilt <= 2012:
                value_yrconc = 10
            elif 2004 <= parcel.hasYearBuilt <= 2007:
                value_yrconc = 9
            elif 2000 <= parcel.hasYearBuilt <= 2003:
                value_yrconc = 8
            elif 1990 <= parcel.hasYearBuilt <= 1999:
                value_yrconc = 7
            elif 1980 <= parcel.hasYearBuilt <= 1989:
                value_yrconc = 6
            elif 1970 <= parcel.hasYearBuilt <= 1979:
                value_yrconc = 5
            elif 1960 <= parcel.hasYearBuilt <= 1969:
                value_yrconc = 4
            elif 1946 <= parcel.hasYearBuilt <= 1959:
                value_yrconc = 3
            elif 1920 <= parcel.hasYearBuilt <= 1945:
                value_yrconc = 2
            elif parcel.hasYearBuilt < 1920:
                value_yrconc = 1
            else:
                print('Year Built not supported')

        # Value for square footage tag (consistent across datasets):
        if parcel.hasArea <= 1000:
            value_area = 1
        elif 1000 < parcel.hasArea <= 5000:
            value_area = 2
        elif 5000 < parcel.hasArea <= 10000:
            value_area = 3
        elif 10000 < parcel.hasArea <= 25000:
            value_area = 4
        elif 25000 < parcel.hasArea <= 50000:
            value_area = 5
        elif 50000 < parcel.hasArea <= 10000:
            value_area = 6
        elif 100000 < parcel.hasArea <= 20000:
            value_area = 7
        elif 200000 < parcel.hasArea <= 500000:
            value_area = 8
        elif 500000 < parcel.hasArea <= 1000000:
            value_area = 9
        elif parcel.hasArea > 1000000:
            value_area = 10
        else:
            print('CBECS square footage code not determined')

        # Read in the .csv file:
        path = 'D:/Users/Karen/Documents/Github/DPBWE/Datasets/CBECS/CBECS'
        CBECS_data = pd.read_csv(path + str(data_yr) + '.csv')

        if data_yr != 2012:
            # Filter the dataset according to census division, year constructed, and square footage:
            cendiv_tag = 'CENDIV' + yr_id
            yrc_tag = 'YRCONC' + yr_id
            sqft_tag = 'SQFTC' + yr_id
            CBECS_data = CBECS_data.loc[(CBECS_data[cendiv_tag] == census_div) & (CBECS_data[yrc_tag] == value_yrconc) & (CBECS_data[sqft_tag] == value_area)]

            # Find the unique set of types for each attribute and define tag for associated weights:
            wtype_tag = 'WLCNS' + yr_id
            rtype_tag = 'RFCNS' + yr_id
            wall_options = CBECS_data[wtype_tag].unique()
            roof_options = CBECS_data[rtype_tag].unique()
            wght_tag = 'ADJWT' + yr_id
            if data_yr == 2003:
                # Window type tag for 2003 CBECS:
                CBECS_data2 = pd.read_csv(path + str(data_yr) + '_2.csv')
                CBECS_data2 = CBECS_data2.loc[(CBECS_data2[cendiv_tag] == census_div) & (CBECS_data2[yrc_tag] == value_yrconc) & (CBECS_data2[sqft_tag] == value_area)]
                win_tag = 'WINTYP'
                win_options = CBECS_data2[win_tag].unique()
            else:
                pass
        else:
            # Filter the dataset according to census division, year constructed, and square footage:
            cendiv_tag = 'CENDIV'
            yrc_tag = 'YRCONC'
            sqft_tag = 'SQFTC'
            CBECS_data = CBECS_data.loc[(CBECS_data[cendiv_tag] == census_div) & (CBECS_data[yrc_tag] == value_yrconc) & (CBECS_data[sqft_tag] == value_area)]

            # Find the unique set of types for each attribute and define tag for associated weights:
            wtype_tag = 'WLCNS'
            rtype_tag = 'RFCNS'
            rtilt_tag = 'RFTILT'
            glsspc_tag = 'GLSSPC'
            win_tag = 'WINTYP'
            wall_options = CBECS_data[wtype_tag].unique()
            roof_options = CBECS_data[rtype_tag].unique()
            rtilt_options = CBECS_data[rtilt_tag].unique()
            glsspc_options = CBECS_data[glsspc_tag].unique()
            win_options = CBECS_data[win_tag].unique()
            wght_tag = 'FINALWT'

        # Find the weights for each of the attributes:
        wall_weights = []
        roof_weights = []

        for option in wall_options:
            wall_weights.append(CBECS_data.loc[CBECS_data[wtype_tag] == option, wght_tag].sum())

        for option in roof_options:
            roof_weights.append(CBECS_data.loc[CBECS_data[rtype_tag] == option, wght_tag].sum())

        # Choose wall and roof types:
        wall_choice = random.choices(wall_options,wall_weights)[0]
        roof_choice = random.choices(roof_options,roof_weights)[0]

        # Conduct the semantic translations from the respective CBECS dataset
        # Wall type descriptions:
        if data_yr == 1989:
            if wall_choice == 1:
                wtype = 'Window/vision glass'
            elif wall_choice == 2:
                wtype = 'Decor./construction glass'
            elif wall_choice == 3:
                wtype = 'Concrete panels'
            elif wall_choice == 4:
                wtype = 'Masonry'
            elif wall_choice == 5:
                wtype = 'Siding/shingles/shakes'
            elif wall_choice == 6:
                wtype = 'Metal panels'
            elif wall_choice == 7:
                wtype = 'Other'
            elif wall_choice == 8:
                wtype = 'Masonry & metal'
            elif wall_choice == 9:
                wtype = 'Masonry & siding'
            elif wall_choice == 10:
                wtype = 'Window glass & masonry'
            elif wall_choice == 11:
                wtype = 'Window glass & concrete'
            elif wall_choice == 12:
                wtype = 'Window glass & concrete'
            elif wall_choice == 13:
                wtype = 'Window & construction glass'
            elif wall_choice == 14:
                wtype = 'Steel frame & masonry'
            elif wall_choice == 15:
                wtype = 'Window glass & metal'
            elif wall_choice == 16:
                wtype = 'Concrete & siding'
            else:
                print('Wall construction not supported')
        elif data_yr == 2003 or data_yr == 2012:
            if wall_choice == 1:
                wtype = 'Brick, stone, or stucco'
            elif wall_choice == 2:
                choice = 'Pre-cast concrete panels'
            elif wall_choice == 3:
                wtype = 'Concrete block or poured concrete'
            elif wall_choice == 4:
                wtype = 'Siding, shingles, tiles, or shakes'
            elif wall_choice == 5:
                wtype = 'Sheet metal panels'
            elif wall_choice == 6:
                wtype = 'Window or vision glass'
            elif wall_choice == 7:
                wtype = 'Decorative or construction glass'
            elif wall_choice == 8:
                wtype = 'No one major type'
            elif wall_choice == 9:
                wtype = 'Other'
        else:
            print('Survey year currently not supported')

        # Assign wall type description to every exterior wall for the parcel:
        for storey in parcel.hasStorey:
            for wall in storey.containsElements['Walls']:
                wall.hasType = wtype

        # Roof type descriptions:
        roof_storey = parcel.hasStorey[-1]
        if data_yr == 1989:
            if roof_choice == 1:
                roof_storey.containsElement['Roof'].hasCover = 'Wooden materials'
            elif roof_choice == 2:
                roof_storey.containsElement['Roof'].hasCover = 'Slate or tile'
            elif roof_choice == 3:
                roof_storey.containsElement['Roof'].hasCover = 'Shingles (not wood)'
            elif roof_choice == 4:
                roof_storey.containsElement['Roof'].hasCover = 'Built-up'
            elif roof_choice == 5:
                roof_storey.containsElement['Roof'].hasCover = 'Metal surfacing'
            elif roof_choice == 6:
                roof_storey.containsElement['Roof'].hasCover = 'Single/multiple ply'
            elif roof_choice == 7:
                roof_storey.containsElement['Roof'].hasCover = 'Concrete roof'
            elif roof_choice == 8:
                roof_storey.containsElement['Roof'].hasCover = 'Other'
            elif roof_choice == 9:
                roof_storey.containsElement['Roof'].hasCover = 'Metal & rubber'
            elif roof_choice == 10:
                roof_storey.containsElement['Roof'].hasCover = 'Cement & asphalt'
            elif roof_choice == 11:
                roof_storey.containsElement['Roof'].hasCover = 'Composite'
            elif roof_choice == 12:
                roof_storey.containsElement['Roof'].hasCover = 'Glass'
            elif roof_choice == 13:
                roof_storey.containsElement['Roof'].hasCover = 'Shingles & metal'
            elif roof_choice == 14:
                roof_storey.containsElement['Roof'].hasCover = 'Slate & built-up'
            elif roof_choice == 15:
                roof_storey.containsElement['Roof'].hasCover = 'Built-up & metal'
            elif roof_choice == 16:
                roof_storey.containsElement['Roof'].hasCover = 'Built-up & s/m ply'
            else:
                print('Roof construction not supported')
        elif data_yr == 2003 or data_yr == 2012:
            if roof_choice == 1:
                roof_storey.containsElement['Roof'].hasCover = 'Built-up'
            elif roof_choice == 2:
                roof_storey.containsElement['Roof'].hasCover = 'Slate or tile shingles'
            elif roof_choice == 3:
                roof_storey.containsElement['Roof'].hasCover = 'Wood shingles/shakes/other wood'
            elif roof_choice == 4:
                roof_storey.containsElement['Roof'].hasCover = 'Asphalt/fiberglass/other shingles'
            elif roof_choice == 5:
                roof_storey.containsElement['Roof'].hasCover = 'Metal surfacing'
            elif roof_choice == 6:
                roof_storey.containsElement['Roof'].hasCover = 'Plastic/rubber/synthetic sheeting'
            elif roof_choice == 7:
                roof_storey.containsElement['Roof'].hasCover = 'Concrete'
            elif roof_choice == 8:
                roof_storey.containsElement['Roof'].hasCover = 'No one major type'
            elif roof_choice == 9:
                roof_storey.containsElement['Roof'].hasCover = 'Other'
        else:
            print('Survey year currently not supported')

        print(roof_storey.containsElement['Roof'].hasCover)

        # For CBECS 2003 and 2012, additional attributes are available for building glass percentage and window type:
        if data_yr == 2003 or data_yr == 2012:
            # Building glass percentage:
            glsspc_weights = []
            for option in glsspc_options:
                glsspc_weights.append(CBECS_data.loc[CBECS_data[glsspc_tag] == option, wght_tag].sum())
            # Choose glass percent: ********NEED TO CREATE A WINDOW ASSEMBLY AND BRING IN ************
            glsspc_choice = random.choices(glsspc_options, glsspc_weights)[0]
            if glsspc_choice == 1:
                choice2 = '1 percent or less'
            elif glsspc_choice == 2:
                choice2 = '2 to 10 percent'
            elif glsspc_choice == 3:
                choice2 = '11 to 25 percent'
            elif glsspc_choice == 4:
                choice2 = '26 to 50 percent'
            elif glsspc_choice == 5:
                choice2 = '51 to 75 percent'
            elif glsspc_choice == 6:
                choice2 = '76 to 100 percent'
            # Window type:
            win_weights = []
            for option in win_options:
                if data_yr == 2003:
                    win_weights.append(CBECS_data.loc[CBECS_data2[win_tag] == option, wght_tag].sum())
                else:
                    win_weights.append(CBECS_data.loc[CBECS_data[win_tag] == option, wght_tag].sum())
            win_choice = random.choices(win_options, win_weights)[0]
            if win_choice == 1:
                win_type = 'Single layer glass'
            elif win_choice == 2:
                win_type = 'Multi layer glass'
            elif win_choice == 3:
                win_type = 'Combination of single layer and multi-layer glass'
            elif win_choice == 4:
                win_type = 'No windows'
            # Add windows to wall elements:
            if win_choice != 4:
                for storey in parcel.hasStorey:
                    wall = storey.containsElement['Wall']
                    wall.hasSubElement = 'Window: ' + win_type
            # Additional "roof tilt" attribute for 2012 CBECS:
            if data_yr == 2012:
                rtilt_weights = []
                for option in rtilt_options:
                    rtilt_weights.append(CBECS_data.loc[CBECS_data[rtilt_tag] == option, wght_tag].sum())
                # Choose roof tilt:
                rtilt_choice = random.choices(rtilt_options, rtilt_weights)[0]
                if rtilt_choice == 1:
                    roof_storey.containsElement['Roof'].hasPitch = 'Flat'
                elif rtilt_choice == 2:
                    roof_storey.containsElement['Roof'].hasPitch = 'Shallow pitch'
                elif rtilt_choice == 3:
                    roof_storey.containsElement['Roof'].hasPitch = 'Steeper pitch'
            else:
                pass
        else:
            pass



#Let's play with the file:
#test = Parcel('12345', 5, 'Hotel', 2002, "801 10th CT E Panama City 32401",'3200')
#b = NatlSurveyData(test)
