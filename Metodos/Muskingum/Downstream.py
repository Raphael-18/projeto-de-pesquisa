import sys

import math
import numpy as np

# O routing de montante para jusante
# recebe um hidrograma de montante (upstream)
def DownstreamRouting(upstream, K, x, T):
    # Coeficientes
    C0 = (T - (2 * K * x)) / ((2 * K * (1 - x)) + T)
    C1 = (T + (2 * K * x)) / ((2 * K * (1 - x)) + T)
    C2 = ((2 * K * (1 - x)) - T) / ((2 * K * (1 - x)) + T)

    n = len(upstream)
    downstream = [0] * n
    # Valor inicial de jusante é igual ao de montante
    downstream[0] = upstream[0]
    # Loop entre segunda e última entradas
    for i in range(1, n):
        downstream[i] = C0 * upstream[i] + C1 * upstream[i - 1] + C2 * downstream[i - 1]

    return downstream

# Modelo não-linear de Muskingum (de primeira ordem) com método de Runge-Kutta
# de quarta ordem (routing de montante para jusante). Variáveis K, X e m devem
# ser calibradas. I refere-se a input, ou hidrograma de montante, e T ao time step
# envolvido (neste caso, 24 horas)
def DownstreamFORK(K, X, m, T, I):
    if np.isnan(K) or np.isnan(X):
        print('ERRO!')
        sys.exit()
    
    n = len(I)

    # Outflow
    O = [0] * n
    # Valor inicial
    O[0] = I[0]
    # Armazenamento
    S = [0] * n

    In_corr = [0.25 if x == 0 else x for x in I]

    for i in range(n - 1):
        # Armazenamento atual
        S[i] = K * (X * In_corr[i] + (1 - X) * O[i]) ** m
        # Coeficientes
        k1 = (-1 / (1 - X)) * ((S[i] / K) ** (1 / m) - In_corr[i])
        k2 = (-1 / (1 - X)) * (((S[i] + 0.5 * T * k1) / K) ** (1 / m) - 0.5 * (In_corr[i] + In_corr[i + 1]))
        k3 = (-1 / (1 - X)) * (((S[i] + 0.5 * T * k2) / K) ** (1 / m) - 0.5 * (In_corr[i] + In_corr[i + 1]))
        k4 = (-1 / (1 - X)) * (((S[i] + 1.0 * T * k3) / K) ** (1 / m) - In_corr[i + 1])

        if np.isnan(k1) or np.isnan(k2) or np.isnan(k3) or np.isnan(k4):
            print(f'K = {K} \n')
            print(f'X = {X} \n')
            print(f'T = {T} \n')
            print(f'S[i] = {S[i]} \n')
            print(f'k1 = {k1} \n')
            print(f'k2 = {k2} \n')
            print(f'k3 = {k3} \n')
            print(f'k4 = {k4} \n')
            sys.exit()
            # print(S[i])
            # print(K)
            # print(X)
            # print(k1)
            # print(k2)
            # print(k3)
            # print(k4)

        # Armazenamento seguinte
        S[i + 1] = S[i] + T * (k1 + 2 * k2 + 2 * k3 + k4) / 6
        # Outflow seguinte
        O[i + 1] = (1 / (1 - X)) * ((S[i + 1] / K) ** (1 / m) - X * In_corr[i + 1])

        _ = [0 if math.isnan(x) else x for x in O]

    return _
