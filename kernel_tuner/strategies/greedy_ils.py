""" A simple greedy iterative local search algorithm for parameter search """
from collections import OrderedDict

from kernel_tuner import util
from kernel_tuner.searchspace import Searchspace
from kernel_tuner.strategies import common
from kernel_tuner.strategies.common import _cost_func
from kernel_tuner.strategies.genetic_algorithm import mutate
from kernel_tuner.strategies.hillclimbers import base_hillclimb

_options = OrderedDict(neighbor=("Method for selecting neighboring nodes, choose from Hamming or adjacent", "Hamming"),
                       restart=("controls greedyness, i.e. whether to restart from a position as soon as an improvement is found", True),
                       no_improvement=("number of evaluations to exceed without improvement before restarting", 50),
                       random_walk=("controls greedyness, i.e. whether to restart from a position as soon as an improvement is found", 0.3))

def tune(runner, kernel_options, device_options, tuning_options):

    dna_size = len(tuning_options.tune_params.keys())

    options = tuning_options.strategy_options

    neighbor, restart, no_improvement, randomwalk = common.get_options(options, _options)

    perm_size = int(randomwalk * dna_size)
    if perm_size == 0:
        perm_size = 1
    max_fevals = options.get("max_fevals", 100)

    tuning_options["scaling"] = False

    # limit max_fevals to max size of the parameter space
    searchspace = Searchspace(tuning_options, runner.dev.max_threads)
    max_fevals = min(searchspace.size, max_fevals)

    fevals = 0
    results = []

    #while searching
    candidate = searchspace.get_random_sample(1)[0]
    best_score = _cost_func(candidate, kernel_options, tuning_options, runner, results, check_restrictions=False)

    last_improvement = 0
    while fevals < max_fevals:

        try:
            candidate = base_hillclimb(candidate, neighbor, max_fevals, searchspace, results, kernel_options, tuning_options, runner, restart=restart, randomize=True)
            new_score = _cost_func(candidate, kernel_options, tuning_options, runner, results, check_restrictions=False)
        except util.StopCriterionReached as e:
            if tuning_options.verbose:
                print(e)
            return results, runner.dev.get_environment()

        fevals = len(tuning_options.unique_results)
        if new_score < best_score:
            last_improvement = 0
        else:
            last_improvement += 1

        # Instead of full restart, permute the starting candidate
        candidate = random_walk(candidate, perm_size, no_improvement, last_improvement, searchspace)
    return results, runner.dev.get_environment()


tune.__doc__ = common.get_strategy_docstring("Greedy Iterative Local Search (ILS)", _options)

def random_walk(indiv, permutation_size, no_improve, last_improve, searchspace: Searchspace):
    if last_improve >= no_improve:
        return searchspace.get_random_sample(1)[0]
    for _ in range(permutation_size):
        indiv = mutate(indiv, 0, searchspace, cache=False)
    return indiv
