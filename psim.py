import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from code_pressures import PressureCalc

# Purpose of this code is to provide a set of methods to populate Knowledge Base of Similitude factors for pressure calculations:

# Roof MWFRS
def run_sim_rmwfrs(ref_exposure, ref_hbldg, ref_cat, wind_speed, edition, cat, use_case):
    # Use Case 1: h/L = 0.5
    # Variation 1: Same building, different wind speeds:
    # Create an instance of PressureCalc()
    pressures = PressureCalc()
    # Figure out what Use Case is being populated, populate column names for DataFrame and set up h/L, wind direction, etc.:
    if use_case == 1:
        case_col = ['Zone 1', 'Zone 2', 'Zone 3']
        length = 2 * ref_hbldg
        ratio = ref_hbldg / length
    else:
        pass
    # Fit curves for each zone for each code edition
    # Create an empty list that will hold DataFrames for each code edition:
    ed_list = list()
    for ed in edition:
        # Create a new dataframe for each edition:
        df = pd.DataFrame(columns=case_col)
        for speed in wind_speed:
            rmps = pressures.rmwfrs_capacity(speed, ref_exposure, ed, ref_hbldg, length, ratio, ref_cat)
            # Create a quick dictionary:
            zone_dict = {df.columns[i]: rmps[i] for i in range(len(rmps))}
            # Add values to Dataframe:
            df = df.append(zone_dict, ignore_index=True)
        # Add DataFrame to list:
        ed_list.append(df)
        # Plot the results:
        fig, ax = plt.subplots()
        for j in range(0, len(rmps)):
            zone_curve = ax.plot(df[case_col[j]], wind_speed, label=case_col[j])
        plt.title('Roof uplift pressures (MWFRS) for All Zones vs. Wind speed for ' + str(ref_hbldg) + ' ft')
        plt.ylabel('Wind Speed [mph]')
        plt.xlabel('Pressure [psf]')
        plt.show()
        print('percent change between zones:', df.pct_change(axis=1))
    # Next step: Fit a curve to each zone for each code edition and save to a .csv:
    df_param = pd.DataFrame(columns=df.columns)
    for dframe in ed_list:
        # Plot the results:
        # fig2, ax2 = plt.subplots()
        param_lst = list()
        for zone in range(0, len(rmps)):
            col_names = dframe.columns
            params = curve_fit(func, dframe[col_names[zone]], wind_speed)
            [a, b, c] = params[0]
            # fit_curve = ax2.plot(dframe[col_names[zone]], func(dframe[col_names[zone]], a, b, c), label='Fitted Zone '+str(zone))
            # real_curve = ax2.plot(dframe[col_names[zone]], wind_speed, label='Real Zone '+str(zone))
            # Save parameters in list:
            param_lst.append([a, b, c])
        # Create a quick dictionary:
        param_dict = {df.columns[k]: param_lst[k] for k in range(len(param_lst))}  # Pairs each key with array of [a, b, c]
        # Add parameters to DataFrame:
        df_param = df_param.append(param_dict, ignore_index=True)
        # Uncomment to show curve fit for each zone
        # ax2.legend()
        # plt.title('Roof uplift pressures (MWFRS) for all zones vs. Wind speed for'  + str(ref_hbldg) + ' ft')
        # plt.ylabel('Wind Speed [mph]')
        # plt.xlabel('Pressure [psf]')
        # plt.ylim(min(wind_speed), max(wind_speed))
        # plt.show()
    # Set the index to the corresponding code editions:
    # Add column:
    df_param['Edition'] = edition
    df_param.set_index('Edition', inplace=True)
    # Save the DataFrame to a .csv file for future reference:
    # df_param.to_csv('Roof_MWFRS_05.csv')
    # Uncomment to show pressure difference between wind speeds:
    #print('percent change in wind speed:')
    #print(df.pct_change(axis=0))
    # Uncomment to show pressure difference between zones:
    #print('percent change in pressure by zone:')
    #print(df.pct_change(axis=1))

    # Variation 2: Different building height, different wind speeds:
    # Create an empty list that will hold DataFrames for each code edition:
    edh_list = list()
    # Play with roof mwfrs:
    h_bldg = np.arange(ref_hbldg, 61, 1)
    # Goal here is to get the pressure difference between ref height and other heights for various wind speeds
    for ed in edition:
        # Set up a dataframe to compare values:
        dfh = pd.DataFrame()
        # Set up a matplotlib figure:
        # fig3, ax3 = plt.subplots()
        for h in h_bldg:
            rmps_arr = np.array([])
            for speed in wind_speed:
                rmps = pressures.rmwfrs_capacity(speed, ref_exposure, ed, h, length, ratio, cat)
                rmps_arr = np.append(rmps_arr, rmps[0])  # Zone 1 since variation across heights is the same for all zones
            # Add values to DataFrame:
            col_name = str(h) + ' ft'
            dfh[col_name] = rmps_arr
            # Plot the results:
            # ax3.plot(dfh[col_name], wind_speed, label = str(h)+ ' ft')
        # Add DataFrame to list:
        edh_list.append(dfh)
        # Plot the results:
        # ax3.legend()
        # plt.title('Roof uplift pressures (MWFRS) for Zone 1 vs. Wind speed for various heights')
        # plt.ylabel('Wind Speed [mph]')
        # plt.xlabel('Pressure [psf]')
        # plt.ylim(90, max(wind_speed))
        # plt.show()
        # Uncomment to show the percent change in pressure between heights:
        print('Percent change in pressure between heights:', ed, dfh.pct_change(axis=1))
    # Calculate the percent change in pressure (compared to reference building height):
    df_hfactor = pd.DataFrame()
    row = dfh.iloc[0]  # Only need one since variation with height is same for all codes
    for index in range(0, len(row)):
        if index == 0:
            factor = 1.0
        elif row[index] == row[0]:
            factor = 1.0
        else:
            factor = (row[index] - row[0]) / row[0]
        hcol_name = dfh.columns[index]
        df_hfactor[hcol_name] = np.array([factor])
    # Save the DataFrame to a .csv file for future reference:
    # df_hfactor.to_csv('Roof_MWFRS_h.csv')

    # Variation 2: Different building height, different wind speeds, different exposures:
    exposures = ['B', 'C', 'D']
    # Set up an empty list to store the dataframes:
    exp_list = list()

    for ed in edition:
        # Set up DataFrame to save pressure difference across exposure categories for various heights:
        df_Efactor = pd.DataFrame(columns=exposures)
        for h in h_bldg:
            dfE = pd.DataFrame()
            # fig4, ax4 = plt.subplots()
            for exp in exposures:
                rmps_arr = np.array([])
                for speed in wind_speed:
                    rmps = pressures.rmwfrs_capacity(speed, exp, ed, h, length, ratio, cat)
                    rmps_arr = np.append(rmps_arr, rmps[1])
                # Add values to DataFrame:
                dfE[exp] = rmps_arr
                # Plot the results (Exposures B, C, D for one height:
                # ax4.plot(dfE[exp], wind_speed, label=exp)
            # Plot the results:
            # ax4.legend()
            # plt.title('Roof uplift pressures (MWFRS, Zone 1) and h = '+str(h)+ ' ft')
            # plt.ylabel('Wind Speed [mph]')
            # plt.xlabel('Pressure [psf]')
            # plt.ylim(90, max(wind_speed))
            # plt.show()
            # Check the percent change between Exposure categories:
            # print('percent change in pressure by Exposure Category by h:', h, exp)
            # print(dfE.pct_change(axis=1))
            # Calculate the percent change from Exposure B:
            row = dfE.iloc[0]
            factor_list = list()
            for index in range(0, len(row)):
                if index == 0:
                    factor = 1.0
                elif row[index] == row[0]:
                    factor = 1.0
                else:
                    factor = (row[index] - row[0]) / row[0]
                factor_list.append(factor)
            # Create a quick dictionary:
            factor_dict = {exposures[m]: factor_list[m] for m in range(len(factor_list))}  # Pairs each key (Exposure) with its corresponding factor
            df_Efactor = df_Efactor.append(factor_dict, ignore_index=True)
        # Set the index to the corresponding building heights:
        # Add column:
        df_Efactor['Height in ft'] = h_bldg
        df_Efactor.set_index('Height in ft', inplace=True)
        # Store the DataFrame of Exposure factors:
        exp_list.append(df_Efactor)

    # Save the DataFrame to a .csv file for future reference:
    # df_Efactor.to_csv('Roof_MWFRS_Exp.csv')

def func(x, a, b, c):
    return a*(x**2)+b*x+c


# Set up the reference building parameters:
ref_exposure = 'B'
ref_hbldg = 9  # [ft]
ref_cat = 2  # Importance factor category
# Create a vector of editions:
edition = ['ASCE 7-95', 'ASCE 7-98', 'ASCE 7-10', 'ASCE 7-16']
# Define a range of wind speed values:
wind_speed = np.arange(90, 185, 5)  # [mph]
use_case = 1
run_sim_rmwfrs(ref_exposure, ref_hbldg, ref_cat, wind_speed, ref_exposure, edition, ref_hbldg, ref_cat, use_case)
