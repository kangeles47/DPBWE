import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from scipy.stats.distributions import norm
from matplotlib import rcParams


def pf(im, theta1, theta2):
    return norm.cdf(np.log(im), np.log(theta1), theta2)

# 1) Pre-FBC Plotting:
df_mb = pd.read_csv('D:/Users/Karen/Documents/Github/DPBWE/Datasets/Fragilities/MexicoBeach/MB_preFBC_DS1_BI.csv')
df_pcb = pd.read_csv('D:/Users/Karen/Documents/GitHub/DPBWE/Datasets/Fragilities/PanamaCityBeach/PCB_preFBC_DS1_BI.csv')
df_full = pd.read_csv('D:/Users/Karen/Documents/Github/DPBWE/Datasets/Fragilities/MexicoBeachAndPanamaCityBeach/MB_PCB_preFBC_DS1_BI.csv')
df_prior = pd.read_csv('D:/Users/Karen/Documents/Github/DPBWE/Datasets/SimulationFragilities/A9_fit.csv')
df_observations = pd.read_csv('D:/Users/Karen/Documents/Github/DPBWE/Datasets/Fragilities/MexicoBeachAndPanamaCityBeach/Observations_FULL_preFBC.csv')
df_sub = df_observations.loc[df_observations['DS Number']==1]
im = np.arange(70, 200, 2)
mph_to_ms = 1/2.237
pf_mb = pf(im, df_mb['theta1mean'][0], df_mb['theta2mean'][0])
pf_pcb = pf(im, df_pcb['theta1mean'][0], df_pcb['theta2mean'][0])
pf_full = pf(im, df_full['theta1mean'][0], df_full['theta2mean'][0])
pf_prior = pf(im, df_prior['theta1'][0], df_prior['theta2'][0])
pf_mle = pf(im, np.exp(4.83402315), 0.1050728)
# Plot each P(f) + observations:
rcParams['font.family'] = "Times New Roman"
rcParams.update({'font.size': 16})
fig, ax = plt.subplots()
ax.set_clip_on(False)
ax.set_ylim(0, 1.2)
ax.scatter(df_sub['demand']*mph_to_ms, df_sub['fail']/df_sub['total'], color='darkviolet', label='Observations', s=70)
#ax.plot(im*mph_to_ms, pf_mle, '--', label='Maximum Likelihood Estimate', color='darkorange', linewidth=2)
ax.plot(im*mph_to_ms, pf_mb, label='Mexico Beach', color='dodgerblue', linestyle='dotted', linewidth=2)
ax.plot(im*mph_to_ms, pf_pcb, '*', color='blue', label='Panama City Beach')
ax.plot(im*mph_to_ms, pf_full, label='Mexico Beach and Panama City Beach', color='r', linestyle='dashed', linewidth=2)
ax.plot(im*mph_to_ms, pf_prior, label='Simulation-based', color='k')
# Plot labels:
ax.set_xlabel('Wind speed [m/s]')
ax.set_ylabel('Probability of Failure')
ax.legend()
plt.show()

