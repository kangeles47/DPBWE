import pymc3 as pm
import numpy as np
import pandas as pd

alphas = np.array([1, 1, 1])
c = np.array([3, 2, 1])

# Create model
with pm.Model() as model:
    # Set up your prior:
    # Parameters of the Multinomial are from a Dirichlet
    parameters = pm.Dirichlet('parameters', a=alphas, shape=3)
    # Set up the likelihood function:
    # Observed data is from a Multinomial distribution
    observed_data = pm.Multinomial(
        'observed_data', n=6, p=parameters, shape=3, observed=c)

with model:
    # Sample from the posterior
    trace = pm.sample(draws=1000, chains=2, tune=500,
                      discard_tuned_samples=True)

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