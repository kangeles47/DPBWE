import pandas as pd
import ast

# Step 1: Import the case study parcel data and clean the data:
df = pd.read_csv('C:/Users/Karen/Desktop/CaseStudyParcels.csv')
# mfh_indices2 = df[df['Use Code'] == 'MULTI-FAMI (000300)'].index  # > 10 units, multi-story
# df = df.drop(mfh_indices2)  # Drop all instances of multi-family complexes
# df = df.reset_index(drop=True)  # Reset the index for the DataFrame
# Get the indices for all potential condo buildings:
cbldg_indices = df[(df['Use Code'] == 'PLAT HEADI (H.)') | (df['Use Code'] == 'RES COMMON (000900)')].index.to_list()
# Match condo units to their buildings:
cbldg = []
for idx in range(0, len(df['Parcel Id'])):
    if 'COND' in df['Use Code'][idx]:
        address = df['Address'][idx].split()[0:2]
        condo_id = df['Parcel Id'][idx].split('-')
        # Loop through all condo buildings and collect potential parcel numbers:
        pbldg_list = []
        for j in cbldg_indices:
            if df['Address'][j].split()[0:2] == address:
                pbldg_list.append(df['Parcel Id'][j])
            else:
                pass
        # Determine the appropriate condo building for the unit:
        if len(pbldg_list) == 1:
            cbldg.append(pbldg_list[0])
        elif len(pbldg_list) > 1:
            bldg_ids = {0: [], 1: [], 2: []}  # Parcel numbers consist of three sets of numbers
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
            # print(condo_id)
            cbldg.append('N/A')
    else:
        cbldg.append('N/A')
df['Condo Bldg'] = cbldg
# Add dummy values to square footage and stories for condo buildings
for i in cbldg_indices:
    df['Square Footage'][i] = 0
    df['Stories'][i] = 0
# Extract condos indices:
condo_indices = df[df['Use Code'] == 'CONDOMINIU (000400)'].index.to_list()
# Add condo unit living area and floor information to condo building:
for c in condo_indices:
    # Find the condo's respective building:
    try:
        bldg_idx = df[df['Parcel Id'] == df['Condo Bldg'][c]].index.to_list()[0]
    except:
        print('Condos without a home building:')
        print(df['Parcel Id'][c])
    # Update the condo building's square footage:
    df['Square Footage'][bldg_idx] = df['Square Footage'][bldg_idx] + df['Living Area'][c]
    # Update the condo building's story information:
    if df['Stories'][bldg_idx] < df['Floor'][c]:
        df['Stories'][bldg_idx] = df['Floor'][c]
    else:
        pass
# Step 4: Print an overview of the typologies in df:
print_flag = True
if print_flag:
    # Use Code
    print('----------------Overview of Typologies in Panama City Beach and Mexico Beach:------------------')
    print(df['Use Code'].value_counts())  # Stores, hotels, office bldg
    # Roof cover type
    print('Roof Cover type:')
    print(df['Roof Cover'].value_counts())  # Modular mt, stand seam, built-up, etc.
    # Number of stories
    print('Number of Stories:')
    print(df['Stories'].value_counts())  # 1, 2, 1.5, 3, 5 (12)
    print('Exterior Wall Type:')
    print(df['Exterior Walls'].value_counts())
else:
    pass
# Step 5: Merge the parcel permit information:
# Load the Commercial parcel permit info:
col_names2 = ['Parcel Id', 'Address', 'Permit Number']
df2 = pd.read_csv('C:/Users/Karen/PycharmProjects/DPBWE/CommParcelsPermits.csv', header=0, names=col_names2)
df2 = df2.drop_duplicates()
# Load the condo parcel permit info:
df2c = pd.read_csv('C:/Users/Karen/PycharmProjects/DPBWE/CondoParcelsPermits.csv', header=0, names=col_names2)
df2c = df2c.drop_duplicates()
# Step 6: Use the parcel number to merge the permit information:
permit_data = []
dis_permit = []
for row in range(0, len(df['Parcel Id'])):
    # Find the permit number for the given Parcel Id:
    parcel_str = df['Parcel Id'][row]
    if 'COND' in df['Use Code'][row]:
        ref_df = df2c
    else:
        ref_df = df2
    try:
        permit_list = ast.literal_eval(ref_df.loc[ref_df['Parcel Id'] == parcel_str, 'Permit Number'].values[0])
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
df['Permit Number'] = permit_data
df['Disaster Permit'] = dis_permit
# Uncomment to see how many parcels have a disaster permit:
# print(df['Disaster Permit'].value_counts())
# Step 7: Bring in the Permit Subtypes and Permit Descriptions:
df_permit = pd.read_csv('C:/Users/Karen/PycharmProjects/DPBWE/BayCountyMichael_Permits.csv', encoding='unicode_escape')
# Setting up two lists: all_permit_desc and permit_desc b/c some parcels have more than one Disaster permit
dis_permit_desc = []
dis_permit_type = []
for parcel in range(0, len(df['Parcel Id'])):
    if not df['Disaster Permit'][parcel]:
        dis_permit_desc.append('N/A')
        dis_permit_type.append('N/A')
    else:
        plist = df['Permit Number'][parcel]
        permit_desc = []
        type_desc = []
        for p in plist:
            if 'DIS' in p:
                row = df_permit.index[df_permit['PERMITNUMBER'] == p].to_list()[0]
                permit_desc.append(df_permit['DESCRIPTION'][row].upper())
                type_desc.append(df_permit['PERMITSUBTYPE'][row].upper())
            else:
                pass
        dis_permit_desc.append(permit_desc)
        dis_permit_type.append(type_desc)
# Add permit descriptions and subtypes
df['Disaster Permit Type'] = dis_permit_type
df['Disaster Permit Description'] = dis_permit_desc
# Step 7: Overview of damaged building typologies:
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
# Drop any parcels that are both vacant and do not have a damage permit:
vac_dam_indices = df.loc[(df['Use Code'] == 'VACANT COM (001000)') & (df['Disaster Permit'] == False)].index
vac_dam_indices2 = df.loc[(df['Use Code'] == 'VACANT/XFO (000070)') & (df['Disaster Permit'] == False)].index
vac_dam_indices3 = df.loc[(df['Use Code'] == 'VACANT (000000)') & (df['Disaster Permit'] == False)].index
vac_dam_indices4 = df.loc[(df['Use Code'] == 'VACANT COM (001070)') & (df['Disaster Permit'] == False)].index
vac_dam_indices5 = df.loc[(df['Use Code'] == 'PLAT HEADI (H.)') & (df['Disaster Permit'] == False)].index
df = df.drop(vac_dam_indices)  # Drop any vacant commercial lots without disaster permit information:
df = df.drop(vac_dam_indices2)
df = df.drop(vac_dam_indices3)
df = df.drop(vac_dam_indices4)
df = df.drop(vac_dam_indices5)
df.to_csv('BC_CParcels.csv', index=False)
