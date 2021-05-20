import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import scipy.optimize as opt
from scipy.stats import norm
import get_sim_bldgs
import post_disaster_damage_dataset


def execute_fragility_workflow(bldg, site, component_type, hazard_type, event_year, event_name, data_types, file_paths, damage_scale_name, analysis_date, hazard_file_path):
    # Step 1: Find similar buildings: features, load path for the given hazard (may include your building as well)
    sim_bldgs = get_sim_bldgs.get_sim_bldgs(bldg, site, hazard_type, component_type)
    # Step 2: Find damage descriptions for each building:
    # Create dictionary to track pertinent sample building info (data visualization):
    sample_dict = {'Parcel Id': [], component_type: [], 'Stories': [], 'Disaster Permit': [], 'Permit Description': [], 'Demand Value': [], 'Value': []}
    for sim_bldg in sim_bldgs:
        data_details_list = []
        avail_flag = False
        for i in range(0, len(data_types)):  # Collect data from each data source
            if isinstance(data_types[i], post_disaster_damage_dataset.STEER):
                data_details = data_types[i].add_steer_data(sim_bldg, component_type, hazard_type, file_paths[i])
            elif isinstance(data_types[i], post_disaster_damage_dataset.BayCountyPermits):
                length_unit = 'ft'
                data_details = data_types[i].add_disaster_permit_data(sim_bldg, component_type, hazard_type, site,
                                 file_paths[i], length_unit, damage_scale_name)
            #elif isinstance(data_types[i], post_disaster_damage_data_source.FemaIhaLd):
            #    data_details = data_types[i].add_fema_IHA_LD_data(sim_bldg, component_type, hazard_type, event_name)
            if data_details['available']:
                avail_flag = True
                data_details_list.append(data_details)
            else:
                pass
        # Step 3: Choose the best data for each bldg/component:
        if avail_flag:
            best_data = get_best_data(data_details_list, analysis_date)  # Data Fidelity Index
        else:
            best_data = data_details.copy()
            best_data['fidelity'] = None
        # Add data to building data model:
        sim_bldg.hasDamageData['roof cover'] = best_data
        sim_bldg.hasElement['Roof'][0].hasDamageData = best_data
        # Step 4: Get the intensity measure or engineering demand parameter for this building:
        if hazard_type == 'wind':
            if component_type == 'roof cover':
                z = bldg.hasGeometry['Height']
                sim_bldg.hasElement['Roof'][0].hasDemand['wind speed'] = get_local_wind_speed(sim_bldg, z, hazard_file_path,
                                                                                              exposure='C', unit='english')
            else:
                pass
        # Step 5: Export attributes for all sample buildings:
        sample_dict['Parcel Id'].append(sim_bldg.hasID)
        sample_dict['Stories'].append(len(sim_bldg.hasStory))
        sample_dict['Value'].append(sim_bldg.hasElement['Roof'][0].hasDamageData['value'])
        sample_dict['Demand Value'].append(sim_bldg.hasElement['Roof'][0].hasDemand['wind speed'])
        if len(sim_bldg.hasPermitData['disaster']['number']) > 0:
            sample_dict['Disaster Permit'].append(True)
            sample_dict['Permit Description'].append(sim_bldg.hasPermitData['disaster']['description'])
        else:
            sample_dict['Disaster Permit'].append(False)
            sample_dict['Permit Description'].append('None')
        if component_type == 'roof cover':
            sample_dict[component_type].append(sim_bldg.hasElement['Roof'][0].hasCover)
    pd.DataFrame(sample_dict).to_csv('SampleBuildings.csv', index=False)
    # Step 5: Get the prior:
    if hazard_type == 'wind' and damage_scale_name == 'HAZUS-HM':
        pass
    else:
        pass
    # Step 6: Get input parameters necessary to conduct point and Bayesian estimates of fragility parameters:
    get_fragility_input(sim_bldgs, damage_scale_name, component_type, hazard_type)


def get_fragility_input(sim_bldgs, damage_scale_name, component_type, hazard_type):
    # Step 1: Extract data pairs (degree of damage, demand value):
    # Specify demand parameter for the hazard:
    if hazard_type == 'wind':
        demand_param = 'wind speed'
    # Instantiate generic dataset object to gather damage scale info:
    gen_dataset = post_disaster_damage_dataset.PostDisasterDamageDataset()
    gen_dataset.get_damage_scale(damage_scale_name, component_type, global_flag=True, component_flag=True)
    # Data pairs in failure datasets provide the following information:
    # (1) Degree of damage of the bldg/component
    # (2) Demand value
    # Use component-level damage descriptions to partition damage for specified scale:
    if len(gen_dataset.hasDamageScale['component damage states']['number']) > 0:
        # Create empty list to hold all data pairs:
        data_pairs = []
        # Now check if sample buildings have component-level damage states:
        for bldg in sim_bldgs:
            if component_type == 'roof cover':
                if bldg.hasElement['Roof'][0].hasDamageData['available']:
                    bldg_dscale = bldg.hasElement['Roof'][0].hasDamageData['fidelity'].hasDamageScale
                    if bldg_dscale['type'] != damage_scale_name:
                        if len(bldg_dscale['component damage states']['number']) > 0:
                            pass
                        else:
                            global_flag = True
                            break  # Cannot create fragilities based solely on component-level damage states
                    else:  # Buildings with matching damage scale
                        new_tuple = (bldg.hasElement['Roof'][0].hasDamageData['hazard damage rating'][hazard_type],
                                    bldg.hasElement['Roof'][0].hasDemand['wind speed'])
                else:  # Buildings w/o damage observations
                    new_tuple = (0, bldg.hasElement['Roof'][0].hasDemand['wind speed'])
            else:
                pass
            data_pairs.append(new_tuple)
    else:  # use global damage scale instead
        print('No component-level damage states available for this damage scale')
    # Step 2: Create dichotomous failure datasets for each damage measure:
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
    # Step 3: Get input parameters for each damage state fragility:
    lparams = get_likelihood_params(dichot_dict)
    # Step 4: Conduct the Bayesian parameter estimation:
    for k in lparams:
        pass
    # Step 5: Conduct the MLE:
    #mle_params = get_point_estimate(lparams)


def get_likelihood_params(dichot_dict):
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
        mu_values = np.arange(4, 6, 0.5)
        beta_values = np.arange(0.1, 0.5, 0.1)
        mu_est, beta_est, loglike_est = [], [], []
        for mu in mu_values:
            for beta in beta_values:
                params_init = np.array([mu, beta])
                bnds = ((0, None), (0, None))  # values for mu and beta must be positive
                results_uncstr = opt.minimize(mle_objective_func, params_init, args=mle_args, bounds=bnds)
                mu_MLE, beta_MLE = results_uncstr.x
                # Save the parameter estimates:
                mu_est.append(mu_MLE)
                beta_est.append(beta_MLE)
                # Calculate the log-likelihood and save:
                loglike_est.append(sum(lparams[key]['fail']*np.log(norm.cdf(np.log(lparams[key]['demand']), mu_MLE, beta_MLE)) + (lparams[key]['total']-lparams[key]['fail'])*np.log(1-norm.cdf(np.log(lparams[key]['demand']), mu_MLE, beta_MLE))))
        # Find the pair of mu, beta initial conditions that maximize the log-likelihood:
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
        im = np.arange(70, 180, 1)
        plt.plot(im, norm.cdf(np.log(im), mle_params[key]['mu'], mle_params[key]['beta']), 'r')
        plt.plot(im, norm.cdf((np.log(im)-mle_params[key]['mu'])/mle_params[key]['beta']), 'm')
        plt.xlabel('Wind Speed')
        plt.ylabel('P(f)')
        plt.title('Damage State ' + str(key))
        plt.show()
    return mle_params


def p_f(im, mu, beta):
    return norm.cdf(np.log(im), mu, beta)




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


def get_local_wind_speed(bldg, z, wind_speed_file_path, exposure, unit):
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
        # An adjustment for height is all that is needed:
        v_local = v_basic*(z/ref_height)**(1/alpha_c)
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
        if z != ref_height:
            # Adjust for roof height:
            v_local = v_new*((z/ref_height)**(1/alpha))
        else:
            v_local = v_new
    return round(v_local)
