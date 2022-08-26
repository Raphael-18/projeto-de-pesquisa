import matplotlib.pyplot as plt

def FORK(m):
    # Tempo de transito, amortecimento
    K, X = 3.5, 0.3
    # Outflow
    O = [2.47009, 2.43915, 2.40861, 2.37844, 2.34866, 17.23663, 15.96501, 13.92656, 12.18385, 10.78502, 14.71313, 12.84354, 19.2795, 18.92476, 16.43397, 15.91862, 13.85649, 12.09774, 10.59467, 9.30975, 8.62209, 7.62157, 23.93988, 20.86482, 19.02764, 16.51971, 14.37035, 18.60134, 16.14606, 14.06106, 12.28281, 10.76611, 9.4726, 8.36917, 7.52131, 8.03666, 7.14668, 6.39277, 5.75, 5.20188, 4.73437, 15.50358, 13.5227, 12.69284, 11.13987, 9.82098, 8.69817, 11.16107, 16.15578, 14.1137, 12.38417, 10.91161, 9.65793, 8.59073, 7.68237, 7.05078, 6.5728, 7.45573, 6.72762, 6.11431, 14.92093, 19.17358, 16.75002, 30.81612, 26.69936, 36.82194, 31.84499, 27.61438, 24.01215, 20.9444]
    n = len(O)

    # Inflow
    I = [0] * n
    # Valor inicial
    I[n - 1] = O[n - 1]

    # Armazenamento, taxa de variacao
    S, dS_dt = [0] * n, [0] * n

    for i in range(n - 1, 0, -1):
        # Armazenamento
        S[i] = K * (X * I[i] + (1 - X) * O[i]) ** m
        # Coeficientes
        k1 = (1 / X) * ((S[i] / K) ** (1 / m) - O[i])
        k2 = (1 / X) * (((S[i] + 0.5 * k1) / K) ** (1 / m) - (0.5 * (O[i] + O[i - 1])))
        k3 = (1 / X) * (((S[i] + 0.5 * k2) / K) ** (1 / m) - (0.5 * (O[i] + O[i - 1])))
        k4 = (1 / X) * (((S[i] + k3) / K) ** (1 / m) - O[i - 1])
        # Taxa de variacao
        dS_dt[i] = (k1 + 2 * k2 + 2 * k3 + k4) / 6

        # Armazenamento no passo anterior
        S[i - 1] = S[i] - dS_dt[i]
        # Inflow no passo anterior
        I[i - 1] = (1 / X) * ((S[i - 1] / K) ** (1 / m)) - ((1 - X) / X) * O[i - 1]

    # Figura
    fig = plt.figure()
    axi = fig.add_subplot(111)
    # Configuracoes
    axi.set_ylim(-5.0, 50.0)
    axi.set_ylabel('Vazão [m³/s]')

    # Eixo x
    t = range(1, n + 1, 1)
    # Output
    axi.plot(t, O, 'C0'  , label='Output')
    # Input
    axi.plot(t, I, 'C1--', label='Input')
    # Limite
    axi.axline((1.0, 0.0), (n, 0.0), color='r')
    axi.legend(loc='upper right')
    # Titulo
    axi.set_title('Upstream routing via método Fourth-Order Runge-Kutta (FORK)', pad=15)

    plt.show()

FORK(m = 1)
