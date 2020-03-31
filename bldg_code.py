# from parcel import parcel


class BldgCode:

    def __init__(self, parcel):
        # First determine what code we need to pull based off of the location and year built:
        if parcel.location == "FL Panhandle":
            if parcel.year_built > 2001 & parcel.year_built < 2004:
                self.edition = "2000 FBC"
                print(self.edition)

        # Knowing the code edition, populate this parcel's code-informed attributes:
        if self.edition == "2000 FBC":
            # Derived parcel attributes:
            parcel.h_bldg = parcel.num_stories * 7.5  # minimum ceiling height per room
            print(parcel.h_bldg)

class NationalSurveyData:

    def __init__(self, parcel):
        # Check what survey this parcel needs data from:
        if parcel.is_comm:
            self.survey = 'CBECS'
        else:
            self.survey = 'Requires nonengineered residential data'

        # Select the survey year:
        if self.survey == 'CBECS':
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

            print(self.data_yr)

# test = parcel ('12345', 5, 'Hotel', 2002, 14, 15, "FL Panhandle")
# test2 = bldg_code(test)
