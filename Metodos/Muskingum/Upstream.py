# previous: solucoes obtidas durante iteracao anterior
# current : solucoes obtidas durante iteracao atual
def TesteDeConvergencia(previous, current):
    # Diferencas; criterio: ser menor ou igual a 0.001
    # Importante: se o hidrograma de jusante conter valores nulos
    # (o que de fato ocorrera em alguns casos dado o projeto), checar
    # e simplesmente continuar
    for i in range(1, len(previous)):
        # Check de nulidade deve vir primeiro
        if previous[i] == 0 or abs((current[i] - previous[i]) / current[i]) <= 0.001:
            continue
        else:
            return False

    return True


# O routing de jusante para montante
# recebe um hidrograma de jusante (downstream)
def UpstreamRouting(downstream, K, x):
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
        rateS = [0] * len(oldI)
        rateS[0] = oldI[0] - downstream[0]
        rateS[len(downstream) - 1] = (S[len(downstream) - 1] - S[len(downstream) - 2]) / (2 * 24.0)
        # Loop para os intermediarios
        for i in range(1, len(downstream) - 1):
            rateS[i] = (S[i + 1] - S[i - 1]) / (2 * 24.0)

        # Smoothing
        smooth = [0] * len(oldI)
        smooth[0] = rateS[0]
        smooth[len(downstream) - 1] = rateS[len(downstream) - 1]
        for i in range(1, len(downstream) - 1):
            smooth[i] = (smooth[i - 1] + (2 * rateS[i]) + rateS[i + 1]) / 4.0

        # Nova estimativa
        newI = [0] * len(oldI)
        for i in range(len(downstream)):
            # Verifica se o dia em questao possui vazao para
            # transportar; caso o dia nao possua, mantem 0
            if downstream[i] != 0:
                newI[i] = downstream[i] + smooth[i]
            else:
                newI[i] = downstream[i]

        # Checagem de convergencia e atualizacao de estimativas
        # com alfa
        check = TesteDeConvergencia(oldI, newI)
        if not check:
            for i in range(len(Ia)):
                Ia[i] = oldI[i] + ((newI[i] - oldI[i]) * alfa)

            k = k + 1

    return newI
