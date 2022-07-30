# O routing de montante para jusante
# recebe um hidrograma de montante (upstream)
def DownstreamRouting(upstream, K, x, T):
    # Coeficientes
    C0 = (T - (2 * K * x)) / ((2 * K * (1 - x)) + T)
    C1 = (T + (2 * K * x)) / ((2 * K * (1 - x)) + T)
    C2 = ((2 * K * (1 - x)) - T) / ((2 * K * (1 - x)) + T)

    n = len(upstream)
    downstream = [0] * n
    # Valor inicial de jusante e igual ao de montante
    downstream[0] = upstream[0]
    # Loop entre segunda e ultima entradas
    for i in range(1, n):
        downstream[i] = C0 * upstream[i] + C1 * upstream[i - 1] + C2 * downstream[i - 1]

    return downstream
