from selenium import webdriver
from bs4 import BeautifulSoup
import pandas as pd
import csv


def query_parcel_info(driver_path, url, parcel_identifier, address_flag):
    # Start the browser and open property appraiser's website:
    browser = webdriver.Chrome(driver_path)
    browser.get(url)
    # Access agreement:
    agreeButton = browser.find_element_by_tag_name("a.btn.btn-primary.button-1")
    agreeButton.click()
    if address_flag:
        # Use the parcel's address to pull building data:
        parcelBox = browser.find_element_by_name("ctlBodyPane$ctl02$ctl01$txtAddress")
        parcelBox.send_keys(parcel_identifier)  # Fill "Search by Location" box:
        # Click on Search
        searchButton = browser.find_element_by_id("ctlBodyPane_ctl02_ctl01_btnSearch")
        searchButton.click()
    else:
        # Use the parcel identification number to pull building data:
        parcelBox = browser.find_element_by_name("ctlBodyPane$ctl03$ctl01$txtParcelID")
        parcelBox.send_keys(parcel_identifier)  # Fill "Search by Parcel Number" box:
        # Click on Search
        searchButton = browser.find_element_by_id("ctlBodyPane_ctl03_ctl01_btnSearch")
        searchButton.click()
    # Parcel Summary page - We can now parse the parcel details
    # Create a global dictionary to hold parcel_information:
    parcel_info = {'Parcel Id': 'N/A', 'Address': 'N/A', 'Use Code': 'N/A', 'Square Footage': 'N/A',
                   'Stories': 'N/A', 'Year Built': 'N/A', 'OccType': 'N/A',
                   'Exterior Walls': 'N/A', 'Roof Cover': 'N/A', 'Interior Walls': 'N/A',
                   'Frame Type': 'N/A', 'Floor Cover': 'N/A', 'Unit No.': 'N/A', 'Floor': 'N/A',
                   'Living Area': 'N/A', 'Number of Bedrooms': 'N/A', 'Number of Bathrooms': 'N/A',
                   'Permit Number': 'N/A'}
    parcelSoup = BeautifulSoup(browser.page_source, "html.parser")
    table = parcelSoup.find_all('table')
    table1 = table[0]  # First table provides overview of the Parcel
    for row in table1.find_all('tr'):
        tag = row.get_text().splitlines()[1]
        if tag == '':
            if 'Use Code' in row.find_all('th')[0].get_text():
               tag = row.find_all('th')[0].get_text().splitlines()[1]
        columns = row.find_all('td')
        value = columns[0].get_text()
        if 'Parcel ID' in tag:
            parcel_info['Parcel Id'] = value.splitlines()[1]
        elif 'Address' in tag:
            parcel_info['Address'] = value.splitlines()[1]
        elif 'Property Use Code' in tag:
            parcel_info['Use Code'] = value.splitlines()[1]
    # Exception cases: vacant lots and condominiums
    if 'VAC' in parcel_info['Use Code'] or ('PLAT' in parcel_info['Use Code']) or ('MISC' in parcel_info['Use Code']):
        # Check to see if there is any permit data:
        for tab in table:
            if 'Permit' in tab.find_all('tr')[0].get_text():
                permit_list = []
                count = 0
                for row in tab.find_all('tr'):
                    if count == 0:
                        count = count + 1
                    elif count > 0:
                        permit_list.append(row.get_text().splitlines()[2])
                # Save the address, parcel number, and permit numbers in a separate CSV:
                parcel_info['Permit Number'] = permit_list
    elif 'COND' in parcel_info['Use Code']:
        # Extract features for condo parcels:
        for tab in table:
            if 'Unit' in tab.find_all('tr')[0].get_text():
                # Extract values for Unit No, Floor, and Living Area:
                cvalues = tab.find_all('span')
                if len(cvalues) == 3:
                    unit_no = cvalues[0].get_text()
                    floor = cvalues[1].get_text()
                    living_area = cvalues[2].get_text()
                elif len(cvalues) == 4:
                    unit_no = cvalues[1].get_text()
                    floor = cvalues[2].get_text()
                    living_area = cvalues[3].get_text()
                parcel_info['Unit No.'] = unit_no
                parcel_info['Floor'] = floor
                parcel_info['Living Area'] = living_area
            elif 'Bed' in tab.find_all('tr')[0].get_text():
                # Extract values for Number of Bedrooms and Bathrooms and Year Built:
                cvalues2 = tab.find_all('span')
                parcel_info['Number of Bedrooms'] = cvalues2[0].get_text()
                parcel_info['Number of Bathrooms'] = cvalues2[1].get_text()
                parcel_info['Year Built'] = cvalues2[2].get_text()
            elif 'Permit' in tab.find_all('tr')[0].get_text():
                permit_list = []
                count = 0
                for row in tab.find_all('tr'):
                    if count == 0:
                        count = count + 1
                    elif count > 0:
                        permit_list.append(row.get_text().splitlines()[2])
                # Update the parcel's Permit Number field:
                parcel_info['Permit Number'] = permit_list
    else:
        # If the parcel is not a vacant lot, access all parcel attributes:
        for tab in table:
            # Figure out if there are multiple buildings in this parcel:
            table_headers = tab.find_all('tr')[0].get_text()
            bldg_count = 1
            if 'Building' in tab.find_all('tr')[0].get_text():  # Some parcels have multiple bldgs
                for row in tab.find_all('tr'):
                    columns = row.find_all('td')
                    tag = row.get_text().splitlines()[2]
                    if tag == '':
                        pass
                    else:
                        value = columns[0].get_text()
                        if 'Total Area' in tag:
                            area = value.splitlines()[1]
                        elif 'Stories' in tag:
                            stories = value.splitlines()[1]
                        elif 'Actual Year Built' in tag:
                            yr_built = value.splitlines()[1]
                        elif 'Type' in tag:
                            if 'Frame' in tag:
                                ftype = value.splitlines()[1]
                            else:
                                occ_type = value.splitlines()[1]
                        elif 'Exterior Walls' in tag:
                            ext_wall = value.splitlines()[1]
                        elif 'Roof Cover' in tag:
                            rcover = value.splitlines()[1]
                        elif 'Interior Walls' in tag:
                            int_wall = value.splitlines()[1]
                        elif 'Floor Cover' in tag:
                            fcover = value.splitlines()[1]
                bldg_dict = {'Square Footage': area, 'Stories': stories, 'Year Built': yr_built, 'Frame Type': ftype,
                             'OccType': occ_type, 'Exterior Walls': ext_wall, 'Roof Cover': rcover, 'Interior Walls': int_wall,
                             'Floor Cover': fcover}
                # Create lists of parameters in cases when there are > 1 bldgs within parcel
                if bldg_count == 1:
                    for key in bldg_dict:
                        parcel_info[key] = bldg_dict[key]
                elif bldg_count == 2:
                    for key in bldg_dict:
                        parcel_info[key] = []
                        parcel_info[key].append(bldg_dict[key])
                elif bldg_count > 2:
                    for key in bldg_dict:
                        parcel_info[key].append(bldg_dict[key])
            elif 'Permit' in tab.find_all('tr')[0].get_text():
                permit_list = []
                count = 0
                for row in tab.find_all('tr'):
                    if count == 0:
                        count = count+1
                    elif count > 0:
                        permit_list.append(row.get_text().splitlines()[2])
                # Save the address, parcel number, and permit numbers in a separate CSV:
                parcel_info['Permit Number'] = permit_list
            else:
                pass
    # Close the browser:
    browser.quit()
    return parcel_info


def query_parcel_info_2(driver_path, url, parcel_identifier, address_flag):
    # Start the browser and open property appraiser's website:
    browser = webdriver.Chrome(driver_path)
    browser.get(url)
    # Access agreement:
    agreeButton = browser.find_element_by_tag_name("a.btn.btn-primary.button-1")
    agreeButton.click()
    if address_flag:
        # Use the parcel's address to pull building data:
        parcelBox = browser.find_element_by_name("ctlBodyPane$ctl02$ctl01$txtAddress")
        parcelBox.send_keys(parcel_identifier)  # Fill "Search by Location" box:
        # Click on Search
        searchButton = browser.find_element_by_id("ctlBodyPane_ctl02_ctl01_btnSearch")
        searchButton.click()
    else:
        # Use the parcel identification number to pull building data:
        parcelBox = browser.find_element_by_name("ctlBodyPane$ctl03$ctl01$txtParcelID")
        parcelBox.send_keys(parcel_identifier)  # Fill "Search by Parcel Number" box:
        # Click on Search
        searchButton = browser.find_element_by_id("ctlBodyPane_ctl03_ctl01_btnSearch")
        searchButton.click()
    # Parcel Summary page - We can now parse the parcel details
    # Create a global dictionary to hold parcel_information:
    parcel_info = {'Parcel Id': None, 'Address': None, 'Use Code': None, 'Building Value': None, 'Just Market Value': None, 'Permit Number': None, 'Building Data': {'Square Footage': [],
                   'Stories': [], 'Year Built': [], 'OccType': [],
                   'Exterior Walls': [], 'Roof Cover': [], 'Interior Walls': [],
                   'Frame Type': [], 'Floor Cover': [], 'Unit No.': None, 'Floor': None,
                   'Living Area': None, 'Number of Bedrooms': None, 'Number of Bathrooms': None}}
    parcelSoup = BeautifulSoup(browser.page_source, "html.parser")
    table = parcelSoup.find_all('table')
    table1 = table[0]  # First table provides overview of the Parcel
    for row in table1.find_all('tr'):
        tag = row.get_text().splitlines()[1]
        if tag == '':
            if 'Use Code' in row.find_all('th')[0].get_text():
               tag = row.find_all('th')[0].get_text().splitlines()[1]
        columns = row.find_all('td')
        value = columns[0].get_text()
        if 'Parcel ID' in tag:
            parcel_info['Parcel Id'] = value.splitlines()[1]
        elif 'Address' in tag:
            parcel_info['Address'] = value.splitlines()[1]
        elif 'Property Use Code' in tag:
            parcel_info['Use Code'] = value.splitlines()[1]
    # Property value information:
    prop_values = table[1].get_text().split('\n')
    # Building value and just market value:
    for i in prop_values:
        if 'Building Value' in i:
            sub_str = i.split('$')
            parcel_info['Building Value'] = sub_str[-1].replace(',','')
        elif 'Just' in i:
            sub_str = i.split('$')
            parcel_info['Just Market Value'] = sub_str[-1].replace(',','')
        else:
            pass
    # Exception cases: vacant lots and condominiums
    if 'VAC' in parcel_info['Use Code'] or ('PLAT' in parcel_info['Use Code']) or ('MISC' in parcel_info['Use Code']):
        # Check to see if there is any permit data:
        for tab in table:
            if 'Permit' in tab.find_all('tr')[0].get_text():
                permit_list = []
                count = 0
                for row in tab.find_all('tr'):
                    if count == 0:
                        count = count + 1
                    elif count > 0:
                        permit_list.append(row.get_text().splitlines()[2])
                # Save the permit information:
                parcel_info['Permit Number'] = permit_list
    elif 'COND' in parcel_info['Use Code']:
        # Extract features for condo parcels:
        for tab in table:
            if 'Unit' in tab.find_all('tr')[0].get_text():
                # Extract values for Unit No, Floor, and Living Area:
                cvalues = tab.find_all('span')
                if len(cvalues) == 3:
                    unit_no = cvalues[0].get_text()
                    floor = cvalues[1].get_text()
                    living_area = cvalues[2].get_text()
                elif len(cvalues) == 4:
                    unit_no = cvalues[1].get_text()
                    floor = cvalues[2].get_text()
                    living_area = cvalues[3].get_text()
                parcel_info['Building Data']['Unit No.'] = unit_no
                parcel_info['Building Data']['Floor'] = floor
                parcel_info['Building Data']['Living Area'] = living_area
            elif 'Bed' in tab.find_all('tr')[0].get_text():
                # Extract values for Number of Bedrooms and Bathrooms and Year Built:
                cvalues2 = tab.find_all('span')
                parcel_info['Building Data']['Number of Bedrooms'] = cvalues2[0].get_text()
                parcel_info['Building Data']['Number of Bathrooms'] = cvalues2[1].get_text()
                parcel_info['Building Data']['Year Built'] = cvalues2[2].get_text()
            elif 'Permit' in tab.find_all('tr')[0].get_text():
                permit_list = []
                count = 0
                for row in tab.find_all('tr'):
                    if count == 0:
                        count = count + 1
                    elif count > 0:
                        permit_list.append(row.get_text().splitlines()[2])
                # Update the parcel's Permit Number field:
                parcel_info['Permit Number'] = permit_list
    else:
        # If the parcel is not a vacant lot, access all parcel attributes:
        for tab in table:
            if 'Building' in tab.find_all('tr')[0].get_text():
                for row in tab.find_all('tr'):
                    columns = row.find_all('td')
                    tag = row.get_text().splitlines()[2]
                    if tag == '':
                        pass
                    else:
                        value = columns[0].get_text()
                        if 'Total Area' in tag:
                            parcel_info['Building Data']['Square Footage'].append(value.splitlines()[1])
                        elif 'Stories' in tag:
                            parcel_info['Building Data']['Stories'].append(value.splitlines()[1])
                        elif 'Actual Year Built' in tag:
                            parcel_info['Building Data']['Year Built'].append(value.splitlines()[1])
                        elif 'Type' in tag:
                            if 'Frame' in tag:
                                parcel_info['Building Data']['Frame Type'].append(value.splitlines()[1])
                            else:
                                parcel_info['Building Data']['OccType'].append(value.splitlines()[1])
                        elif 'Exterior Walls' in tag:
                            parcel_info['Building Data']['Exterior Walls'].append(value.splitlines()[1])
                        elif 'Roof Cover' in tag:
                            parcel_info['Building Data']['Roof Cover'].append(value.splitlines()[1])
                        elif 'Interior Walls' in tag:
                            parcel_info['Building Data']['Interior Walls'].append(value.splitlines()[1])
                        elif 'Floor Cover' in tag:
                            parcel_info['Building Data']['Floor Cover'].append(value.splitlines()[1])
            elif 'Permit' in tab.find_all('tr')[0].get_text():
                permit_list = []
                count = 0
                for row in tab.find_all('tr'):
                    if count == 0:
                        count = count+1
                    elif count > 0:
                        permit_list.append(row.get_text().splitlines()[2])
                # Save the address, parcel number, and permit numbers in a separate CSV:
                parcel_info['Permit Number'] = permit_list
            else:
                pass
    # Close the browser:
    browser.quit()
    return parcel_info

# Play with this:
driver_path = 'C:/Users/Karen/Desktop/chromedriver.exe'
url = "https://qpublic.schneidercorp.com/application.aspx?app=BayCountyFL&PageType=Search"
address_flag = False
df = pd.read_csv('C:/Users/Karen/Desktop/BayCountyCommercial.csv')
for row in range(0, len(df['Parcel ID'])):
    parcel_identifier = df['Parcel ID'][row]
    parcel_info = query_parcel_info_2(driver_path, url, parcel_identifier, address_flag)
    # Save the building's data:
    for bldg in range(0, len(parcel_info['Building Data']['Stories'])):
        with open('BayCountyCommercialParcels.csv', 'a', newline='') as csvfile:
            fieldnames = ['Parcel Id', 'Address', 'Use Code', 'Square Footage', 'Stories', 'Year Built', 'OccType',
                          'Exterior Walls', 'Roof Cover', 'Interior Walls', 'Frame Type', 'Floor Cover', 'Unit No.', 'Floor',
                          'Living Area', 'Number of Bedrooms', 'Number of Bathrooms', 'Permit Number']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writerow(
                {'Parcel Id': parcel_info['Parcel Id'], 'Address': parcel_info['Address'], 'Use Code': parcel_info['Use Code'],
                'Square Footage': parcel_info['Building Data']['Square Footage'][bldg], 'Stories': parcel_info['Building Data']['Stories'][bldg],
                'Year Built': parcel_info['Building Data']['Year Built'][bldg], 'OccType': parcel_info['Building Data']['OccType'][bldg],
                'Exterior Walls': parcel_info['Building Data']['Exterior Walls'][bldg], 'Roof Cover': parcel_info['Building Data']['Roof Cover'][bldg],
                'Interior Walls': parcel_info['Building Data']['Interior Walls'][bldg], 'Frame Type': parcel_info['Building Data']['Frame Type'][bldg],
                'Floor Cover': parcel_info['Building Data']['Floor Cover'][bldg], 'Unit No.': parcel_info['Building Data']['Unit No.'],
                'Floor': parcel_info['Building Data']['Floor'], 'Living Area': parcel_info['Building Data']['Living Area'],
                'Number of Bedrooms': parcel_info['Building Data']['Number of Bedrooms'], 'Number of Bathrooms': parcel_info['Building Data']['Number of Bathrooms'],
                'Permit Number': parcel_info['Permit Number']})