import numpy as np
import pandas as pd
import arviz as az
import pymc3 as pm
import theano.tensor as tt
import matplotlib.pyplot as plt
from scipy.stats import norm
from scipy.special import comb


# Damage observations per building and IM are either 0 or 1 (failure)
class LogLike(tt.Op):
    """
    Pass in vector of values (the parameters that define our model) and return a single "scalar" value (the log-likelihood)
    """
    itypes = [tt.dvector]  # expects a vector of parameter values when called
    otypes = [tt.dscalar]  # outputs a single scalar value (log-likelihood)

    def __init__(self, loglike, fail, total, demand):
        """
        Initialise the Op with various things that our log-likelihood function
        requires.

        Parameters
        ----------
        loglike:
            The log-likelihood function
        fail:
            The number of failure occurrences
        total:
            The number of total buildings or components available
        demand:
            The demand value for each observation of failed/total
        """

        # add inputs as class attributes
        self.log_like = loglike
        self.fail = fail
        self.total = total
        self.demand = demand
        #self.mu = mu
        #self.beta = beta

    def perform(self, node, inputs, outputs):
        # the method that is used when calling the Op
        (theta,) = inputs  # this will contain my variables

        # call the log-likelihood function
        logl = self.log_like(theta, self.fail, self.total, self.demand)

        outputs[0][0] = np.array(logl)  # output the log-likelihood


def log_likelihood(theta, fail, total, demand):
    mu, beta = theta
    return sum(comb(total, fail) +
               fail*np.log(norm.cdf(np.log(demand), mu, beta)) + (total-fail)*np.log(1-norm.cdf(np.log(demand), mu, beta)))


def pf(im, mu, beta):
    return norm.cdf(np.log(im), mu, beta)


demand_arr = np.array([117, 123, 128])
fail_bldgs = np.array([0, 3, 2])
total_bldgs = np.array([1, 4, 2])
xj = np.array([117, 123, 128])
zj = np.array([0, 3, 2])
nj = np.array([1, 4, 2])
m = sum(xj)/len(xj)
#xj = xj/m

with pm.Model() as model:
    # Set up the prior:
    #BoundedNormal = pm.Bound(pm.Normal, lower=0.0)
    theta = pm.Normal('theta', 4.69, 2.71)
    beta = pm.Normal('beta', 0.1645, 0.03)

    # Define fragility function equation:
    #def my_func(theta, beta, xj):
     #   p = pm.Normal.dist(0, 1).logcdf((tt.log(xj)-theta)/beta)
      #  return p
      #  return custom_p.distribution.logcdf((np.log(xj)-theta)/beta)
    def normal_cdf(theta, beta, xj):
        """Compute the log of the cumulative density function of the normal."""
        return 0.5 * (1 + tt.erf((tt.log(xj) - theta) / (beta * tt.sqrt(2))))
    #p = pm.invlogit(beta+theta*np.log(xj))
    # Define likelihood:
    #like = pm.Binomial('like', p=p, observed=zj, n=nj)
    like = pm.Binomial('like', p=normal_cdf(theta, beta, xj), observed=zj, n=nj)
    for RV in model.basic_RVs:
        print(RV.name, RV.logp(model.test_point))
    # Determine the posterior
    trace = pm.sample(2000, cores=1)
    # Plot the posterior distributions of each RV
    #pm.traceplot(trace, ['theta', 'beta'])
    az.plot_trace(trace[1000:])
    az.plot_posterior(trace)
    print(az.summary(trace))
    plt.show()

# Additional plotting
im = np.arange(70, 200, 1)
df = pm.trace_to_dataframe(trace)
y_init = pf(im, 4.69, 0.1645)
plt.plot(im, y_init)

# create our Op
#logl = LogLike(log_likelihood, fail_bldgs, total_bldgs, demand_arr)
# Create Bayesian model:
#with pm.Model() as model:
    # Set up your prior:
 #   BoundedNormal = pm.Bound(pm.Normal, lower=0.0)
  #  theta = BoundedNormal('theta', 4.69, 2.71)
   # beta = BoundedNormal('beta', 0.1645, 0.03)
    # convert mu and beta to a tensor vector
    #theta = tt.as_tensor_variable([theta, beta])
    # Set up log-likelihood function:
    #log_like = pm.DensityDist('log_like', lambda v: logl(v), observed={'v': theta})
    # Determine the posterior
    #trace = pm.sample(1000, cores=1)  # might want to include a burn-in period here
#    # Plot the posterior distributions of each RV
    #pm.traceplot(trace, ['mu', 'beta'])
    #pm.summary(trace)
    #plt.show()

