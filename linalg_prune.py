from functools import reduce
import logging

import numpy as np

def prune_sum_eq_len(domain):
    constraints = [
        domain.estimate("min") > domain.length,
        domain.estimate("max") < domain.length,
    ]
    pad = reduce(lambda x, y: x | y, constraints)
    pad = pad & np.isnan(domain.grid)
    domain.grid = np.where(pad, ~pad, domain.grid)
    return pad.any()

def prune_fill_last_col(domain):
    """ Fill with 1 if last available position in column """
    pad = np.isnan(domain.grid) * (np.isnan(domain.grid).sum(0) == 1)
    domain.grid = np.where(pad, pad, domain.grid)
    return pad.any()

def prune_fill_last_number(domain):
    """ Fill last missing number """
    if np.isnan(domain.to_numbers()).sum() == 1:
        position = np.nanmax(np.where(
            np.isnan(domain.to_numbers()),
            domain.numbers, # index
            np.nan))
        domain.grid[:, position] = np.isnan(domain.grid[:position])
        return True
    return False

def prune_less_than_possible(domain):
    """ Fill with 0 values less than current number of occurences """
    row_sum = np.nansum(domain.grid, 1)
    pad = domain.missing_values() < row_sum
    domain.grid = np.where(pad, ~pad, domain.grid)
    return pad.any()

def prune_row_ready(domain):
    """ Decide number at position if already filled corresponding row """
    ready_rows = np.where(
        np.isnan(domain.to_numbers()),
        np.isnan(domain.grid).sum(1) == 0,
        np.nan)
    row_sum = np.nansum(domain.grid, 1)
    filler = np.where(ready_rows, row_sum, np.nan)
    for position, value in enumerate(filler):
        if ~np.isnan(value):
            domain[position] = value
    return False

def prune(domain):
    """ Prune using listed functions """
    logging.debug("Input domain:\n%s" % str(domain))
    constraints = [
        prune_less_than_possible,
        prune_sum_eq_len,
        prune_fill_last_col,
        prune_fill_last_number,
        prune_row_ready,
    ]
    changed = feasible = True
    while changed and feasible:
        changed = any([func(domain) for func in constraints])
        feasible = domain.feasibility_test().all()
        logging.debug("Feasible: {}".format(feasible))
    return feasible
