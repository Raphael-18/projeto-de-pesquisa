"""
Script com funções objetivo para utilização em otimizações.
"""

import numpy as np


def NSE(obs, calc):
    """
    Calculate the Nash-Sutcliffe Efficiency (NSE) coefficient.
    The NSE coefficient is used to assess the predictive power of
    hydrological models.
    It ranges from -∞ to 1, where 1 indicates a perfect match between
    observed and calculated values.
    Parameters:
    obs (list or array-like): Observed data.
    calc (list or array-like): Calculated data from the model.
    Returns:
    float: The NSE coefficient.
    Raises:
    ValueError: If the lengths of `obs` and `calc` are not equal.
    """
    a = 0
    b = 0
    Qm = np.mean(obs)
    for i in range(len(obs)):
        a += (obs[i] - calc[i]) ** 2
        b += (obs[i] - Qm) ** 2
    return a / b


def SSQ(obs, calc):
    """
    Calculate the Sum of Squares of Deviations (SSQ) between
    observed and calculated values.
    Parameters:
    obs (list or array-like): The observed values.
    calc (list or array-like): The calculated values.
    Returns:
    float: The sum of squares of deviations.
    Raises:
    ValueError: If the lengths of `obs` and `calc` do not match.
    Example:
    >>> obs = [1, 2, 3]
    >>> calc = [1.1, 1.9, 3.2]
    >>> SSQ(obs, calc)
    0.015
    """
    a = 0
    for i in range(len(obs)):
        a += ((obs[i] - calc[i]) / obs[i]) ** 2
    return a


def RMSE(obs, calc):
    """
    Calculate the Root Mean Square Error (RMSE) between observed and
    calculated values.
    Parameters:
    obs (list or array-like): The observed values.
    calc (list or array-like): The calculated values.
    Returns:
    float: The RMSE value.
    Example:
    >>> obs = [1.0, 2.0, 3.0]
    >>> calc = [1.1, 1.9, 3.2]
    >>> RMSE(obs, calc)
    0.17320508075688773
    """
    a = 0
    n = len(obs)
    for i in range(n):
        a += (obs[i] - calc[i]) ** 2
    return np.sqrt(a / n)


def KGE(obs, calc):
    """
    Calculate the Kling-Gupta Efficiency (KGE) between observed
    and calculated data.
    The KGE is a metric that combines three components: correlation,
    variability bias, and mean bias.
    It is used to evaluate the performance of hydrological models.
    Parameters:
    obs (array-like): Array of observed data.
    calc (array-like): Array of calculated data.
    Returns:
    float: The KGE value, which ranges from -∞ to 1. A value of 1
    indicates perfect agreement between observed and calculated data.
    """

    r = np.corrcoef(obs, calc)  # Correlação de Pearson
    alfa = np.std(calc) / np.std(obs)
    beta = np.mean(calc) / np.mean(obs)
    return ((r[0, 1] - 1) ** 2 + (alfa - 1) ** 2 + (beta - 1) ** 2) ** 0.5
