import numpy as np

# 1. Funcoes objetivo utilizadas durante rotinas de calibracao:
# NSE: Nash-Sutcliffe
def NSE(obs, calc):
    a = 0
    b = 0
    Qm = np.mean(obs)
    for i in range(len(obs)):
        a += (obs[i] - calc[i]) ** 2
        b += (obs[i] - Qm) ** 2
    return a / b

# SSQ: Sum of Squares of Deviations
def SSQ(obs, calc):
    a = 0
    for i in range(len(obs)):
        a += ((obs[i] - calc[i]) / obs[i]) ** 2
    return a

# RMSE: Root-Mean-Square Error
def RMSE(obs, calc):
    a = 0
    n = len(obs)
    for i in range(n):
        a += (obs[i] - calc[i]) ** 2
    return np.sqrt(a / n)
