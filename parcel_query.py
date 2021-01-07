import sys
import os
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from bs4 import BeautifulSoup
import csv

# Starting the browser and opening tax assessor's data website for the Florida Bay County
browser = webdriver.Chrome('C:/Users/Karen/Desktop/chromedriver.exe')
url = "https://qpublic.schneidercorp.com/application.aspx?app=BayCountyFL&PageType=Search"
browser.get(url)

# Access agreement:
#wait = WebDriverWait(browser, 10)
agreeButton = browser.find_element_by_tag_name("a.btn.btn-primary.button-1")
agreeButton.click()

# For the Cedar's Crossing case study, we are interested in pulling the following parcel numbers:
# Parcels numbered between 14805-101-000 to 14805-191-000 AND 14876-501-000 to 14876-614-000
parcel_list = []

for num in range(0, 85):
    parcel_list.append('33320-100-00' + str(num))

# for num2 in range(501,615):
    # parcel_list.append('14876-' + str(num2) + '-000')

# Get started with the first parcel and click through the rest:
# Fill "Search by Parcel Number" box:
parcelBox = browser.find_element_by_name("ctlBodyPane$ctl03$ctl01$txtParcelID")
parcelBox.send_keys(parcel_list[0])
# Click on Search
searchButton = browser.find_element_by_id("ctlBodyPane_ctl03_ctl01_btnSearch")
searchButton.click()

# Create an empty list to hold all of our information:
data_list = []

# Pulling information for each parcel
print(len(parcel_list)) #38
for parcel in range(0, len(parcel_list)):
    # Parcel Summary page - We can now parse the parcel details
    parcelSoup = BeautifulSoup(browser.page_source, "html.parser")
    table = parcelSoup.find_all('table')
    #try:
     #   table1 = table[0]
      #  table1.get_text()
    #except:
     #   table1 = table[1]
    table1 = table[0]  # First table provides overview of the Parcel
    for row in table1.find_all('tr'):
        tag = row.get_text().splitlines()[1]
        if tag == '':
            if 'Use Code' in row.find_all('th')[0].get_text():
               tag = row.find_all('th')[0].get_text().splitlines()[1]
        columns = row.find_all('td')
        #tag = columns[0].get_text()
        value = columns[0].get_text()
        if 'Parcel ID' in tag:
            parcel_id = value.splitlines()[1]
        elif 'Address' in tag:
            address = value.splitlines()[1]
        elif 'Property Use Code' in tag:
            use_code = value.splitlines()[1]

    if 'VAC' in use_code:
        sq_ft = 'N/A'
        stories = 'N/A'
        yr_built = 'N/A'
        occ_type = 'N/A'
        ewall_type = 'N/A'
        rcover_type = 'N/A'
        iwall_type = 'N/A'
        ftype = 'N/A'
        fcover_type = 'N/A'
        # Save the parcel:
        with open('CommParcels.csv', 'a', newline='') as csvfile:
            fieldnames = ['Parcel Id', 'Address', 'Use Code', 'Square Footage', 'Stories', 'Year Built', 'OccType',
                          'Exterior Walls', 'Roof Cover', 'Interior Walls', 'Frame Type', 'Floor Cover']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writerow({'Parcel Id': parcel_id, 'Address': address, 'Use Code': use_code, 'Square Footage': sq_ft,
                             'Stories': stories, 'Year Built': yr_built, 'OccType': occ_type,
                             'Exterior Walls': ewall_type, 'Roof Cover': rcover_type, 'Interior Walls': iwall_type,
                             'Frame Type': ftype, 'Floor Cover': fcover_type})
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
                with open('CommParcelsPermits.csv', 'a', newline='') as csvfile:
                    fieldnames = ['Parcel Id', 'Address', 'Permit Number']
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writerow(
                        {'Parcel Id': parcel_id, 'Address': address, 'Permit Number': permit_list})
    elif 'COND' in use_code:
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
            elif 'Bed' in tab.find_all('tr')[0].get_text():
                # Extract values for Number of Bedrooms and Bathrooms and Year Built:
                cvalues2 = tab.find_all('span')
                num_bed = cvalues2[0].get_text()
                num_bath = cvalues2[1].get_text()
                yr_built = cvalues2[2].get_text()
            elif 'Permit' in tab.find_all('tr')[0].get_text():
                permit_list = []
                count = 0
                for row in tab.find_all('tr'):
                    if count == 0:
                        count = count + 1
                    elif count > 0:
                        permit_list.append(row.get_text().splitlines()[2])
                # Save the address, parcel number, and permit numbers in a separate CSV:
                with open('CondoParcelsPermits.csv', 'a', newline='') as csvfile:
                    fieldnames = ['Parcel Id', 'Address', 'Permit Number']
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writerow(
                        {'Parcel Id': parcel_id, 'Address': address, 'Permit Number': permit_list})
        # Save the condo feature information:
        with open('CondoParcels.csv', 'a', newline='') as csvfile:
            fieldnames = ['Parcel Id', 'Address', 'Use Code', 'Unit No.', 'Floor', 'Living Area', 'Number of Bedrooms', 'Number of Bathrooms', 'Year Built']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writerow({'Parcel Id': parcel_id, 'Address': address, 'Use Code': use_code, 'Unit No.': unit_no, 'Floor': floor, 'Living Area': living_area, 'Number of Bedrooms': num_bed, 'Number of Bathrooms': num_bath, 'Year Built': yr_built})
    else:
        # If the parcel is not a vacant lot, access all parcel attributes:
        bldg_flag = False
        for tab in table:
            if 'Building' in tab.find_all('tr')[0].get_text():  # Some parcels have multiple bldgs
                bldg_flag = True
                for row in tab.find_all('tr'):
                    columns = row.find_all('td')
                    tag = row.get_text().splitlines()[2]
                    if tag == '':
                        sq_ft = 'N/A'
                        stories = 'N/A'
                        yr_built = 'N/A'
                        occ_type = 'N/A'
                        ewall_type = 'N/A'
                        rcover_type = 'N/A'
                        iwall_type = 'N/A'
                        ftype = 'N/A'
                        fcover_type = 'N/A'
                    else:
                        value = columns[0].get_text()
                        if 'Total Area' in tag:
                            sq_ft = value.splitlines()[1]
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
                            ewall_type = value.splitlines()[1]
                        elif 'Roof Cover' in tag:
                            rcover_type = value.splitlines()[1]
                        elif 'Interior Walls' in tag:
                            iwall_type = value.splitlines()[1]
                        elif 'Floor Cover' in tag:
                            fcover_type = value.splitlines()[1]
                    # Save the building and parcel information:
                with open('CommParcels.csv', 'a', newline='') as csvfile:
                    fieldnames = ['Parcel Id', 'Address', 'Use Code', 'Square Footage', 'Stories', 'Year Built', 'OccType', 'Exterior Walls', 'Roof Cover', 'Interior Walls', 'Frame Type','Floor Cover']
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writerow({'Parcel Id': parcel_id, 'Address': address, 'Use Code': use_code, 'Square Footage': sq_ft,
                             'Stories': stories, 'Year Built': yr_built, 'OccType': occ_type,
                             'Exterior Walls': ewall_type, 'Roof Cover': rcover_type, 'Interior Walls': iwall_type,
                             'Frame Type': ftype, 'Floor Cover': fcover_type})
            elif 'Permit' in tab.find_all('tr')[0].get_text():
                permit_list = []
                count = 0
                for row in tab.find_all('tr'):
                    if count == 0:
                        count = count+1
                    elif count > 0:
                        permit_list.append(row.get_text().splitlines()[2])
                # Save the address, parcel number, and permit numbers in a separate CSV:
                with open('CommParcelsPermits.csv', 'a', newline='') as csvfile:
                    fieldnames = ['Parcel Id', 'Address', 'Permit Number']
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writerow(
                        {'Parcel Id': parcel_id, 'Address': address, 'Permit Number': permit_list})
            else:
                pass
        if not bldg_flag:
            # Create dummy data for Parcels without 'VAC' in use code
            sq_ft = 'N/A'
            stories = 'N/A'
            yr_built = 'N/A'
            occ_type = 'N/A'
            ewall_type = 'N/A'
            rcover_type = 'N/A'
            iwall_type = 'N/A'
            ftype = 'N/A'
            fcover_type = 'N/A'
            with open('CommParcels.csv', 'a', newline='') as csvfile:
                fieldnames = ['Parcel Id', 'Address', 'Use Code', 'Square Footage', 'Stories', 'Year Built', 'OccType',
                              'Exterior Walls', 'Roof Cover', 'Interior Walls', 'Frame Type', 'Floor Cover']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writerow(
                    {'Parcel Id': parcel_id, 'Address': address, 'Use Code': use_code, 'Square Footage': sq_ft,
                     'Stories': stories, 'Year Built': yr_built, 'OccType': occ_type,
                     'Exterior Walls': ewall_type, 'Roof Cover': rcover_type, 'Interior Walls': iwall_type,
                     'Frame Type': ftype, 'Floor Cover': fcover_type})
        else:
            pass
    # Move on to the next parcel or stop once we have gone through all of the parcels:
    if parcel_id != parcel_list[-1]:
        # Going to next page in the search results
        nextButton = browser.find_element_by_tag_name("span.glyphicon.glyphicon-arrow-right")
        nextButton.click()
    else:
        print('Query complete')

