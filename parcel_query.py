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
agreeButton = browser.find_element_by_tag_name("a.btn.btn-primary.button-1")
agreeButton.click()

# For the Cedar's Crossing case study, we are interested in pulling the following parcel numbers:
# Parcels numbered between 14805-101-000 to 14805-191-000 AND 14876-501-000 to 14876-614-000
parcel_list = []

for num in range(10, 99):
    parcel_list.append('04103-0' + str(num) + '-000')

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
for parcel in range(0, len(parcel_list)):
    # Parcel Summary page - We can now parse the parcel details
    parcelSoup = BeautifulSoup(browser.page_source, "html.parser")
    table = parcelSoup.find_all('table')
    table1 = table[0]
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
    else:
        table2 = table[2]

        for row in table2.find_all('tr'):
            columns = row.find_all('td')
            tag = row.get_text().splitlines()[1]
            value = columns[0].get_text()
            if 'Total Area' in tag:
                sq_ft = value.splitlines()[1]
            elif 'Stories' in tag:
                stories = value.splitlines()[1]
            elif 'Actual Year Built' in tag:
                yr_built = value.splitlines()[1]
            elif 'Type' in tag:
                occ_type = value.splitlines()[1]
            elif 'Exterior Walls' in tag:
                ewall_type = value.splitlines()[1]
            elif 'Roof Cover' in tag:
                rcover_type = value.splitlines()[1]
            elif 'Interior Walls' in tag:
                iwall_type = value.splitlines()[1]
            elif 'Frame Type' in tag:
                ftype = value.splitlines()[1]
            elif 'Floor Cover' in tag:
                fcover_type = value.splitlines()[1]

    with open('CommParcels.csv', 'a', newline = '') as csvfile:
        fieldnames = ['Parcel Id', 'Address', 'Use Code', 'Square Footage', 'Stories', 'Year Built', 'OccType', 'Exterior Walls', 'Roof Cover', 'Interior Walls', 'Frame Type', 'Floor Cover']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writerow({'Parcel Id': parcel_id, 'Address': address, 'Use Code': use_code, 'Square Footage': sq_ft, 'Stories': stories, 'Year Built': yr_built, 'OccType': occ_type, 'Exterior Walls': ewall_type, 'Roof Cover': rcover_type, 'Interior Walls': iwall_type, 'Frame Type': ftype, 'Floor Cover': fcover_type})

    # Move on to the next parcel or stop once we have gone through all of the parcels:
    if parcel_id != parcel_list[-1]:
        # Going to next page in the search results
        nextButton = browser.find_element_by_tag_name("span.glyphicon.glyphicon-arrow-right")
        nextButton.click()
    else:
        print('Query complete')

