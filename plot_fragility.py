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
ax.spines['right'].set_visible(False)
ax.spines['top'].set_visible(False)
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

# 2) Pre-FBC with additional roof permits:
df_mbr = pd.read_csv('D:/Users/Karen/Documents/Github/DPBWE/Datasets/Fragilities/MexicoBeach/MB_preFBC_rpermit_DS1_BI.csv')
df_pcbr = pd.read_csv('D:/Users/Karen/Documents/GitHub/DPBWE/Datasets/Fragilities/PanamaCityBeach/PCB_preFBC_rpermit_DS1_BI.csv')
df_fullr = pd.read_csv('D:/Users/Karen/Documents/Github/DPBWE/Datasets/Fragilities/MexicoBeachAndPanamaCityBeach/MB_PCB_preFBC_rpermit_DS1_BI.csv')
df_prior = pd.read_csv('D:/Users/Karen/Documents/Github/DPBWE/Datasets/SimulationFragilities/A9_fit.csv')
df_observations = pd.read_csv('D:/Users/Karen/Documents/Github/DPBWE/Datasets/Fragilities/MexicoBeachAndPanamaCityBeach/Observations_FULL_preFBC_rpermit.csv')
df_sub = df_observations.loc[df_observations['DS Number']==1]
im = np.arange(70, 200, 2)
mph_to_ms = 1/2.237
pf_mbr = pf(im, df_mbr['theta1mean'][0], df_mbr['theta2mean'][0])
pf_pcbr = pf(im, df_pcbr['theta1mean'][0], df_pcbr['theta2mean'][0])
pf_fullr = pf(im, df_fullr['theta1mean'][0], df_fullr['theta2mean'][0])
pf_prior = pf(im, df_prior['theta1'][0], df_prior['theta2'][0])
pf_mle = pf(im, np.exp(4.814943855384), 0.1004095049)
# Plot each P(f) + observations:
rcParams['font.family'] = "Times New Roman"
rcParams.update({'font.size': 16})
fig2, ax2 = plt.subplots()
ax2.set_clip_on(False)
ax2.set_ylim(0, 1.2)
ax2.spines['right'].set_visible(False)
ax2.spines['top'].set_visible(False)
ax2.scatter(df_sub['demand']*mph_to_ms, df_sub['fail']/df_sub['total'], color='darkviolet', label='Observations', s=70)
#ax.plot(im*mph_to_ms, pf_mle, '--', label='Maximum Likelihood Estimate', color='darkorange', linewidth=2)
ax2.plot(im*mph_to_ms, pf_mbr, label='Mexico Beach', color='dodgerblue', linestyle='dotted', linewidth=2)
ax2.plot(im*mph_to_ms, pf_pcbr, '*', color='blue', label='Panama City Beach')
ax2.plot(im*mph_to_ms, pf_fullr, label='Mexico Beach and Panama City Beach', color='r', linestyle='dashed', linewidth=2)
ax2.plot(im*mph_to_ms, pf_prior, label='Simulation-based', color='k')
# Plot labels:
ax2.set_xlabel('Wind speed [m/s]')
ax2.set_ylabel('Probability of Failure')
ax2.legend()
plt.show()

# 3) Checking influence of roof permits for pre-FBC:
fig3, ax3 = plt.subplots(1,3)
for a in ax3:
    a.set_clip_on(False)
    a.set_ylim(0, 1.2)
    a.set_xlabel('Wind speed [m/s]')
    a.spines['right'].set_visible(False)
    a.spines['top'].set_visible(False)
# Mexico beach
ax3[0].plot(im*mph_to_ms, pf_mb, color='b')
ax3[0].plot(im*mph_to_ms, pf_mbr, color='b', linestyle='dotted')
ax3[0].set_title('Mexico Beach')
# Panama city beach
ax3[1].plot(im*mph_to_ms, pf_pcb, label='without roof permit data', color='b')
ax3[1].plot(im*mph_to_ms, pf_pcbr, label='with roof permit data', color='b', linestyle='dotted')
ax3[1].legend()
ax3[1].set_title('Panama City Beach')
# Both
ax3[2].plot(im*mph_to_ms, pf_full, color='b')
ax3[2].plot(im*mph_to_ms, pf_fullr, color='b', linestyle='dotted')
ax3[2].set_title('Mexico Beach and \nPanama City Beach')
plt.show()

# 4) Bring in the FBC era buildings:
df_mb_fbc = pd.read_csv('D:/Users/Karen/Documents/Github/DPBWE/Datasets/Fragilities/MexicoBeach/MB_postFBC_DS1_BI.csv')
df_pcb_fbc = pd.read_csv('D:/Users/Karen/Documents/GitHub/DPBWE/Datasets/Fragilities/PanamaCityBeach/PCB_postFBC_DS1_BI.csv')
df_full_fbc = pd.read_csv('D:/Users/Karen/Documents/Github/DPBWE/Datasets/Fragilities/MexicoBeachAndPanamaCityBeach/MB_PCB_postFBC_DS1_BI.csv')
df_prior = pd.read_csv('D:/Users/Karen/Documents/Github/DPBWE/Datasets/SimulationFragilities/A9_fit.csv')
df_observations = pd.read_csv('D:/Users/Karen/Documents/Github/DPBWE/Datasets/Fragilities/MexicoBeachAndPanamaCityBeach/Observations_FULL_postFBC.csv')
df_sub = df_observations.loc[df_observations['DS Number']==1]
im = np.arange(70, 200, 2)
mph_to_ms = 1/2.237
pf_mb_fbc = pf(im, df_mb_fbc['theta1mean'][0], df_mb_fbc['theta2mean'][0])
pf_pcb_fbc = pf(im, df_pcb_fbc['theta1mean'][0], df_pcb_fbc['theta2mean'][0])
pf_full_fbc = pf(im, df_full_fbc['theta1mean'][0], df_full_fbc['theta2mean'][0])
pf_prior = pf(im, df_prior['theta1'][0], df_prior['theta2'][0])
pf_mle = pf(im, np.exp(4.849286332438377), 0.11317134203248831)
# Plot each P(f) + observations:
fig4, ax4 = plt.subplots()
ax4.set_clip_on(False)
ax4.set_ylim(0, 1.2)
ax4.spines['right'].set_visible(False)
ax4.spines['top'].set_visible(False)
ax4.scatter(df_sub['demand']*mph_to_ms, df_sub['fail']/df_sub['total'], color='darkviolet', label='Observations', s=70)
#ax4.plot(im*mph_to_ms, pf_mle, '--', label='Maximum Likelihood Estimate', color='darkorange', linewidth=2)
ax4.plot(im*mph_to_ms, pf_mb_fbc, label='Mexico Beach', color='dodgerblue', linestyle='dotted', linewidth=2)
ax4.plot(im*mph_to_ms, pf_pcb_fbc, '*', color='blue', label='Panama City Beach')
ax4.plot(im*mph_to_ms, pf_full_fbc, label='Mexico Beach and Panama City Beach', color='r', linestyle='dashed', linewidth=2)
ax4.plot(im*mph_to_ms, pf_prior, label='Simulation-based', color='k')
# Plot labels:
ax4.set_xlabel('Wind speed [m/s]')
ax4.set_ylabel('Probability of Failure')
ax4.legend()
plt.show()

# Bring in FBC, with roof permit data:
df_mb_fbcr = pd.read_csv('D:/Users/Karen/Documents/Github/DPBWE/Datasets/Fragilities/MexicoBeach/MB_postFBC_rpermit_DS1_BI.csv')
df_pcb_fbcr = pd.read_csv('D:/Users/Karen/Documents/GitHub/DPBWE/Datasets/Fragilities/PanamaCityBeach/PCB_postFBC_rpermit_DS1_BI.csv')
df_full_fbcr = pd.read_csv('D:/Users/Karen/Documents/Github/DPBWE/Datasets/Fragilities/MexicoBeachAndPanamaCityBeach/MB_PCB_postFBC_rpermit_DS1_BI.csv')
df_prior = pd.read_csv('D:/Users/Karen/Documents/Github/DPBWE/Datasets/SimulationFragilities/A9_fit.csv')
df_observations = pd.read_csv('D:/Users/Karen/Documents/Github/DPBWE/Datasets/Fragilities/MexicoBeachAndPanamaCityBeach/Observations_FULL_postFBC_rpermit.csv')
df_sub = df_observations.loc[df_observations['DS Number']==1]
im = np.arange(70, 200, 2)
mph_to_ms = 1/2.237
pf_mb_fbcr = pf(im, df_mb_fbcr['theta1mean'][0], df_mb_fbcr['theta2mean'][0])
pf_pcb_fbcr = pf(im, df_pcb_fbcr['theta1mean'][0], df_pcb_fbcr['theta2mean'][0])
pf_full_fbcr = pf(im, df_full_fbcr['theta1mean'][0], df_full_fbcr['theta2mean'][0])
pf_prior = pf(im, df_prior['theta1'][0], df_prior['theta2'][0])
pf_mle = pf(im, np.exp(4.841923034920179), 0.16880303364283972)
# Plot each P(f) + observations:
fig5, ax5 = plt.subplots()
ax5.set_clip_on(False)
ax5.set_ylim(0, 1.2)
ax5.spines['right'].set_visible(False)
ax5.spines['top'].set_visible(False)
ax5.scatter(df_sub['demand']*mph_to_ms, df_sub['fail']/df_sub['total'], color='darkviolet', label='Observations', s=70)
#ax5.plot(im*mph_to_ms, pf_mle, '--', label='Maximum Likelihood Estimate', color='darkorange', linewidth=2)
ax5.plot(im*mph_to_ms, pf_mb_fbcr, label='Mexico Beach', color='dodgerblue', linestyle='dotted', linewidth=2)
ax5.plot(im*mph_to_ms, pf_pcb_fbcr, '*', color='blue', label='Panama City Beach')
ax5.plot(im*mph_to_ms, pf_full_fbcr, label='Mexico Beach and Panama City Beach', color='r', linestyle='dashed', linewidth=2)
ax5.plot(im*mph_to_ms, pf_prior, label='Simulation-based', color='k')
# Plot labels:
ax5.set_xlabel('Wind speed [m/s]')
ax5.set_ylabel('Probability of Failure')
ax5.legend()
plt.show()

# Let's see the performance of parcels pre vs. FBC:
fig6, ax6 = plt.subplots(1,3)
for i in ax6:
    i.set_clip_on(False)
    i.set_ylim(0, 1.2)
    i.set_xlabel('Wind speed [m/s]')
    i.spines['right'].set_visible(False)
    i.spines['top'].set_visible(False)
ax6[0].plot(im*mph_to_ms, pf_mbr, color='b')
ax6[0].plot(im*mph_to_ms, pf_mb_fbcr, color='b', linestyle='dotted')
ax6[0].set_title('Mexico Beach')
# Panama city beach
ax6[1].plot(im*mph_to_ms, pf_pcbr, label='pre-FBC', color='b')
ax6[1].plot(im*mph_to_ms, pf_pcb_fbcr, label='FBC', color='b', linestyle='dotted')
ax6[1].legend()
ax6[1].set_title('Panama City Beach')
# Both
ax6[2].plot(im*mph_to_ms, pf_fullr, color='b')
ax6[2].plot(im*mph_to_ms, pf_full_fbcr, color='b', linestyle='dotted')
ax6[2].set_title('Mexico Beach and \nPanama City Beach')
plt.show()