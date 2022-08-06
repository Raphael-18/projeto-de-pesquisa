from Dados.Classes import *
from Metodos.Muskingum.Downstream import *
from Metodos.Muskingum.Upstream   import *
from Metodos.SMAP     import *
from scipy.optimize   import differential_evolution
from Scripts.Graficos import *
import numpy as np

def Modelo(
    obsAtibaia    , obsValinhos    ,    # Captacoes, chuvas e vazoes observadas nos pontos (p/ calibrar SMAP)
    revAtibainha  , revCachoeira   ,    # Despachos observados nos reservatorios (p/ calibrar SMAP)
    prevArtAtibaia, prevArtValinhos,    # 60 dias observados + previsoes artificiais de 10 dias em cada bacia incremental
    Atibaia       , Valinhos       ,    # Bacias (dados p/ SMAP)
    flag          , step                # Flag e time step necessarios para geracao de graficos
                                        # de apoio ao pos-processamento
):
    # 1. Muskingum de jusante ate o ponto de controle de Atibaia
    # K = 4.9 dias (de Atibainha para Atibaia)
    # K = 2.6 dias (de Cachoeira para Atibaia)
    # X = 0.3 (fator de amortecimento geral)
    # p/ Atibainha: necessario subdividir o metodo em 5 passos
    j = 1
    pAtibaia1 = DownstreamRouting(revAtibainha.D, 4.9 / 5, 0.3, 1.0)
    while j < 5:
        pAtibaia1 = DownstreamRouting(pAtibaia1, 4.9 / 5, 0.3, 1.0)
        j = j + 1
    # p/ Cachoeira: necessario subdividir o metodo em 3 passos
    j = 1
    pAtibaia2 = DownstreamRouting(revCachoeira.D, 2.6 / 3, 0.3, 1.0)
    while j < 3:
        pAtibaia2 = DownstreamRouting(pAtibaia2, 2.6 / 3, 0.3, 1.0)
        j = j + 1
    # Somatorio de hidrogramas transladados
    despachado = []
    n = len(revAtibainha.D)
    for i in range(n):
        despachado.append(pAtibaia1[i] + pAtibaia2[i])

    # 2. Muskingum de jusante ate o ponto de controle de Valinhos
    # K = 3.5 dias (de Atibaia para Valinhos)
    # X = 0.3 (fator de amortecimento geral)
    # p/ Valinhos: necessario subdividir o metodo em 4 passos
    j = 1
    pValinhos = DownstreamRouting(obsAtibaia.Q, 3.5 / 4, 0.3, 1.0)
    while j < 4:
        pValinhos = DownstreamRouting(pValinhos, 3.5 / 4, 0.3, 1.0)
        j = j + 1

    # 3. Separacao de vazoes em Valinhos para obter as incrementais
    # A vazao observada na secao corresponde ao que choveu mais o que foi
    # despachado menos a parcela de captacao. Logo, inc. = obs. + cap. - desp.
    incrementaisValinhos = []
    for i in range(n):
        incrementaisValinhos.append(obsValinhos.Q[i] + obsValinhos.C[i] - pValinhos[i])

    # 4.1. Escoamento basico inicial para calibrar modelo SMAP
    Valinhos.EB = 0.95 * min(incrementaisValinhos)

    # 4.2. Calibracao SMAP para Valinhos
    # Condicoes de contorno para variaveis que serao calibradas
    bounds = [[100.0, 2000.0], [0.2, 10.0], [0.0, 20.0]]

    # Funcao objetivo que maximiza NSE (coeficiente de Nash-Sutcliffe)
    def objective1(p):
        Str, k2t, Crec = p
        Q = SMAP(Str, k2t, Crec, obsValinhos, Valinhos)

        a  = 0
        b  = 0
        Qm = np.mean(incrementaisValinhos)
        for i in range(n):
            a += (incrementaisValinhos[i] - Q[i]) ** 2
            b += (incrementaisValinhos[i] - Qm) ** 2

        return a / b

    # Busca por evolucao diferencial
    result1 = differential_evolution(objective1, bounds)
    # Resultados
    # print('Valinhos:')
    # print('Status : %s' % result1['message'])
    # print('Avaliacoes realizadas: %d' % result1['nfev'])
    # Solucao
    solution1   = result1['x']
    evaluation1 = objective1(solution1)
    # print('Solucao: f([%.3f \t %.3f \t %.3f]) = %.3f' % (solution1[0], solution1[1], solution1[2], evaluation1))

    # 5. Separacao de vazoes em Atibaia para obter as incrementais
    # A vazao observada na secao corresponde ao que choveu mais o que foi
    # despachado menos a parcela de captacao. Logo, inc. = obs. + cap. - desp.
    incrementaisAtibaia = []
    for i in range(n):
        incrementaisAtibaia.append(obsAtibaia.Q[i] + obsAtibaia.C[i] - despachado[i])

    # 6.1. Escoamento basico inicial para calibrar modelo SMAP
    Atibaia.EB = 0.95 * min(incrementaisAtibaia)

    # 6.2. Calibracao SMAP para Atibaia
    # Funcao objetivo que maximiza NSE (coeficiente de Nash-Sutcliffe)
    def objective2(p):
        Str, k2t, Crec = p
        Q = SMAP(Str, k2t, Crec, obsAtibaia, Atibaia)

        a  = 0
        b  = 0
        Qm = np.mean(incrementaisAtibaia)
        for i in range(n):
            a += (incrementaisAtibaia[i] - Q[i]) ** 2
            b += (incrementaisAtibaia[i] - Qm) ** 2

        return a / b

    # Busca por evolucao diferencial
    result2 = differential_evolution(objective2, bounds)
    # Resultados
    # print()
    # print('Atibaia:')
    # print('Status : %s' % result2['message'])
    # print('Avaliacoes realizadas: %d' % result2['nfev'])
    # Solucao
    solution2   = result2['x']
    evaluation2 = objective2(solution2)
    # print('Solucao: f([%.3f \t %.3f \t %.3f]) = %.3f' % (solution2[0], solution2[1], solution2[2], evaluation2))

    # 7. Calculo de vazoes previstas com parametros SMAP calibrados para cada sub-bacia
    # O vetor de previsoes artificias e formado por 60 observacoes + 10 previsoes (70 dias continuos)
    calcAtibaia  = SMAP(solution2[0], solution2[1], solution2[2], prevArtAtibaia , Atibaia )
    calcValinhos = SMAP(solution1[0], solution1[1], solution1[2], prevArtValinhos, Valinhos)

    # GERACAO DE GRAFICOS
    if flag == 'comGraficos':
        NSE = [[0] * 2 for l in range(1)]
        NSEAtibaia  = 1 - evaluation2
        NSEValinhos = 1 - evaluation1
        NSE[0][0] = NSEAtibaia
        NSE[0][1] = NSEValinhos

        ChuvaVazao(
            obsAtibaia         , obsValinhos         ,
            incrementaisAtibaia, incrementaisValinhos,
            prevArtAtibaia     , prevArtValinhos     ,
            calcAtibaia        , calcValinhos        ,
            NSE                , step
        )

    # 8.1. Verificacao de atendimento ao minimo outorgavel em Valinhos (10 m3/s)
    # e a captacao media de Valinhos durante o periodo de observacao para
    # repasse para o hidrograma que sera deslocado ate Atibaia
    m = len(calcValinhos)
    deficitValinhos = []
    for i in range(m):
        if calcValinhos[i] > 10 + np.mean(obsValinhos.C):
            deficitValinhos.append(0)
        else:
            deficitValinhos.append(10 + np.mean(obsValinhos.C) - calcValinhos[i])

    # 8.2. Muskingum para Atibaia
    # K = 3.5 dias (de Valinhos para Atibaia)
    # X = 0.3 (fator de amortecimento geral)
    upAtibaia = UpstreamRouting(deficitValinhos, 3.5, 0.3, 1.0)

    # 9.1. Verificacao de atendimento ao minimo outorgavel em Atibaia (2 m3/s)
    # e a captacao media de Atibaia durante o periodo de observacao
    deficitAtibaia1 = []
    for i in range(m):
        if calcAtibaia[i] > 2 + np.mean(obsAtibaia.C):
            deficitAtibaia1.append(0)
        else:
            deficitAtibaia1.append(2 + np.mean(obsAtibaia.C) - calcAtibaia[i])

    # 9.2. Verificacao com o translado de Valinhos para Atibaia
    deficitAtibaia2 = []
    for i in range(m):
        if upAtibaia[i] != 0:
            if calcAtibaia[i] > upAtibaia[i]:
                deficitAtibaia2.append(0)
            else:
                deficitAtibaia2.append(upAtibaia[i] - calcAtibaia[i])
        else:
            deficitAtibaia2.append(0)

    # 10. Necessario comparar a maior diferenca nao nula entre
    # os dois deficits antes de dividir para os reservatorios
    pReservatorios = []
    for i in range(m):
        pReservatorios.append(max(deficitAtibaia1[i], deficitAtibaia2[i]))

    # 11. Regra simples: separar vazoes ao meio e encaminhar para
    # Atibainha e Cachoeira
    for i in range(m):
        pReservatorios[i] /= 2.0
    # Muskingum para Atibainha
    # K = 4.9 dias (de Atibaia para Atibainha)
    # X = 0.3 (fator de amortecimento geral)
    pAtibainha = UpstreamRouting(pReservatorios, 4.9, 0.3, 1.0)
    # Muskingum para Cachoeira
    # K = 2.6 dias (de Atibaia para Cachoeira)
    # X = 0.3 (fator de amortecimento geral)
    pCachoeira = UpstreamRouting(pReservatorios, 2.6, 0.3, 1.0)

    # GERACAO DE GRAFICOS
    if flag == 'comGraficos':
        Routings(
            obsAtibaia     , deficitValinhos, pReservatorios,
            upAtibaia      , pAtibainha     , pCachoeira    ,
            step
        )

    # 12. Decisao de despacho em Atibainha e Cachoeira
    # A decisao e o despacho na posicao 60: 0 e o primeiro dia e 59
    # o ultimo dia observado (01/03/21 em diante).
    decisao = Decisao(
        Atibainha = pAtibainha[60],
        Cachoeira = pCachoeira[60]
    )

    return decisao
