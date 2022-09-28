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


df = pd.read_csv('D:/Users/Karen/Documents/GitHub/DPBWE/MB_Building_Inventory_BayCounty.csv')
replace_years = []
for idx in df.index.to_list():
    roof_replace_year = get_roof_replacement(df['permit_description'][idx], df['permit_issue_date'][idx], df['YearBuilt'][idx])
    replace_years.append(roof_replace_year)
df['RoofReplaceYear'] = replace_years
df.to_csv('D:/Users/Karen/Documents/GitHub/DPBWE/MB_Building_Inventory_BayCounty_Permits.csv', index=False)
