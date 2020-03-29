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

# test = parcel ('12345', 5, 'Hotel', 2002, 14, 15, "FL Panhandle")
# test2 = bldg_code(test)
