import pymc3 as pm
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.stats import norm


# Damage observations per building and IM are either 0 or 1 (failure)
def custom_logp(mu, beta, n_i, N_i, im_i):
    return  sum(n_i*np.log(norm.cdf(np.log(im_i), np.log(mu), beta)) + (N_i-n_i)*np.log(1-norm.cdf(np.log(im_i), np.log(mu), beta)))


# Generate the dataset (observed values):
# Note: no DataFrames, no Booleans

# Create Bayesian model:
with pm.Model() as model:
    # Set up your prior:
    mu = pm.Normal('mu', 0, 0.001, value=0)  # check these
    beta = pm.Normal('beta', 0, 0.001, value=0)
    # Set up log-likelihood function:
    param_obs = pm.DensityDist('param_obs', custom_logp(mu, beta, n_i, N_i, im_i), observed=0)
    # Determine the posterior
    trace = pm.sample(1000)  # might want to include a burn-in perior here
    # Plot the posterior distributions of each RV
    pm.traceplot(trace, ['mu', 'beta'])
    pm.summary(trace)
    plt.show()

def bayesian_updating(name, priors_beta_mu1, priors_beta_sd1, priors_beta_mu0, priors_beta_sd0):
    data = pd.read_csv('file_path')  # 'file_path' contains observation data
    data_x = data.iloc[:,0]  # x-values of the dataframe
    n = len(data.index)  # number of rows in the dataframe
    norm_factor = max(data.iloc[:, 0])  # maximum value in the data
    data_xnorm = data_x/norm_factor
    x = data_xnorm
    y = data.iloc[:,1]  # second column in dataframe
    # Set up some plotting:
    x_plot = np.arange(1,500,1)
    x_plot_norm = x_plot/norm_factor
    b1.prior_mu = priors_beta_mu1/norm_factor
    b1.prior_sd = priors_beta_sd1/norm_factor
    calc_x = get_x(x)
    updating = 0
    return updating

def get_x(x):
    input_value =
    calc_x = np.exp(input_val)