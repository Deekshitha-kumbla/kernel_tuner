""" The differential evolution strategy that optimizes the search through the parameter space """
from __future__ import print_function

import itertools

import numpy
from scipy.optimize import differential_evolution
from kernel_tuner import util

def tune(runner, kernel_options, device_options, tuning_options):
    """ Find the best performing kernel configuration in the parameter space

    :params runner: A runner from kernel_tuner.runners
    :type runner: kernel_tuner.runner

    :param kernel_options: A dictionary with all options for the kernel.
    :type kernel_options: dict

    :param device_options: A dictionary with all options for the device
        on which the kernel should be tuned.
    :type device_options: dict

    :param tuning_options: A dictionary with all options regarding the tuning
        process.
    :type tuning_options: dict

    :returns: A list of dictionaries for executed kernel configurations and their
        execution times. And a dictionary that contains a information
        about the hardware/software environment on which the tuning took place.
    :rtype: list(dict()), dict()

    """

    #build a bounds array as needed for the optimizer
    results = []
    bounds = []
    param_names = []
    for k, v in tuning_options.tune_params.items():
        sorted_values = numpy.sort(v)
        param_names.append(k)
        bounds.append((v[0], v[-1]))

    #call the differential evolution optimizer
    opt_result = differential_evolution(_cost_func, bounds, [kernel_options, tuning_options, runner, results],
                                        maxiter=1, polish=False, disp=tuning_options.verbose)

    if tuning_options.verbose:
        print(opt_result.message)
        print('best config:', _snap_to_nearest_config(opt_result.x, tuning_options.tune_params))

    return results, runner.dev.get_environment()



def _snap_to_nearest_config(x, tune_params):
    """ Helper func that for each param selects the closest actual value """
    params = []
    for i, k in enumerate(tune_params.keys()):
        values = numpy.array(tune_params[k])
        idx = numpy.abs(values-x[i]).argmin()
        params.append(values[idx])
    return params


def _cost_func(x, kernel_options, tuning_options, runner, results):
    """ cost function used by the differential evolution optimizer """

    #snap values in x to nearest actual value for each parameter
    params = _snap_to_nearest_config(x, tuning_options.tune_params)

    #check if this is a legal (non-restricted) parameter instance
    if tuning_options.restrictions:
        legal = util.check_restrictions(tuning_options.restrictions, params, tuning_options.tune_params.keys(), tuning_options.verbose)
        if not legal:
            return 1e20

    #compile and benchmark this instance
    res, _ = runner.run([params], kernel_options, tuning_options)

    #append to tuning results
    if len(res) > 0:
        results.append(res[0])
        return res[0]['time']

    return 1e20
