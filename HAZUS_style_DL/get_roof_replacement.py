import pandas as pd


def get_roof_replacement(permit_description, permit_issue_date, bldg_yrbuilt):
    if len(permit_issue_date) > 0:
        pdesc = permit_description[2:-2].split("'")
        pyear = permit_issue_date[2:-2].split("'")
        replace_list = [bldg_yrbuilt]  # default value
        for p in range(0, len(pdesc)):
            if pdesc[p].upper() == 'ROOF':
                new_year = int(pyear[p][:4])
                if bldg_yrbuilt < new_year < 2018:
                    replace_list.append(new_year)
            else:
                pass
        roof_replace_year = max(replace_list)
    return roof_replace_year


def get_reroof(permit_description, permit_issue_date, bldg_yrbuilt):
    if len(permit_issue_date) > 0:
        pdesc = permit_description[2:-2].split("'")
        pyear = permit_issue_date[2:-2].split("'")
        reroof_list = [bldg_yrbuilt]  # default value
        for p in range(0, len(pdesc)):
            if 'ROOF' in pdesc[p].upper():
                new_year = int(pyear[p][:4])
            elif 'RERF' in pdesc[p].upper():
                new_year = int(pyear[p][:4])
            else:
                new_year = bldg_yrbuilt
            if bldg_yrbuilt < new_year < 2018:
                reroof_list.append(new_year)
            else:
                pass
        reroof_year = max(reroof_list)
    return reroof_year


# Uncomment below to populate roof replace year:
# df = pd.read_csv('D:/Users/Karen/Documents/GitHub/DPBWE/HAZUS_style_DL/PCB_Building_Inventory.csv')
# replace_years = []
# for idx in df.index.to_list():
#     roof_replace_year = get_roof_replacement(df['permit_description'][idx], df['permit_issue_date'][idx], df['YearBuilt'][idx])
#     replace_years.append(roof_replace_year)
# df['RoofReplaceYear'] = replace_years
# df.to_csv('D:/Users/Karen/Documents/GitHub/DPBWE/HAZUS_style_DL/PCB_Building_Inventory_Permit.csv', index=False)

# Uncomment below to populate re-roof year:
df = pd.read_csv('D:/Users/Karen/Documents/GitHub/DPBWE/A9_Buildings.csv')
reroof_years = []
for idx in df.index.to_list():
    reroof_year = get_reroof(df['permit_description'][idx], df['permit_issue_date'][idx], df['YearBuilt'][idx])
    reroof_years.append(reroof_year)
df['ReRoofYear'] = reroof_years
df.to_csv('D:/Users/Karen/Documents/GitHub/DPBWE/A9_Buildings.csv', index=False)