from parcel import Parcel

class NatlSurveyData:

    def __init__(self, parcel):
        # Check what survey this parcel needs data from:
        if parcel.is_comm:
            self.survey = 'CBECS'
        else:
            self.survey = 'RECS - currently not supported'

        print(self.survey)

        # Determine the census division for the CBECS and RECS surveys:
        if self.survey == 'CBECS' or 'RECS':
            self.census_division(parcel)

        #Now call the function that populates building attributes using the CBECS:
        if self.survey == 'CBECS':
            self.CBECS(parcel)


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


    def CBECS(self, parcel):
        if parcel.yr_built > 2012 and parcel.yr_built <= 2018:
            self.data_yr = 2018
        elif parcel.yr_built <= 2012 and parcel.yr_built > 2003:
            self.data_yr = 2012
        elif parcel.yr_built <= 2003 and parcel.yr_built > 1999:
            self.data_yr = 2003
        elif parcel.yr_built <= 1999 and parcel.yr_built > 1995:
            self.data_yr = 1999
        elif parcel.yr_built <= 1995 & parcel.yr_built > 1992:
            self.data_yr = 1995
        elif parcel.yr_built <= 1992 & parcel.yr_built > 1989:
            self.data_yr = 1992
        elif parcel.yr_built <= 1989 & parcel.yr_built > 1986:
            self.data_yr = 1989
        elif parcel.yr_built <= 1986 & parcel.yr_built > 1983:
            self.data_yr = 1986
        elif parcel.yr_built <= 1983 & parcel.yr_built > 1979:
            self.data_yr = 1983
        elif parcel.yr_built <= 1979:
            self.data_yr = 1979
        print(self.survey, self.data_yr)

#Let's play with the file:
test = Parcel('12345', 5, 'Hotel', 2002, "801 10th CT E Panama City 32401",'3200')
b = NatlSurveyData(test)
