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
    n = len(I)

    # Outflow
    O = [0] * n
    # Valor inicial
    O[0] = I[0]
    # Armazenamento
    S = [0] * n

    for i in range(n - 1):
        # Armazenamento atual
        S[i] = K * (X * I[i] + (1 - X) * O[i]) ** m
        # Coeficientes
        k1 = (-1 / (1 - X)) * ((S[i] / K) ** (1 / m) - I[i])
        k2 = (-1 / (1 - X)) * (((S[i] + 0.5 * T * k1) / K) ** (1 / m) - 0.5 * (I[i] + I[i + 1]))
        k3 = (-1 / (1 - X)) * (((S[i] + 0.5 * T * k2) / K) ** (1 / m) - 0.5 * (I[i] + I[i + 1]))
        k4 = (-1 / (1 - X)) * (((S[i] + 1.0 * T * k3) / K) ** (1 / m) - I[i + 1])
        # Armazenamento seguinte
        S[i + 1] = S[i] + T * (k1 + 2 * k2 + 2 * k3 + k4) / 6
        # Outflow seguinte
        O[i + 1] = (1 / (1 - X)) * ((S[i + 1] / K) ** (1 / m) - X * I[i + 1])

    return O
