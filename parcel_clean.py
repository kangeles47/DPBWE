import pandas as pd
import ast


# Step 1: Import the Commercial Building parcel data and clean the data:
col_names = ['Parcel ID', 'Address', 'Use Code', 'Square Footage', 'Stories', 'Year Built', 'OccType', 'Exterior Walls', 'Roof Cover', 'Interior Walls', 'Frame Type', 'Floor Cover']
df = pd.read_csv('C:/Users/Karen/PycharmProjects/DPBWE/CommParcels.csv', header=0, names=col_names)
df = df.drop_duplicates()  # Clear any repetitive parcels:
sfh_indices = df[df['Use Code'] == 'SINGLE FAM (000100)'].index
df = df.drop(sfh_indices)  # Drop any single family homes
mh_indices = df[df['Use Code'] == 'MOBILE HOM (000200)'].index
df = df.drop(mh_indices)  # Drop any mobile homes
mfh_indices = df[df['Use Code'] == 'MULTI-FAMI (000800)'].index
mfh_indices2 = df[df['Use Code'] == 'MULTI-FAMI (000300)'].index
df = df.drop(mfh_indices)
df = df.drop(mfh_indices2)  # Drop all instances of multi-family complexes
df = df.reset_index(drop=True)  # Reset the index for the DataFrame
sqf_list = []
for sqf in df['Square Footage']:
    try:
        sqf_list.append(float(sqf.replace(',', '')))
    except:
        sqf_list.append(sqf)
df['Square Footage'] = sqf_list
# Fix stories designations:
for row in range(0, len(df['Stories'])):
    if df['Stories'][row] == 0:
        df.at[row, 'Stories'] = 0
    else:
        pass
# Step 2: Load and merge the condo parcel data:
col_cnames = ['Parcel ID', 'Address', 'Use Code', 'Unit No.', 'Floor', 'Living Area', 'Number of Bedrooms', 'Number of Bathrooms', 'Year Built']
df_condo = pd.read_csv('C:/Users/Karen/PycharmProjects/DPBWE/CondoParcels.csv', header=0, names=col_cnames)
df_condo = df_condo.drop_duplicates()  # Clear any repetitive parcels
df_condo = df_condo.reset_index(drop=True)  # Reset the index for the DataFrame
df_full = pd.concat([df, df_condo], axis=0, ignore_index=True)  # Merge condo parcels with commercial parcel data
# Step 3: Link individual condo units to their "home parcel" - Valid for units within a tower
# Use condo addresses to establish a set of condo bldg addresses:
cbldg_addresses = []
for cond in range(0, len(df_condo['Parcel ID'])):
    address = df_condo['Address'][cond].split()[0:2]
    if cond == 0:
        condo_bldg_address = address
        cbldg_addresses.append(address)
    else:
        if address == condo_bldg_address:
            pass
        else:
            condo_bldg_address = address
            cbldg_addresses.append(address)
# Get the indices for all potential condo buildings:
cbldg_indices = df_full[(df_full['Use Code'] == 'PLAT HEADI (H.)') | (df_full['Use Code'] == 'RES COMMON (000900)')].index.to_list()
# Match condo units to their buildings:
cbldg = []
for idx in range(0, len(df_full['Parcel ID'])):
    if 'COND' in df_full['Use Code'][idx]:
        address = df_full['Address'][idx].split()[0:2]
        condo_id = df_full['Parcel ID'][idx].split('-')
        # Loop through all condo buildings and collect potential parcel numbers:
        pbldg_list = []
        for j in cbldg_indices:
            if df_full['Address'][j].split()[0:2] == address:
                pbldg_list.append(df_full['Parcel ID'][j])
            else:
                pass
        # Determine the appropriate condo building for the unit:
        if len(pbldg_list) == 1:
            cbldg.append(pbldg_list[0])
        elif len(pbldg_list) > 1:
            bldg_ids = {0: [], 1:[], 2:[]}  # Parcel numbers consist of three sets of numbers
            for bldg in pbldg_list:
                pid = bldg.split('-')
                bldg_ids[0].append(pid[0])
                bldg_ids[1].append(pid[1])
                bldg_ids[2].append(pid[2])
            # Individual condo units have larger parcel numbers than the tower they belong to:
            if len(set(bldg_ids[0])) == 1 and len(set(bldg_ids[1])) > 1:
                # Get the index of the bldg parcel closest (and smaller) than condo unit:
                for i in range(0, len(bldg_ids[1])):
                    if i == 0:
                        start_num = int(bldg_ids[1][i])
                        cparcel = pbldg_list[i]
                    else:
                        new_num = int(bldg_ids[1][i])
                        if start_num < new_num < int(condo_id[1]):
                            cparcel = pbldg_list[i]
                        else:
                            pass
                cbldg.append(cparcel)
            elif len(set(bldg_ids[0])) == 1 and len(set(bldg_ids[1])) == 1:
                # Get the index of the bldg parcel closest (and smaller) than condo unit:
                for i in range(0, len(bldg_ids[2])):
                    if i == 0:
                        start_num = int(bldg_ids[2][i])
                        cparcel = pbldg_list[i]
                    else:
                        new_num = int(bldg_ids[2][i])
                        if start_num < new_num < int(condo_id[2]):
                            cparcel = pbldg_list[i]
                        else:
                            pass
                cbldg.append(cparcel)
        else:
            #print(condo_id)
            cbldg.append('N/A')
    else:
        cbldg.append('N/A')
df_full['Condo Bldg'] = cbldg
# Add dummy values to square footage and stories for condo buildings
for i in cbldg_indices:
    df_full['Square Footage'][i] = 0
    df_full['Stories'][i] = 0
# Extract condos indices:
condo_indices = df_full[df_full['Use Code'] == 'CONDOMINIU (000400)'].index.to_list()
# Add condo unit living area and floor information to condo building:
for c in condo_indices:
    # Find the condo's respective building:
    try:
        bldg_idx = df_full[df_full['Parcel ID'] == df_full['Condo Bldg'][c]].index.to_list()[0]
    except:
        print('Condos without a home building:')
        print(df_full['Parcel ID'][c])
    # Update the condo building's square footage:
    df_full['Square Footage'][bldg_idx] = df_full['Square Footage'][bldg_idx] + df_full['Living Area'][c]
    # Update the condo building's story information:
    if df_full['Stories'][bldg_idx] < df_full['Floor'][c]:
        df_full['Stories'][bldg_idx] = df_full['Floor'][c]
    else:
        pass
# Step 4: Print an overview of the typologies in df_full:
print_flag = False
if print_flag:
    # Use Code
    print('----------------Overview of Typologies in Panama City Beach and Mexico Beach:------------------')
    print(df_full['Use Code'].value_counts())  # Stores, hotels, office bldg
    # Roof cover type
    print('Roof Cover type:')
    print(df_full['Roof Cover'].value_counts())  # Modular mt, stand seam, built-up, etc.
    # Number of stories
    print('Number of Stories:')
    print(df_full['Stories'].value_counts()) # 1, 2, 1.5, 3, 5 (12)
    print('Exterior Wall Type:')
    print(df_full['Exterior Walls'].value_counts())
else:
    pass
# Step 5: Merge the parcel permit information:
# Load the Commercial parcel permit info:
col_names2 = ['Parcel ID', 'Address', 'Permit Number']
df2 = pd.read_csv('C:/Users/Karen/PycharmProjects/DPBWE/CommParcelsPermits.csv', header=0, names=col_names2)
df2 = df2.drop_duplicates()
# Load the condo parcel permit info:
df2c = pd.read_csv('C:/Users/Karen/PycharmProjects/DPBWE/CondoParcelsPermits.csv', header=0, names=col_names2)
df2c = df2c.drop_duplicates()
# Step 6: Use the parcel number to merge the permit information:
permit_data = []
dis_permit = []
for row in range(0, len(df_full['Parcel ID'])):
    # Find the permit number for the given Parcel ID:
    parcel_str = df_full['Parcel ID'][row]
    if 'COND' in df_full['Use Code'][row]:
        ref_df = df2c
    else:
        ref_df = df2
    try:
        permit_list = ast.literal_eval(ref_df.loc[ref_df['Parcel ID'] == parcel_str, 'Permit Number'].values[0])
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
# Add parcel permit data:
df_full['Permit Number'] = permit_data
df_full['Disaster Permit'] = dis_permit
# Uncomment to see how many parcels have a disaster permit:
#print(df['Disaster Permit'].value_counts())
# Step 7: Bring in the Permit Subtypes and Permit Descriptions:
df_18 = pd.read_excel('C:/Users/Karen/PycharmProjects/DPBWE/BayCountyMichael_Permits.xlsx', sheet_name='Sheet1')
df_19 = pd.read_excel('C:/Users/Karen/PycharmProjects/DPBWE/BayCountyMichael_Permits.xlsx', sheet_name='Sheet2')
df_20 = pd.read_excel('C:/Users/Karen/PycharmProjects/DPBWE/BayCountyMichael_Permits.xlsx', sheet_name='Sheet3')
# Setting up two lists: all_permit_desc and permit_desc b/c some parcels have more than one Disaster permit
dis_permit_desc = []
dis_permit_type = []
for parcel in range(0, len(df_full['Parcel ID'])):
    if not df_full['Disaster Permit'][parcel]:
        dis_permit_desc.append('N/A')
        dis_permit_type.append('N/A')
    else:
        plist = df_full['Permit Number'][parcel]
        permit_desc = []
        type_desc = []
        for p in plist:
            if 'DIS' in p:
                if 'DIS18' in p:
                    row = df_18.index[df_18['Permit Number'] == p].to_list()[0]
                    desc = df_18['DESCRIPTION'][row].upper()
                    tdesc = df_18['PERMITSUBTYPE'][row].upper()
                elif 'DIS19' in p:
                    row = df_19.index[df_19['Permit Number'] == p].to_list()[0]
                    desc = df_19['DESCRIPTION'][row].upper()
                    tdesc = df_19['PERMITSUBTYPE'][row].upper()
                elif 'DIS20' in p:
                    row = df_20.index[df_20['Permit Number'] == p].to_list()[0]
                    desc = df_20['DESCRIPTION'][row].upper()
                    tdesc = df_20['PERMITSUBTYPE'][row].upper()
                permit_desc.append(desc)
                type_desc.append(tdesc)
            else:
                pass
        dis_permit_desc.append(permit_desc)
        dis_permit_type.append(type_desc)
# Add permit descriptions and subtypes
df_full['Disaster Permit Type'] = dis_permit_type
df_full['Disaster Permit Description'] = dis_permit_desc
# Step 7: Overview of damaged building typologies:
damage_indices = df_full.index[df_full['Disaster Permit'] == True].to_list()
df_damage = df_full.loc[damage_indices]
# Reset the index:
df_damage = df_damage.reset_index(drop=True)
print('-----------------------Overview of Damaged Building Typologies-----------------------')
print('Roof Covers:')
print(df_damage['Roof Cover'].value_counts())
print('Stories:')
print(df_damage['Stories'].value_counts())
print('Frame Type:')
print(df_damage['Frame Type'].value_counts())
# Export the Damage DataFrame to a .csv:
df_damage.to_csv('Bay_Parcels_Permits.csv', index=False)
# Drop any parcels that are both vacant and do not have a damage permit:
vac_dam_indices = df_full.loc[(df['Use Code'] == 'VACANT COM (001000)') & (df_full['Disaster Permit'] == False)].index
vac_dam_indices2 = df_full.loc[(df['Use Code'] == 'VACANT/XFO (000070)') & (df_full['Disaster Permit'] == False)].index
vac_dam_indices3 = df_full.loc[(df['Use Code'] == 'VACANT (000000)') & (df_full['Disaster Permit'] == False)].index
vac_dam_indices4 = df_full.loc[(df['Use Code'] == 'VACANT COM (001070)') & (df_full['Disaster Permit'] == False)].index
vac_dam_indices5 = df_full.loc[(df['Use Code'] == 'PLAT HEADI (H.)') & (df_full['Disaster Permit'] == False)].index
df_full = df_full.drop(vac_dam_indices)  # Drop any vacant commercial lots without disaster permit information:
df_full = df_full.drop(vac_dam_indices2)
df_full = df_full.drop(vac_dam_indices3)
df_full = df_full.drop(vac_dam_indices4)
df_full = df_full.drop(vac_dam_indices5)
df_full.to_csv('Full_Comm_Parcels.csv', index=False)
