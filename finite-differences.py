def ConvergenceTest(previous, current):
    # Diferenças; critério: ser menor ou igual a 0.001
    for i in range(1, len(previous)):
        if abs((current[i] - previous[i]) / current[i]) <= 0.001:
            continue
        else:
            return False

    return True


def FiniteDifference(downstream, K, x, T):
    # Iteração
    k = 1
    # Estimativa inicial
    Ia = [0] * len(downstream)
    for i in range(len(downstream)):
        Ia[i] = downstream[i]
    # Controle de convergência
    check = False
    # O peso alfa deve ser calibrado por tentativa e erro
    alfa = 0.4

    # Loop até convergência
    while not check:
        # Primeira estimativa
        oldI = Ia

        # Storage para todos os dados
        S = [0] * len(oldI)
        for i in range(len(downstream)):
            S[i] = K * ((x * oldI[i]) + ((1 - x) * downstream[i]))

        # Derivadas para primeiro e último pontos
        rateS = [0] * len(oldI)
        rateS[0] = oldI[0] - downstream[0]
        rateS[len(downstream) - 1] = (S[len(downstream) - 1] - S[len(downstream) - 2]) / (2 * T)
        # Loop para os intermediários
        for i in range(1, len(downstream) - 1):
            rateS[i] = (S[i + 1] - S[i - 1]) / (2 * T)

        # Smoothing
        smooth = [0] * len(oldI)
        smooth[0] = rateS[0]
        smooth[len(downstream) - 1] = rateS[len(downstream) - 1]
        for i in range(1, len(downstream) - 1):
            smooth[i] = (smooth[i - 1] + (2 * rateS[i]) + rateS[i + 1]) / 4.0

        # Nova estimativa
        newI = [0] * len(oldI)
        for i in range(len(downstream)):
            newI[i] = downstream[i] + smooth[i]

        # Checagem de convergência e atualização de estimativas
        # com alfa
        check = ConvergenceTest(oldI, newI)
        if not check:
            for i in range(len(Ia)):
                Ia[i] = oldI[i] + ((newI[i] - oldI[i]) * alfa)

            k = k + 1

    return newI


sample = [274.000, 281.679, 303.587, 316.062, 359.749, 421.956, 478.863, 506.048, 517.677, 540.789, 565.437,
          494.374, 653.114, 844.577, 905.357, 973.837, 930.406, 875.011, 776.182, 702.896, 655.923, 614.680,
          597.178, 589.002, 572.407, 573.467, 560.154, 529.137, 474.748, 454.544, 410.279, 371.594, 329.236]

answer = [274.000, 313.839, 354.572, 403.821, 495.436, 566.675, 586.198, 571.509, 574.344, 571.836, 571.427,
          676.532,1026.127,1155.680,1080.610,1000.901, 816.215, 681.269, 568.078, 537.868, 533.825, 534.941,
          551.074, 555.106, 549.040, 543.963, 492.943, 427.976, 376.014, 357.024, 301.012, 273.999, 270.995]

resultado = FiniteDifference(sample, 66.0, 0.0, 24.0)

print("Resultados:")
for i in range(len(resultado)):
    print('%.3f \t %.3f' % (resultado[i], answer[i]))
