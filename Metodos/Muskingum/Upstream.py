# previous: solucoes obtidas durante iteracao anterior
# current : solucoes obtidas durante iteracao atual
def TesteDeConvergencia(previous, current):
    # Diferencas; criterio: ser menor ou igual a 0.001
    # Importante: se o hidrograma de jusante conter valores nulos
    # (o que de fato ocorrera em alguns casos dado o projeto), checar
    # e simplesmente continuar
    for i in range(1, len(previous)):
        # Check de nulidade deve vir primeiro
        if current[i] == 0 or abs((current[i] - previous[i]) / current[i]) <= 0.001:
            continue
        else:
            return False

    return True

# O routing de jusante para montante
# recebe um hidrograma de jusante (downstream)
def UpstreamRouting(downstream, K, x, T):
    # Iteracao
    k = 1
    # Estimativa inicial
    Ia = [0] * len(downstream)
    for i in range(len(downstream)):
        Ia[i] = downstream[i]
    # Controle de convergencia
    check = False
    # O peso alfa deve ser calibrado por tentativa e erro
    alfa = 0.4

    # Loop ate convergencia
    while not check:
        # Primeira estimativa
        oldI = Ia

        # Storage para todos os dados
        S = [0] * len(oldI)
        for i in range(len(downstream)):
            S[i] = K * ((x * oldI[i]) + ((1 - x) * downstream[i]))

        # Derivadas para primeiro e ultimo pontos
        rateS    = [0] * len(oldI)
        rateS[0] = oldI[0] - downstream[0]
        rateS[len(downstream) - 1] = (S[len(downstream) - 1] - S[len(downstream) - 2]) / (2 * T)
        # Loop para os intermediarios
        for i in range(1, len(downstream) - 1):
            rateS[i] = (S[i + 1] - S[i - 1]) / (2 * T)

        # Smoothing
        smooth    = [0] * len(oldI)
        smooth[0] = rateS[0]
        smooth[len(downstream) - 1] = rateS[len(downstream) - 1]
        for i in range(1, len(downstream) - 1):
            smooth[i] = (smooth[i - 1] + (2 * rateS[i]) + rateS[i + 1]) / 4.0

        # Nova estimativa
        newI = [0] * len(oldI)
        for i in range(len(downstream)):
            # Verifica se o dia em questao possui vazao para
            # transportar; caso o dia nao possua, mantem 0
            # if downstream[i] > 0 and smooth[i] > 0: # Essa condicao esta correta?
            #     newI[i] = downstream[i] + smooth[i]
            # else:
            #     newI[i] = downstream[i]
            newI[i] = downstream[i] + smooth[i]

        # Checagem de convergencia e atualizacao de estimativas
        # com alfa
        check = TesteDeConvergencia(oldI, newI)
        if not check:
            for i in range(len(Ia)):
                Ia[i] = oldI[i] + ((newI[i] - oldI[i]) * alfa)

            k = k + 1

    return newI

# Modelo nao-linear de Muskingum (de primeira ordem) com metodo de Runge-Kutta
# de quarta ordem (routing de jusante para montante). Variaveis K, X e m devem
# ser calibradas. O refere-se a output, ou hidrograma de jusante, e T ao time step
# envolvido (neste caso, 24 horas)
def UpstreamFORK(K, X, m, T, O):
    n = len(O)

    # Inflow
    I = [0] * n
    # Valor inicial
    I[n - 1] = O[n - 1]

    # Armazenamento, taxa de variacao
    S = [0] * n

    for i in range(n - 1, 0, -1):
        # Armazenamento
        S[i] = K * (X * I[i] + (1 - X) * O[i]) ** m
        # Coeficientes
        k1 = (1 / X) * ((S[i] / K) ** (1 / m) - O[i])
        k2 = (1 / X) * (((S[i] + 0.5 * T * k1) / K) ** (1 / m) - (0.5 * (O[i] + O[i - 1])))
        k3 = (1 / X) * (((S[i] + 0.5 * T * k2) / K) ** (1 / m) - (0.5 * (O[i] + O[i - 1])))
        k4 = (1 / X) * (((S[i] + 1.0 * T * k3) / K) ** (1 / m) - O[i - 1])
        # Armazenamento em t - 1 (passo anterior)
        S[i - 1] = S[i] - T * (k1 + 2 * k2 + 2 * k3 + k4) / 6
        # Inflow em t - 1 (passo anterior)
        I[i - 1] = (1 / X) * ((S[i - 1] / K) ** (1 / m)) - ((1 - X) / X) * O[i - 1]

    return I
