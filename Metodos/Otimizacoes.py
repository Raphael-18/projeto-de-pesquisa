import numpy as np

# Funções objetivo utilizadas durante rotinas de calibração:
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

# KGE: Kling-Gupta
def KGE(obs, calc):
    r = np.corrcoef(obs, calc) # Correlação de Pearson
    alfa = np.std(calc) / np.std(obs)
    beta = np.mean(calc) / np.mean(obs)
    return ((r[0, 1] - 1) ** 2 + (alfa - 1) ** 2 + (beta - 1) ** 2) ** 0.5
