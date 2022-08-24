import numpy as np
import pandas as pd
from scipy.stats import norm
from scipy.optimize import curve_fit


def pf(im, mu, beta):
    return norm.cdf(np.log(im), np.log(mu), beta)


file_list = ['A1', 'A5', 'A49', 'A53', 'A57', 'A61', 'A81', 'A85']
file_path = 'C:/Users/Karen/Desktop/HAZUS_rcover_fragilities/'
# Loop through each file and find fragility parameters for each damage state:
param_dict = {'fig_num': file_list, 'DS1_mu': [], 'DS1_beta': [], 'DS2_mu': [], 'DS2_beta': [], 'DS3_mu': [], 'DS3_beta': []}
for file in file_list:
    df = pd.read_csv(file_path+file+'.csv')
    print(file)
    for i in range(1, 4):
        xtag = 'DS' + str(i) + '_x'
        ytag = 'DS' + str(i) + '_y'
        print(xtag)
        popt = curve_fit(pf, df[xtag], df[ytag])
        mu_dict = 'DS' + str(i) + '_mu'
        beta_dict = 'DS' + str(i) + '_beta'
        param_dict[mu_dict].append(popt[0][0])
        param_dict[beta_dict].append(popt[0][1])
df_param = pd.DataFrame(param_dict)
# Save parameter estimates:
df_param.to_csv('SFH_fragility_params.csv', index=False)
