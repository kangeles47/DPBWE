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
use_count = df['Use Code'].value_counts()  # Stores, hotels, office bldg
# Roof cover type
rcover_count = df['Roof Cover'].value_counts()  # Modular mt, stand seam, built-up, etc.
# Number of stories
story_count = df['Stories'].value_counts()  # 1, 2, 1.5, 3, 5 (12)
# Step 4: Merge the building permit data:
col_names2 = ['Parcel Id', 'Address', 'Permit Number']
df2 = pd.read_csv('D:/Users/Karen/Documents/GitHub/DPBWE/CommParcelsPermits.csv', header=0, names=col_names2)
df2 = df2.drop_duplicates()
df2['Permit Number'] = df2['Permit Number'].apply(eval)
# Step 5: Use the parcel number to merge the permit data:
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
# Step 6: Let's figure out the typologies of the buildings with permits:
damage_indices = df.index[df['Disaster Permit'] == True].to_list()
df_damage = df.loc[damage_indices]
print(df_damage['Roof Cover'].value_counts())
print(df_damage['Stories'].value_counts())
print(df_damage['Frame Type'].value_counts())
print(df_damage['Exterior Walls'].value_counts())
plt.figure()
ax = df_damage['Roof Cover'].value_counts().plot.bar(x='Num of Stories', y='Num of Occurrences')
plt.xlabel('Roof Cover Type')
plt.ylabel('Number of Occurrences')
plt.show()
# Bring in the Permit Descriptions:
#pdata_full = pd.read_csv
