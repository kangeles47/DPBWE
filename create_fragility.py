import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import scipy.optimize as opt
from scipy.stats import norm
import get_sim_bldgs
import post_disaster_damage_dataset
import pymc3 as pm
import arviz as az
import theano.tensor as tt


def execute_fragility_workflow(bldg, site, component_type, hazard_type, event_year, event_name, data_types, file_paths,
                               damage_scale_name, analysis_date, hazard_file_path, sfh_flag):
    """
    A function that runs the automated updating of component-level fragilities using heterogeneous post-disaster damage
    datasets.
    :param bldg: Parcel or Building object with case study structure's attributes
    :param site: Site Object with hasBuilding attribute that contains data models for building inventory
    :param component_type: String specifying the component under consideration (e.g., roof_cover)
    :param hazard_type: String specifying the hazard under consideration (e.g., wind)
    :param event_year: Number specifying the year of the event (e.g., 2016)
    :param event_name: String specifying the name of the event (e.g., Hurricane Michael). Write 'N/A' if not applicable.
    :param data_types: List containing generic instances of classes within the PostDisasterDamageDataset class
    :param file_paths: List containing the file paths to each post-disaster damage dataset, in same order as data_types.
                       Option to specify 'API' for FEMA Claims data types.
    :param damage_scale_name: String specifying the name of the damage scale that will be used to produce fragilities
                              (e.g., 'HAZUS-HM')
    :param analysis_date: String specifying date for the analysis in month-day-year format: '00-00-0000'
                          Useful for exploring time-varying nature of data.
    :param hazard_file_path: String specifying the file path for the associated hazard dataset
    :return: fragility_dict: A dictionary with keys = damage state number and values = fragility parameter samples from the posterior distribution.
    """
    # Step 1: Sample building selection
    # For the given hazard, component type, find buildings with similar features, load path:
    sim_bldgs = get_sim_bldgs.get_sim_bldgs(bldg, site, hazard_type, component_type, event_year, sfh_flag)
    # Step 2: Find damage descriptions:
    # Step 2a: Find parcel-specific damage descriptions:
    for sbldg in sim_bldgs:
        data_details_list = []
        avail_flag = False
        for i in range(0, len(data_types)):  # Collect data from each data source
            data_details = {'available': False, 'fidelity': None, 'component type': component_type, 'hazard type': hazard_type, 'value': None}  # Placeholder dictionary for each new iteration
            if isinstance(data_types[i], post_disaster_damage_dataset.STEER):
                data_details = data_types[i].add_steer_data(sbldg, component_type, hazard_type, file_paths[i])
            elif isinstance(data_types[i], post_disaster_damage_dataset.BayCountyPermits):
                length_unit = 'ft'
                if sbldg.hasLocation['City'].upper() == 'MEXICO BEACH' and not sbldg.isComm:
                    data_details = data_types[i].add_mb_disaster_res_permit_data(sbldg, component_type, hazard_type, damage_scale_name)
                else:
                    data_details = data_types[i].add_disaster_permit_data(sbldg, component_type, hazard_type, site,
                                     file_paths[i], length_unit, damage_scale_name)
            # Check if damage data is available for this data source:
            if data_details['available']:
                avail_flag = True
                data_details_list.append(data_details)
            else:
                pass
        # Choose the best data for each bldg/component: Data Utility Index
        if avail_flag:
            best_data = get_best_data(data_details_list, analysis_date)
        else:
            # Dummy values for buildings with no observations:
            best_data = data_details.copy()
            best_data['fidelity'] = None
        # Add best data to building data model:
        sbldg.hasDamageData['roof cover'] = best_data
        sbldg.hasElement['Roof'][0].hasDamageData = best_data
    # Step 2b: Find regional damage descriptions:
    for i in range(0, len(data_types)):  # Collect data from each data source
        new_bldgs = []
        if isinstance(data_types[i], post_disaster_damage_dataset.FemaIahrld):
            length_unit = 'ft'
            if file_paths[i] == 'API':
                df_fema = data_types[i].pull_fema_iahrld_data(event_name)
            else:
                df_fema = pd.read_csv(file_paths[i])
            new_bldgs = data_types[i].add_fema_iahrld_data(bldg, component_type, hazard_type, damage_scale_name, df_fema)
        elif isinstance(data_types[i], post_disaster_damage_dataset.FemaHma):
            length_unit = 'ft'
            if file_paths[i] == 'API':
                df_fema = data_types[i].pull_fema_hma_data(event_name)
            else:
                df_fema = pd.read_csv(file_paths[i])
            new_bldgs = data_types[i].add_fema_hma_data(bldg, component_type, hazard_type, df_fema, hazard_file_path)
        # Add new building models to list of similar buildings:
        if len(new_bldgs) > 0:
            for nbldg in new_bldgs:
                sim_bldgs.append(nbldg)
    # Step 3: Get demand data and add to each building's data model:
    for sim in sim_bldgs:
        if hazard_type == 'wind':
            if component_type == 'roof cover':
                #z = sim.hasGeometry['Height']
                sim.hasElement['Roof'][0].hasDemand['wind speed'] = get_wind_speed(sim, hazard_file_path,
                                                                                              exposure='C', unit='english')
            else:
                pass
    export_sample_flag = True
    # Optional step: Export sample building characteristics:
    if export_sample_flag:
        # Create dictionary to track pertinent sample building info (data visualization):
        sample_dict = {'Parcel Id': [], 'Address': [], component_type: [], 'Stories': [], 'Disaster Permit': [],
                       'Permit Description': [], 'Demand Value': [], 'Value': [], 'Year Built': []}
        for s in sim_bldgs:
            # Step 4: Export attributes for all sample buildings (for sanity checking):
            sample_dict['Parcel Id'].append(s.hasID)
            sample_dict['Address'].append(s.hasLocation['Address'])
            sample_dict['Stories'].append(len(s.hasStory))
            sample_dict['Value'].append(s.hasElement['Roof'][0].hasDamageData['value'])
            sample_dict['Demand Value'].append(s.hasElement['Roof'][0].hasDemand['wind speed'])
            sample_dict['Year Built'].append(s.hasYearBuilt)
            # Export permit descriptions when available as well:
            if len(s.hasPermitData['disaster']['number']) > 0:
                sample_dict['Disaster Permit'].append(True)
                sample_dict['Permit Description'].append(s.hasPermitData['disaster']['description'])
            else:
                sample_dict['Disaster Permit'].append(False)
                sample_dict['Permit Description'].append('None')
            # Export component type for verification:
            if component_type == 'roof cover':
                sample_dict[component_type].append(s.hasElement['Roof'][0].hasCover)
        # Export as csv file:
        pd.DataFrame(sample_dict).to_csv('SampleBuildings_Harvey.csv', index=False)
    # Step 6: Bayesian Parameter Estimation
    # Step 6a: Populate the prior:
    if hazard_type == 'wind' and damage_scale_name == 'HAZUS-HM':
        pass
    else:
        pass
    # Step 6b: Get input parameters for the likelihood function:
    lparams = get_likelihood_params(sim_bldgs, damage_scale_name, component_type, hazard_type)
    # Export into DataFrame:
    df_params = pd.DataFrame(columns=['DS Number', 'demand', 'fail', 'total'])
    for key in lparams:
        ds_array = np.ones(len(lparams[key]['total'])) * key
        new_dict = {'DS Number': ds_array, 'demand': lparams[key]['demand'], 'fail': lparams[key]['fail'],
                    'total': lparams[key]['total']}
        df_new = pd.DataFrame(new_dict)
        df_params = pd.concat([df_params, df_new], ignore_index=True)
    # Make sure we get rid of any damage states that we cannot update:
    for ds in df_params['DS Number'].unique():
        df_sub = df_params.loc[df_params['DS Number'] == ds]
        fail_unique = df_sub['fail'].unique()
        if len(fail_unique) == 1 and fail_unique[0] == 0:
            df_params = df_params.drop(df_sub.index)
        else:
            pass
    df_params.to_csv('Observations_Harvey.csv', index=False)
    # Calculate MLE estimate for comparison:
    mle_params = get_point_estimate(lparams)
    # Step 6c: Run Bayesian Parameter Estimation:
    # Step 7: Plotting:
    if hazard_type == 'wind':
        if length_unit == 'ft':
            demand_values = np.arange(70, 200, 10)  # mph
        elif length_unit == 'm':
            demand_values = np.arange(30, 90, 5)  # m/s


def conduct_bayesian(observations_file_path, mu_init, beta_init):
    df = pd.read_csv(observations_file_path)
    # Get list of unique damage state values:
    ds_list = df['DS Number'].unique()
    for ds in range(0, len(ds_list)):
        df_sub = df.loc[df['DS Number'] == ds_list[ds]]
        xj = np.array(df_sub['demand'])
        zj = np.array(df_sub['fail'])
        nj = np.array(df_sub['total'])
        mu_ds = mu_init[ds]
        beta_ds = beta_init[ds]
        with pm.Model() as model:
            # Set up the prior:
            mu = pm.Normal('mu', mu_ds, 2.71)
            beta = pm.Normal('beta', beta_ds, 0.03)

            # Define fragility function equation:
            def normal_cdf(mu, beta, xj):
                """Compute the log of the cumulative density function of the normal."""
                return 0.5 * (1 + tt.erf((tt.log(xj) - mu) / (beta * tt.sqrt(2))))
            # Define likelihood:
            # like = pm.Binomial('like', p=p, observed=zj, n=nj)
            like = pm.Binomial('like', p=normal_cdf(mu, beta, xj), observed=zj, n=nj)
            for RV in model.basic_RVs:
                print(RV.name, RV.logp(model.test_point))
            # Determine the posterior
            trace = pm.sample(2000, cores=1, return_inferencedata=True)
            # Posterior predictive check are a great way to validate model:
            # Generate data from the model using parameters from draws from the posterior:
            ppc = pm.sample_posterior_predictive(trace, var_names=['mu', 'beta', 'like'])
        # Calculate failure probabilities using samples:
        im = np.arange(70, 200, 5)
        pf_ppc = []
        for i in range(0, len(ppc['mu'])):
            y = pf(im, ppc['mu'][i], ppc['beta'][i])
            pf_ppc.append(y)
        # Plot the HPD:
        _, ax = plt.subplots()
        az.plot_hdi(im, pf_ppc, fill_kwargs={'alpha': 0.2, 'color': 'blue', 'label': 'bounds of prediction: 94% HPD'})
        # Calculate and plot the mean outcome:
        pf_mean = pf(im, ppc['mu'].mean(), ppc['beta'].mean())
        ax.plot(im, pf_mean, label='mean of prediction', color='r', linestyle='dashed')
        # Plot the mean of the simulation-based fragility:
        pf_sim = pf(im, mu_ds, beta_ds)
        ax.plot(im, pf_sim, label='simulation-based', color='k')
        # Plot the observations:
        ax.scatter(xj, zj / nj, color='r', marker='^', label='observations')
        ax.legend()
        plt.show()
        # Looking at the difference between the prior of the parameters and updated distributions:
        new_mu_mean, new_mu_std = norm.fit(ppc['mu'])
        plt.hist(ppc['mu'], bins=25, density=True, alpha=0.4, color='b')
        xmin, xmax = plt.xlim()
        x = np.linspace(xmin, xmax, 100)
        p_prior = norm.pdf(x, mu_ds, 2.71)
        p_new = norm.pdf(x, new_mu_mean, new_mu_std)
        plt.plot(x, p_prior, 'k', linewidth=2, label='prior distribution')
        plt.plot(x, p_new, 'r', linewidth=2, label='updated distribution', linestyle='dashed')
        # Note az.plot_violin(trace, var_names=['mu']) can be helpful for seeing distribution of parameter values
        # Plot the posterior distributions of each RV
        fig, ax = plt.subplots()
        az.plot_trace(trace, chain_prop={'color': ['blue','red']})
        az.plot_posterior(trace)
        az.plot_forest(trace, var_names=['mu', 'beta'])
        plt.show()
        print(az.summary(trace))



def get_dichot_dict(sim_bldgs, damage_scale_name, component_type, hazard_type, plot_flag):
    """
    Translates component-level damage descriptions (discrete or continuous) into discrete damage measures
    for the specified damage_scale_name.
    Creates data pairs of (degree of damage, demand) for each building in sim_bldgs.
    Populates dichotomous failure dataset for each damage measure for the specified damage_scale_name.

    :param sim_bldgs: List with data models of all identified sample buildings
    :param damage_scale_name: String specifying the damage scale that will be used for generation of fragilities
    :param component_type: String specifying the component type
    :param hazard_type: String specifying the hazard type
    :return: dichot_dict: A dictionary with keys = damage measure number and values = list with failure data pairs
                         for each building: (1 or 0, demand)
    """
    # Step 1: Instantiate generic dataset object to gather damage scale info:
    gen_dataset = post_disaster_damage_dataset.PostDisasterDamageDataset()
    gen_dataset.get_damage_scale(damage_scale_name, component_type, global_flag=True, component_flag=True)
    # Step 2: Translate component-level damage into discrete damage measures
    # and create (degree of damage, demand) data pairs:
    data_pairs = []
    markers = []
    for bldg in sim_bldgs:
        if component_type == 'roof cover':
            if plot_flag:
                if isinstance(bldg.hasDamageData['roof cover']['fidelity'], post_disaster_damage_dataset.STEER):
                    markers.append('o')
                elif isinstance(bldg.hasDamageData['roof cover']['fidelity'],
                                post_disaster_damage_dataset.BayCountyPermits):
                    markers.append('^')
                elif isinstance(bldg.hasDamageData['roof cover']['fidelity'], post_disaster_damage_dataset.FemaHma):
                    markers.append('1')
                elif isinstance(bldg.hasDamageData['roof cover']['fidelity'], post_disaster_damage_dataset.FemaIahrld):
                    markers.append('*')
                else:
                    markers.append('x')
            if bldg.hasElement['Roof'][0].hasDamageData['available']:
                # Use component-level descriptions to find equivalent damage measure:
                for dm in range(0, len(gen_dataset.hasDamageScale['component damage states']['number'])):
                    if isinstance(gen_dataset.hasDamageScale['component damage states']['value'], list):
                        if isinstance(bldg.hasElement['Roof'][0].hasDamageData['value'], list):
                            if (bldg.hasElement['Roof'][0].hasDamageData['value'][0] <= gen_dataset.hasDamageScale['component damage states']['value'][dm][0]) and (bldg.hasElement['Roof'][0].hasDamageData['value'][1] <= gen_dataset.hasDamageScale['component damage states']['value'][dm][1]):
                                new_dm = gen_dataset.hasDamageScale['component damage states']['number'][dm]
                                break
                            else:
                                pass
                        else:
                            if gen_dataset.hasDamageScale['component damage states']['value'][dm][0] <= bldg.hasElement['Roof'][0].hasDamageData['value'] <= gen_dataset.hasDamageScale['component damage states']['value'][dm][1]:
                                new_dm = gen_dataset.hasDamageScale['component damage states']['number'][dm]
                                break
                            else:
                                pass
                    else:
                        print('discrete damage measures not currently supported')
            else:  # Buildings w/o damage observations
                new_dm = 0
            # Create new (degree of damage, demand) data pair:
            if hazard_type == 'wind':
                new_tuple = (new_dm, bldg.hasElement['Roof'][0].hasDemand['wind speed'])
        else:
            pass
        data_pairs.append(new_tuple)
    print(data_pairs)
    if plot_flag:
        from matplotlib import rcParams
        rcParams['font.family'] = "Times New Roman"
        rcParams.update({'font.size': 16})
        msize = 12
        fig, ax = plt.subplots()
        xflag = 0
        oflag = 0
        one_flag = 0
        c_flag = 0
        for i in range(0, len(data_pairs)):
            if markers[i] == 'x':
                if xflag == 0:
                    xflag = 1
                    ax.plot(data_pairs[i][1]/2.237, data_pairs[i][0], 'k'+markers[i], markersize=msize, label='No damage dataset')
                else:
                    ax.plot(data_pairs[i][1]/2.237, data_pairs[i][0], 'k' + markers[i], markersize=msize)
            elif markers[i] == 'o':
                if oflag == 0:
                    oflag = 1
                    ax.plot(data_pairs[i][1]/2.237, data_pairs[i][0], 'r'+markers[i], markerfacecolor='none', markersize=msize, label='Field surveys')
                else:
                    ax.plot(data_pairs[i][1]/2.237, data_pairs[i][0], 'r' + markers[i], markerfacecolor='none', markersize=msize)
            elif markers[i] == '1':
                if one_flag == 0:
                    one_flag = 1
                    ax.plot(data_pairs[i][1]/2.237, data_pairs[i][0], 'b'+markers[i], markersize=msize, label='HMA dataset')
                else:
                    ax.plot(data_pairs[i][1]/2.237, data_pairs[i][0], 'b' + markers[i], markersize=msize)
            elif markers[i] == '^':
                if c_flag == 0:
                    c_flag = 1
                    ax.plot(data_pairs[i][1]/2.237, data_pairs[i][0], 'b'+markers[i], markerfacecolor='none', markersize=msize, label='Disaster Building \nPermits')
                else:
                    ax.plot(data_pairs[i][1]/2.237, data_pairs[i][0], 'b' + markers[i], markerfacecolor='none', markersize=msize)
        #ax.set_xlim(50, 80)
        ax.set_yticks([0, 1, 2, 3, 4])
        ax.set_ylabel('Damage Measure')
        ax.set_xlabel('Peak Gust Wind Speed [m/s]')
        ax.legend(loc='upper left', fontsize=12, markerscale=0.8)
        plt.show()
    # Step 3: Create dichotomous failure datasets for each damage measure:
    dichot_dict = {}
    for ds in gen_dataset.hasDamageScale['component damage states']['number']:
        bldg_fail = []
        for pair in data_pairs:
            if isinstance(pair[0], list):
                pass
            else:
                if ds <= pair[0]:
                    bldg_fail.append((1, pair[1]))
                else:
                    bldg_fail.append((0, pair[1]))
        dichot_dict[ds] = bldg_fail
    return dichot_dict


def get_likelihood_params(sim_bldgs, damage_scale_name, component_type, hazard_type):
    """
    A function that generates the input parameters for the likelihood function.

    :param sim_bldgs: (input for get_dichot_dict) List with data models of all identified sample buildings
    :param damage_scale_name: (input for get_dichot_dict) String specifying the damage scale that will be used for generation of fragilities
    :param component_type: (input for get_dichot_dict) String specifying the component type
    :param hazard_type: (input for get_dichot_dict) String specifying the hazard type
    :return: lparams: Dictionary. 'demand' key-value: list of demand values where building damage/no damage observed.
                      'total' key-value: the total number of buildings observed at the demand value.
                      'fail' key-value: the number of buildings with failures observed at the demand value.
    """
    dichot_dict = get_dichot_dict(sim_bldgs, damage_scale_name, component_type, hazard_type, plot_flag=True)
    lparams = {}
    for key in dichot_dict:
        if key == 0:
            pass
        else:
            # Set up new dictionary key:
            lparams[key] = {'demand': None, 'fail': None, 'total': None}
            # Construct an array of observed hazard intensity levels for the damage state:
            demand_lst = []
            for p in dichot_dict[key]:
                demand_lst.append(p[1])
            demand_lst.sort()
            demand_arr = np.unique(np.array(demand_lst))
            lparams[key]['demand'] = demand_arr
            # Now translate the dichotomous failure dataset into discrete values of failed and total buildings:
            fail_bldgs, total_bldgs = [], []
            for d in demand_arr:
                count_total, count_failed = 0, 0
                for pair in dichot_dict[key]:
                    if isinstance(pair[0], list):
                        pass
                    else:
                        if pair[1] == d:
                            count_total +=1
                            if pair[0] == 1:
                                count_failed +=1
                        else:
                            pass
                total_bldgs.append(count_total)
                fail_bldgs.append(count_failed)
            # Convert to numpy arrays and add to dictionary:
            lparams[key]['total'] = np.array(total_bldgs, dtype=float)
            lparams[key]['fail'] = np.array(fail_bldgs, dtype=float)
            print('Total and fail for DS '+ str(key))
            print(demand_arr)
            print(total_bldgs)
            print(fail_bldgs)
    return lparams


def get_point_estimate(lparams):
    """
    A function to obtain point estimates of unknown fragility parameters, mu and beta
    :param lparams: a dictionary with first set of keys = damage state number. Each damage state number is dictionary
                    with keys that contain arrays corresponding to:
                    (1) ['demand'] value of demand parameter
                    (2) ['fail'] # of buildings experiencing failure
                    (3) ['total'] total # of buildings at the demand parameter value
    :return: mle_params: a dictionary with keys corresponding to damage state number.
                        Each damage state number then contains dictionary with:
                        ['mu'] = MLE value for logarithmic mean
                        ['beta'] = MLE value for logarithmic dispersion
    """
    # Run the MLE optimization for each damage state:
    mle_params = {}
    for key in lparams:
        # Set up input parameters for objective function:
        mle_args = (lparams[key]['demand'], lparams[key]['total'], lparams[key]['fail'])
        # Initialization parameters for MLE:
        # Try out a range of values:
        mu_values = np.arange(4, 7, 0.5)
        beta_values = np.arange(0.1, 0.5, 0.1)
        mu_est, beta_est, loglike_est = [], [], []
        for mu in mu_values:
            for beta in beta_values:
                params_init = np.array([mu, beta])
                bnds = ((0, None), (0, None))  # values for mu and beta must be positive
                results_uncstr = opt.minimize(mle_objective_func, params_init, args=mle_args, bounds=bnds)
                mu_MLE, beta_MLE = results_uncstr.x
                # Calculate the log-likelihood:
                loglike_calc = (sum(lparams[key]['fail']*np.log(norm.cdf(np.log(lparams[key]['demand']), mu_MLE, beta_MLE)) + (lparams[key]['total']-lparams[key]['fail'])*np.log(1-norm.cdf(np.log(lparams[key]['demand']), mu_MLE, beta_MLE))))
                if np.isnan(loglike_calc):
                    pass
                else:
                    # Save the parameter estimates:
                    mu_est.append(mu_MLE)
                    beta_est.append(beta_MLE)
                    loglike_est.append(loglike_calc)
        # Find the pair of mu, beta initial conditions that maximize the log-likelihood:
        print('loglike values MLE:')
        print(loglike_est)
        max_index = loglike_est.index(max(loglike_est))
        mle_params[key] = {}
        mle_params[key]['mu'] = mu_est[max_index]
        mle_params[key]['beta'] = beta_est[max_index]
        # Plotting:
        print('Damage state number: ' + str(key))
        print('mu_MLE=', mle_params[key]['mu'], 'beta_MLE=', mle_params[key]['beta'])
        # Plotting:
        fig = plt.figure()
        plt.scatter(lparams[key]['demand'], lparams[key]['fail'] / lparams[key]['total'])
        im = np.arange(70, 200, 1)
        plt.plot(im, norm.cdf(np.log(im), mle_params[key]['mu'], mle_params[key]['beta']), 'r')
        #plt.plot(im, norm.cdf((np.log(im)-mle_params[key]['mu'])/mle_params[key]['beta']), 'm')
        plt.xlabel('Wind Speed')
        plt.ylabel('P(f)')
        plt.title('Damage State ' + str(key))
        plt.show()
    return mle_params


def pf(im, mu, beta):
    # Form of the fragility equation is such that:
    # y = 0.5 * (1 + tt.erf((tt.log(xj/mu)) / (beta * tt.sqrt(2))))
    return norm.cdf(np.log(im), np.log(mu), beta)


def mle_objective_func(params, *args):
    """
    This function computes the negative of the log likelihood function
    given parameters and data. This is the minimization problem version
    of the maximum likelihood optimization problem

    INPUTS:
    params = (2,) vector, ([mu, beta])
    mu     = scalar, median of the fragility function
    beta  = scalar, standard deviation of the fragility function
    args   = length 3 tuple, (im_i, N_i, n_i)
    im_i  = (N,) vector, values of the intensity measure
    N_i = (N,) vector, number of total buildings at the intensity measure for the damage state
    n_i = (N,) vector, number of damaged buildings at the intensity measure for the damage state

    OBJECTS CREATED WITHIN FUNCTION:
    log_lik_val = scalar, value of the log likelihood function
    neg_log_lik_val = scalar, negative of log_lik_val

    RETURNS: neg_log_lik_val
    """
    mu, beta = params
    im_i, N_i, n_i = args
    log_lik_val = sum(n_i*np.log(norm.cdf(np.log(im_i), mu, beta)) + (N_i-n_i)*np.log(1-norm.cdf(np.log(im_i), mu, beta)))
    neg_log_lik_val = -log_lik_val

    return neg_log_lik_val


def get_best_data(data_details_list, analysis_date):
    data_dict = {'damage precision': [], 'location precision': [], 'accuracy': [], 'currentness': []}
    for data in data_details_list:
        # Extract component/building damage descriptions:
        # Prioritize any descriptions that are at the component-level:
        # Data sources may have component & building level descriptions, if statement adds highest fidelity to data_dict
        if data['fidelity'].hasDamagePrecision['component, discrete']:
            data_dict['damage precision'].append('component, discrete')
        elif data['fidelity'].hasDamagePrecision['component, range']:
            data_dict['damage precision'].append('component, range')
        elif data['fidelity'].hasDamagePrecision['building, discrete']:
            data_dict['damage precision'].append('building, discrete')
        elif data['fidelity'].hasDamagePrecision['building, range']:
            data_dict['damage precision'].append('building, range')
        # Extract location description:
        for key in data['fidelity'].hasLocationPrecision:
            if data['fidelity'].hasLocationPrecision[key]:
                data_dict['location precision'].append(key)
        # Extract accuracy indicator:
        data_dict['accuracy'].append(data['fidelity'].hasAccuracy)
        # Extract current-ness:
        data_dict['currentness'].append(data['fidelity'].hasDate)
    # Convert to DataFrame for easier data manipulation:
    df_data = pd.DataFrame(data_dict)
    # Check for component-level damage descriptions first:
    data_fidelity_index = {'damage precision': ['component, discrete', 'component, range', 'building, discrete',
                                                'building, range'], 'location precision': ['exact location',
                                                                                           'street level', 'city/town level', 'zipcode/censusblock level'], 'accuracy': [True, False, None, None]}
    best_data = None
    for i in data_fidelity_index['location precision']:
        if best_data is not None:
            break
        else:
            for j in data_fidelity_index['damage precision']:
                if best_data is not None:
                    break
                else:
                    for k in data_fidelity_index['accuracy']:
                        if k is None:
                            pass
                        else:
                            idx = df_data.loc[(df_data['damage precision'] == j) & (df_data['location precision'] == i) & (df_data['accuracy'] == k)].index.to_list()
                            if len(idx) == 0:
                                pass
                            elif len(idx) == 1:
                                best_data = data_details_list[idx[0]]
                                break
                            else:
                                # Choose the data source closest to either the disaster date or today's date
                                print('Multiple data sources with the same fidelity for this bldg/component')
                                best_data = data_details_list[idx]
    return best_data


def get_wind_speed(bldg, wind_speed_file_path, exposure, unit):
    df_wind_speeds = pd.read_csv(wind_speed_file_path)
    # Round the lat and lon values to two decimal places:
    df_wind_speeds['Lon'] = round(df_wind_speeds['Lon'], 2)
    df_wind_speeds['Lat'] = round(df_wind_speeds['Lat'], 2)
    # Use the parcel's geodesic location to determine its corresponding wind speed (interpolation):
    latitude = bldg.hasLocation['Geodesic'].y
    longitude = bldg.hasLocation['Geodesic'].x
    if np.sign(latitude) < 0:
        v1_idx = df_wind_speeds.loc[(df_wind_speeds['Lat'] == round(latitude, 2)) & (
                df_wind_speeds['Lon'] < round(longitude, 2))].index[0]
        v2_idx = df_wind_speeds.loc[(df_wind_speeds['Lat'] == round(latitude, 2)) & (
                df_wind_speeds['Lon'] > round(longitude, 2))].index[-1]
        # Now find the index of the two longitude values larger/smaller than parcel's longitude:
        v_basic = np.interp(longitude, [df_wind_speeds['Lon'][v1_idx], df_wind_speeds['Lon'][v2_idx]],
                            [df_wind_speeds['Vg_mph'][v1_idx], df_wind_speeds['Vg_mph'][v2_idx]])
    else:
        # Check first if there is a datapoint with lat, lon of parcel rounded two 2 decimal places:
        try:
            v_idx = df_wind_speeds.loc[(df_wind_speeds['Lat'] == round(latitude, 2)) & (
                    df_wind_speeds['Lon'] == round(longitude, 2))].index[0]
        except IndexError:
            # Choose the wind speed based off of the closest lat, lon coordinate:
            lat_idx = df_wind_speeds.loc[df_wind_speeds['Lat'] == round(latitude, 2)].index.to_list()
            new_series = abs(longitude - df_wind_speeds['Lon'][lat_idx])
            v_idx = new_series.idxmin()
        v_basic = df_wind_speeds['Vg_mph'][v_idx]
    if unit == 'metric':
        v_basic = v_basic*2.237
        ref_height = 10
        zg_c = 274.32
    else:
        ref_height = 33
        zg_c = 900
    # Populate the remaining parameters for exposure C:
    alpha_c = 9.5
    # Calculate the local wind speed at height z given the exposure category:
    if exposure == 'C':
        bldg.hasDemand['wind speed'] = v_basic
        v_local = v_basic
        # An adjustment for height is all that is needed:
        #v_local = v_basic*(z/ref_height)**(1/alpha_c)
    else:
        # Power law - calculate the wind speed at gradient height for exposure C:
        v_gradient = v_basic / ((ref_height / zg_c) ** (1 / alpha_c))
        if exposure == 'B':
            alpha = 7.0
            if unit == 'metric':
                zg = 365.76
            else:
                zg = 1200
        elif exposure == 'D':
            alpha = 11.5
            if unit == 'metric':
                zg = 213.35
            else:
                zg = 900
        # Calculate the wind speed for the specified exposure, at its reference height:
        v_new = v_gradient*((ref_height/zg)**(1/alpha))
        bldg.hasDemand['wind speed'] = v_new
        v_local = v_new
        #f z != ref_height:
         #   # Adjust for roof height:
          #  v_local = v_new*((z/ref_height)**(1/alpha))
        #else:
         #   v_local = v_new
    return round(v_local)


def conduct_bayesian_norm(xj, zj, nj, mu_init, beta_init, num_samples=None, plot_flag=True):
    """
    A function to conduct Bayesian updating of fragility models.
    (Optional): Produce MCMC-related plots (trace). Default: True
    Notes:
    Here intensity measure is the wind speed: A normalizing factor (max wind speed) is used to improve
    numerical stability.

    Prior distributions are designated according to the assumption that the Bayesian analysis will utilize
    wind fragility functions from HAZUS (see priors for mu and beta). See De Brujin et al. (2020) for more details.

    De Bruijn J. et al. (2020). "Using rapid damage observations from social media for Bayesian updating of hurricane
    vulnerability functions: A case study of Hurricane Dorian." Nat.Hazards Earth Syst. Sci. Discuss. [preprint],
    https://doi.org/10.5194/nhess-2020-282.

    The likelihood function is modeled using a Binomial distribution see Lallemant et al. (2015) for more details.

    :param xj: An array or list of observed intensity measure values for the damage measure.
    :param zj: An array or list of failure observations (number of failed buildings/components) for the given damage
                and intensity measure.
    :param nj: An array or list of the total # of buildings for the given damage measure and intensity measure
    :param mu_init: The mean value of the prior distribution for the logarithmic mean.
    :param beta_init: The mean value of the prior distribution for the logarithmic std. dev.
    :param num_samples: (Optional) The number of samples to conduct MCMC.
    :param plot_flag: (Optional) Produce the trace plot for the MCMC and updated distributions for parameters.
    :return: updated_values: A dictionary with each parameter's updated mean and standard deviation.
    """
    # Step 1: Normalize the intensity measure:
    norm_analysis = True
    if norm_analysis:
        norm_factor = max(xj)
        xj = xj/norm_factor
        mu_init = mu_init/norm_factor
        mu_std_dev = 15/norm_factor
        nj = nj/24
        zj = zj/24
        #beta_init = beta_init/norm_factor
        #beta_std_dev = 0.03/norm_factor
    else:
        mu_std_dev = 15
    beta_std_dev = 0.03
    # Step 2: Build the Bayesian model in PyMC3:
    with pm.Model() as model:
        # Step 3a: Set up the prior
        # Here we assume Normal distributions for both parameters of the fragility
        # Note: Parameters for mu are also normalized for compatibility with intensity measure values.
        # See De Brujin et al. for more information regarding the initialization of prior distributions.
        #mu = pm.Normal('mu', mu_init/norm_factor, 15/norm_factor)
        BoundedNormal = pm.Bound(pm.Normal, lower=0.0)
        #x = BoundedNormal('x', mu=1.0, sigma=3.0)
        mu = BoundedNormal('mu', mu_init, mu_std_dev)
        beta = BoundedNormal('beta', beta_init, beta_std_dev)

        # Step 3b: Set up the likelihood function:
        # The likelihood in this model is represented via a Binomial distribution.
        # See Lallemant et al. (2015) for MLE derivation.
        # Define fragility function equation:
        def normal_cdf(mu, beta, xj):
            """Compute the log of the cumulative density function of the normal."""
            return 0.5 * (1 + tt.erf((tt.log(xj/mu)) / (beta * tt.sqrt(2))))
        # Define the likelihood:
        like = pm.Binomial('like', p=normal_cdf(mu, beta, xj), observed=zj, n=nj)
        # Uncomment to do an initial check of parameter values (lookout for like = +/-inf)
        #for RV in model.basic_RVs:
         #   print(RV.name, RV.logp(model.test_point))
        # Step 3c: Determine the posterior
        # Note: can manually change number of cores if more computational power is available.
        trace = pm.sample(6000, cores=1, return_inferencedata=True, tune=2000, random_seed=52, target_accept=0.85)
        #trace = pm.sample(8000, cores=1, return_inferencedata=True, tune=2000, random_seed=52)  #tune=2000
        # (Optional): Plotting the trace and updated distributions for parameters:
        if plot_flag:
            from matplotlib import rcParams
            rcParams['font.family'] = "Times New Roman"
            rcParams.update({'font.size': 16})
            az.plot_trace(trace, chain_prop={'color': ['blue', 'red']})
        # Step 4: Generate summary statistics for the MCMC:
        print('Summary statistics for the MCMC:')
        print(az.summary(trace))  # Note: can output this DataFrame if needed
        # Step 5: Sample from the posterior and save updated values for mean and std. dev:
        ppc = pm.sample_posterior_predictive(trace, var_names=['mu', 'beta', 'like'])
        # Re-scale values for logarithmic mean:
        if norm_analysis:
            ppc['mu'] = ppc['mu']*norm_factor
        else:
            pass
        updated_values = {'mu': {'mean': ppc['mu'].mean(), 'std dev': np.std(ppc['mu'])},
                          'beta': {'mean': ppc['beta'].mean(), 'std dev': np.std(ppc['beta'])}}
        if plot_flag:
            # Plot prior and updated distributions for parameters:
            # mu
            fig, ax = plt.subplots()
            ax.hist(ppc['mu']/2.237, bins=25, density=True, alpha=0.4, color='b', label='posterior samples')
            xmin, xmax = ax.set_xlim()
            x = np.linspace(xmin, xmax, 100)
            if norm_analysis:
                p_prior = norm.pdf(x, mu_init*norm_factor / 2.237, mu_std_dev*norm_factor / 2.237)
            else:
                p_prior = norm.pdf(x, mu_init/2.237, mu_std_dev/2.237)
            p_new = norm.pdf(x, updated_values['mu']['mean']/2.237, updated_values['mu']['std dev']/2.237)
            ax.plot(x, p_prior, 'k', linewidth=2, label='prior')
            ax.plot(x, p_new, 'r', linewidth=2, label='updated', linestyle='dashed')
            ax.set_title('Prior and updated distributions for ' + r'$\theta_1$')
            ax.set_xlabel(r'$\theta_1$')
            ax.set_ylabel('Probability')
            ax.legend()
            plt.show()
            # beta
            fig2, ax2 = plt.subplots()
            ax2.hist(ppc['beta'], bins=25, density=True, alpha=0.4, color='b', label='posterior samples')
            xmin2, xmax2 = ax2.set_xlim()
            x2 = np.linspace(xmin2, xmax2, 100)
            p_prior2 = norm.pdf(x2, beta_init, 0.03)
            p_new2 = norm.pdf(x2, updated_values['beta']['mean'], updated_values['beta']['std dev'])
            ax2.plot(x2, p_prior2, 'k', linewidth=2, label='prior')
            ax2.plot(x2, p_new2, 'r', linewidth=2, label='updated', linestyle='dashed')
            ax2.set_title('Prior and updated distributions for ' + r'$\theta_2$')
            ax2.set_xlabel(r'$\theta_2$')
            ax2.set_ylabel('Probability')
            ax2.legend()
            plt.show()
            # Calculate failure probabilities for prior, updated:
            im = np.arange(70, 200, 5)
            # Mean of simulation-based fragility:
            if norm_analysis:
                pf_sim = pf(im, mu_init*norm_factor, beta_init)
            else:
                pf_sim = pf(im, mu_init, beta_init)
            # Mean of updated fragility:
            pf_mean = pf(im, ppc['mu'].mean(), ppc['beta'].mean())
            # Calculate entire distribution of pfs using posterior samples:
            pf_ppc = []
            for i in range(0, len(ppc['mu'])):
                y = pf(im, ppc['mu'][i], ppc['beta'][i])
                pf_ppc.append(y)
            # Plot the credible intervals, mean outcome of prediction, mean of simulation-based:
            fig3, ax3 = plt.subplots()
            ax3.set_clip_on(False)
            ax3.set_ylim(0, 1.2)
            ax3.spines['right'].set_visible(False)
            ax3.spines['top'].set_visible(False)
            az.plot_hdi(im/2.237, pf_ppc, hdi_prob=0.89, fill_kwargs={'alpha': 0.1, 'color': 'blue',
                                                                      'label': '89% credible interval'})
            ax3.plot(im/2.237, pf_mean, label='mean of prediction', color='r', linestyle='dashed')
            ax3.plot(im/2.237, pf_sim, label='mean of simulation-based', color='k')
            # Plot the observations:
            if norm_analysis:
                ax3.scatter(xj*norm_factor/2.237, zj / nj, color='darkviolet', label='observations', zorder=5, s=70)
            else:
                ax3.scatter(xj / 2.237, zj / nj, color='darkviolet', label='observations', zorder=5, s=70)
            ax3.set_xlabel('Wind Speed [m/s]')
            ax3.set_ylabel('Probability of Failure')
            ax3.legend()
            plt.show()
    return updated_values


# observations_file_path = 'C:/Users/Karen/PycharmProjects/DPBWE/Observations_MB_preFBC.csv'
# df = pd.read_csv(observations_file_path)
# prior_file_path = 'C:/Users/Karen/PycharmProjects/DPBWE/Datasets/SimulationFragilities/A9_fit.csv'
# df_prior = pd.read_csv(prior_file_path)
# ds_list = df['DS Number'].unique()
# #mu_init = [4.69, 4.8]
# #mu_ds = [108.85]
# #beta_ds = [0.16, 0.15]
# for ds in range(0, len(ds_list)):
#     df_sub = df.loc[df['DS Number'] == ds_list[ds]]
#     xj = np.array(df_sub['demand'])
#     zj = np.array(df_sub['fail'])
#     nj = np.array(df_sub['total'])
#     mu_init = df_prior['theta1'][ds]
#     beta_init = df_prior['theta2'][ds]
#     updated_values = conduct_bayesian_norm(xj, zj, nj, mu_init, beta_init)
#     print('Update fragility model parameter values:')
#     print(updated_values)
# Notes:
# For MB case study: /24 + 4000 samples, 1000 tune
# fine for most, not great for post FBC with permits /30 in this case
# full PCB: /140 10000/5000 --> 1 divergence
# divide PCB full by norm factor, 6000/1000 for convergence (4000/1000 worked too)
# FULL_preFBC: /160, 8000/1000, 0.85
# MB_preFBC /24, 4000/2000, 0.85