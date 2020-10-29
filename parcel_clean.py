import pandas as pd
import matplotlib.pyplot as plt

# Import the parcel data:
col_names = ['Parcel Id', 'Address', 'Use Code', 'Square Footage', 'Stories', 'Year Built', 'OccType', 'Exterior Walls', 'Roof Cover', 'Interior Walls', 'Frame Type', 'Floor Cover']
df = pd.read_csv('D:/Users/Karen/Documents/GitHub/DPBWE/CommParcels.csv', header=0, names=col_names)
# Step 1: Clear any repetitive parcels:
df = df.drop_duplicates()
# Step 2: Drop any single family homes, mobile homes, multi-family, and condos
sfh_indices = df[df['Use Code'] == 'SINGLE FAM (000100)'].index
df = df.drop(sfh_indices)
mh_indices = df[df['Use Code'] == 'MOBILE HOM (000200)'].index
df = df.drop(mh_indices)
mfh_indices = df[df['Use Code'] == 'MULTI-FAMI (000800)'].index
mfh_indices2 = df[df['Use Code'] == 'MULTI-FAMI (000300)'].index
df = df.drop(mfh_indices)
df = df.drop(mfh_indices2)
c_indices = df[df['Use Code'] == 'RES COMMON (000900)'].index
df = df.drop(c_indices)
# Reset the index:
df = df.reset_index(drop=True)
# Step 3: Find the number of occurrences for a given column tag:
# Use Code
print('----------------Overview of Typologies in Panama City Beach and Mexico Beach:------------------')
print(df['Use Code'].value_counts())  # Stores, hotels, office bldg
# Roof cover type
print('Roof Cover type:')
print(df['Roof Cover'].value_counts())  # Modular mt, stand seam, built-up, etc.
# Number of stories
print('Number of Stories:')
story_count = df['Stories'].value_counts()  # 1, 2, 1.5, 3, 5 (12)
# Step 4: Merge the parcel permit information:
col_names2 = ['Parcel Id', 'Address', 'Permit Number']
df2 = pd.read_csv('D:/Users/Karen/Documents/GitHub/DPBWE/CommParcelsPermits.csv', header=0, names=col_names2)
df2 = df2.drop_duplicates()
df2['Permit Number'] = df2['Permit Number'].apply(eval)
# Step 5: Use the parcel number to merge the permit information:
permit_data = []
dis_permit = []
for row in range(0, len(df['Parcel Id'])):
    # Find the permit number for the given Parcel ID:
    parcel_str = df['Parcel Id'][row]
    try:
        permit_list = df2.loc[df2['Parcel Id'] == parcel_str, 'Permit Number'].values[0]
        permit_data.append(permit_list)
        # Check if a disaster permit is available:
        for permit in permit_list:
            if 'DIS' in permit:
                dis_flag = True
                break
            else:
                dis_flag = False
        dis_permit.append(dis_flag)
    except:
        permit_data.append('N/A')
        dis_permit.append(False)
df['Permit Number'] = permit_data
df['Disaster Permit'] = dis_permit
print(df['Disaster Permit'].value_counts())
# Step 6: Bring in the Permit Subtypes and Permit Descriptions:
df_18 = pd.read_excel('D:/Users/Karen/Documents/GitHub/DPBWE/BayCountyMichael_Permits.xlsx', sheet_name='Sheet1')
df_19 = pd.read_excel('D:/Users/Karen/Documents/GitHub/DPBWE/BayCountyMichael_Permits.xlsx', sheet_name='Sheet2')
df_20 = pd.read_excel('D:/Users/Karen/Documents/GitHub/DPBWE/BayCountyMichael_Permits.xlsx', sheet_name='Sheet3')
# Setting up two lists: all_permit_desc and permit_desc b/c some parcels have more than one Disaster permit
dis_permit_desc = []
dis_permit_type = []
for parcel in range(0, len(df['Parcel Id'])):
    plist = df['Permit Number'][parcel]
    if plist == 'N/A':
        dis_permit_desc.append('N/A')
        dis_permit_type.append('N/A')
    else:
        permit_desc = []
        type_desc = []
        for p in plist:
            if 'DIS' in p:
                if 'DIS18' in p:
                    row = df_18.index[df_18['Permit Number'] == p].to_list()
                    desc = df_18['DESCRIPTION'][row]
                    tdesc = df_18['PERMITSUBTYPE'][row]
                elif 'DIS19' in p:
                    row = df_19.index[df_19['Permit Number'] == p].to_list()
                    desc = df_19['DESCRIPTION'][row]
                    tdesc = df_19['PERMITSUBTYPE'][row]
                elif 'DIS20' in p:
                    row = df_20.index[df_20['Permit Number'] == p].to_list()
                    desc = df_20['DESCRIPTION'][row]
                    tdesc = df_20['PERMITSUBTYPE'][row]
                permit_desc.append(desc)
                type_desc.append(tdesc)
            else:
                pass
        dis_permit_desc.append(permit_desc)
        dis_permit_type.append(type_desc)
# Add permit descriptions and subtypes
df['Disaster Permit Type'] = dis_permit_type
df['Disaster Permit Description'] = dis_permit_desc
# Step 7: Let's figure out the typologies of the buildings with permits:
damage_indices = df.index[df['Disaster Permit'] == True].to_list()
df_damage = df.loc[damage_indices]
# Reset the index:
df_damage = df_damage.reset_index(drop=True)
print('-----------------------Overview of Damaged Building Typologies-----------------------')
print('Roof Covers:')
print(df_damage['Roof Cover'].value_counts())
print('Stories:')
print(df_damage['Stories'].value_counts())
print('Frame Type:')
print(df_damage['Frame Type'].value_counts())
