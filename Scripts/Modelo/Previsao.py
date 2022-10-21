from Dados.Classes import *
from Metodos.Muskingum.Downstream import *
from Metodos.Muskingum.Upstream   import *
from Metodos.SMAP        import *
from Metodos.Otimizacoes import *
from scipy.optimize      import differential_evolution
import numpy as np

def Previsao(
        obsAtibaia   , obsValinhos   ,     # Chuvas observadas nos pontos (p/ calibrar TUin e EBin)
        prevAtibaia  , prevValinhos  ,     # 30 dias observados + previsoes de 7 dias em cada bacia incremental
        paramsAtibaia, paramsValinhos,     # Parametros calibrados com 4 meses de observacao
        revAtibainha , revCachoeira  ,     # Despachos observados nos reservatorios (p/ calibrar TUin e EBin)
        startAtibaia , startValinhos ,     # Dicionarios para armazenamento de parametros apos calibracao
        Atibaia      , Valinhos      ,     # Bacias (dados p/ SMAP)
        FO           , step                # Funcao objetivo p/ otimizacoes e variavel de controle de iteracoes
):
    # 1. Translado de vazoes observadas em Atibaia para calibrar TUin e EBin
    # e invocar o modelo SMAP para previsao em Valinhos
    bounds = [
        [0.0,  1.0],            # TUin
        [0.0, 40.0]             # EBin
    ]

    n = len(obsAtibaia.Q)

    # Routing de jusante nao linear de Atibaia para Valinhos
    Q = DownstreamFORK(
        paramsValinhos['K'][0],
        paramsValinhos['X'][0],
        paramsValinhos['m'][0],
        24.0, obsAtibaia.Q
    )

    # Junto ao ponto de controle, a vazao observada equivale a uma parcela
    # despachada de cada reservatorio mais uma parcela incremental de eventos chuvosos
    # menos uma parcela captada entre as barragens e a propria secao
    inc1 = [0] * n
    for j in range(n):
        inc1[j] = obsValinhos.Q[j] - Q[j] + obsValinhos.C[j]

    # Funcao objetivo
    def objective(p):
        # Sujeitos a calibracao
        TUin, EBin = p

        # Segundo vetor incremental ("obs")
        inc2 = SMAP(
            paramsValinhos['Str']  ,
            paramsValinhos['k2t']  ,
            paramsValinhos['Crec'] ,
            TUin, EBin, obsValinhos, Valinhos)

        # Restricao positiva aos routings calculados e as vazoes incrementais
        minQ = min(inc2)
        if minQ < 0:
            return np.inf
        else:
            # Metrica utilizada para otimizacao
            match FO:
                case 1:
                    # NSE: Nash-Sutcliffe
                    return NSE(inc1, inc2)

                case 2:
                    # SSQ: Sum of Squares of Deviations
                    return SSQ(inc1, inc2)

                case 3:
                    # RMSE: Root-Mean-Square Error
                    return RMSE(inc1, inc2)

    # Busca por evolucao diferencial
    result = differential_evolution(objective, bounds, maxiter = 1000)
    # Resultados
    print()
    print('Step: %d' % step)
    print('SMAP em Valinhos:')
    print('Status: %s' % result['message'])
    print('Avaliacoes realizadas: %d' % result['nfev'])
    # Solucao
    solution   = result['x']
    evaluation = objective(solution)
    print('Solucao: \n'
          'f = ( \n'
          '\t[TUin = %.3f \n\t EBin = %.3f]'
          % (solution[0], solution[1]))
    if FO == 1:
        print(') = %.3f' % (1 - evaluation))
    else:
        print(') = %.3f' % evaluation)

    startValinhos['TUin'] += [solution[0]]
    startValinhos['EBin'] += [solution[1]]

    # 2. Vetor de vazoes continuas (observado 30 dias + previsto 7 dias)
    calcValinhos = SMAP(
            paramsValinhos['Str']  ,
            paramsValinhos['k2t']  ,
            paramsValinhos['Crec'] ,
            solution[0], solution[1], prevValinhos, Valinhos)

    # 3. Translado de despachos observadas em Atibainha e Cachoeira para calibrar TUin e EBin
    # e invocar o modelo SMAP para previsao em Atibaia
    bounds = [
        [0.0, 1.0],            # TUin
        [0.0, 9.2]             # EBin
    ]

    # Routing de jusante nao linear de Atibainha para Atibaia (#1) e de Cachoeira para Atibaia (#2)
    Q1 = DownstreamFORK(
        paramsAtibaia['K1'][0],
        paramsAtibaia['X1'][0],
        paramsAtibaia['m1'][0],
        24.0, revAtibainha.D)
    Q2 = DownstreamFORK(
        paramsAtibaia['K2'][0],
        paramsAtibaia['X2'][0],
        paramsAtibaia['m2'][0],
        24.0, revCachoeira.D)

    # Junto ao ponto de controle, a vazao observada equivale a uma parcela
    # despachada de cada reservatorio mais uma parcela incremental de eventos chuvosos
    # menos uma parcela captada entre as barragens e a propria secao
    inc1 = [0] * n
    for j in range(n):
        inc1[j] = obsAtibaia.Q[j] - (Q1[j] + Q2[j]) + obsAtibaia.C[j]

    # Funcao objetivo
    def objective(p):
        # Sujeitos a calibracao
        TUin, EBin = p

        # Segundo vetor incremental ("obs")
        inc2 = SMAP(
            paramsAtibaia['Str']  ,
            paramsAtibaia['k2t']  ,
            paramsAtibaia['Crec'] ,
            TUin, EBin, obsAtibaia, Atibaia)

        # Restricao positiva aos routings calculados e as vazoes incrementais
        minQ = min(inc2)
        if minQ < 0:
            return np.inf
        else:
            # Metrica utilizada para otimizacao
            match FO:
                case 1:
                    # NSE: Nash-Sutcliffe
                    return NSE(inc1, inc2)

                case 2:
                    # SSQ: Sum of Squares of Deviations
                    return SSQ(inc1, inc2)

                case 3:
                    # RMSE: Root-Mean-Square Error
                    return RMSE(inc1, inc2)

    # Busca por evolucao diferencial
    result = differential_evolution(objective, bounds, maxiter=1000)
    # Resultados
    print()
    print('SMAP em Atibaia:')
    print('Status: %s' % result['message'])
    print('Avaliacoes realizadas: %d' % result['nfev'])
    # Solucao
    solution   = result['x']
    evaluation = objective(solution)
    print('Solucao: \n'
          'f = ( \n'
          '\t[TUin = %.3f \n\t EBin = %.3f]'
          % (solution[0], solution[1]))
    if FO == 1:
        print(') = %.3f' % (1 - evaluation))
    else:
        print(') = %.3f' % evaluation)

    startAtibaia['TUin'] += [solution[0]]
    startAtibaia['EBin'] += [solution[1]]

    # 4. Vetor de vazoes continuas (observado 30 dias + previsto 7 dias)
    calcAtibaia = SMAP(
        paramsAtibaia['Str'] ,
        paramsAtibaia['k2t'] ,
        paramsAtibaia['Crec'],
        solution[0], solution[1], prevAtibaia, Atibaia)

    # 5. Tomada de decisao:
    # A serie de 30 dias de observacao + 7 dias de previsao em Valinhos sera transladada duas vezes,
    # uma ate o reservatorio de Atibainha com os parametros calibrados por trecho (Valinhos - Atibaia e
    # Atibaia - Atibainha) e outra ate o reservatorio de Cachoeira, de modo semelhante (Valinhos - Atibaia e
    # Atibaia - Cachoeira). Ao chegar em cada barragem, os hidrogramas finais devem ser confrontados com a minima
    # media diaria de Valinhos (10 m3/s) somada a media de captacao em seu periodo de observacao. Caso a ordenada em
    # index = 31 (dia de decisao) seja inferior as demandas, o despacho necessario sera o deficit remanescente;
    # caso contrario, despacha-se o minimo de 0.25 m3/s. Para Atibaia, o procedimento e o mesmo. Sua serie de 30 + 7
    # sera retrocedida duas vezes, uma para cada barragem, e os hidrogramas finais serao comparados com a minima
    # media diaria de 2 m3/s + media de captacao durante os primeiros 30 dias observados. Caso a ordenada em
    # index = 31 (dia de decisao) seja inferior as demandas, o despacho necessario sera o deficit remanescente;
    # caso contrario, despacha-se o minimo outorgado

    # Routings ate barragens:
    decisV = UpstreamFORK(
        paramsValinhos['K'][1],
        paramsValinhos['X'][1],
        paramsValinhos['m'][1],
        24.0, calcValinhos
    )
    # de Valinhos (pt. 1)
    decisVA = UpstreamFORK(
        paramsAtibaia['K1'][1],
        paramsAtibaia['X1'][1],
        paramsAtibaia['m1'][1],
        24.0, list(np.multiply(decisV, 0.5))
    )
    # de Valinhos (pt. 2)
    decisVC = UpstreamFORK(
        paramsAtibaia['K2'][1],
        paramsAtibaia['X2'][1],
        paramsAtibaia['m2'][1],
        24.0, list(np.multiply(decisV, 0.5))
    )
    # de Atibaia (pt. 1)
    decisAA = UpstreamFORK(
        paramsAtibaia['K1'][1],
        paramsAtibaia['X1'][1],
        paramsAtibaia['m1'][1],
        24.0, list(np.multiply(calcAtibaia, 0.5))
    )
    # de Atibaia (pt. 2)
    decisAC = UpstreamFORK(
        paramsAtibaia['K2'][1],
        paramsAtibaia['X2'][1],
        paramsAtibaia['m2'][1],
        24.0, list(np.multiply(calcAtibaia, 0.5))
    )

    # Em Atibainha
    if decisVA[31] < 10 + np.mean(obsValinhos.C):
        defic1 = 10 + np.mean(obsValinhos.C) - decisVA[31]
    else:
        defic1 = 0.25
    if decisAA[31] <  2 + np.mean(obsAtibaia.C):
        defic2 =  2 + np.mean(obsAtibaia.C)  - decisAA[31]
    else:
        defic2 = 0.25
    despAtibainha = max(defic1, defic2)

    # Em Cachoeira
    if decisVC[31] < 10 + np.mean(obsValinhos.C):
        defic1 = 10 + np.mean(obsValinhos.C) - decisVC[31]
    else:
        defic1 = 0.25
    if decisAC[31] <  2 + np.mean(obsAtibaia.C):
        defic2 =  2 + np.mean(obsAtibaia.C)  - decisAC[31]
    else:
        defic2 = 0.25
    despCachoeira = max(defic1, defic2)

    resultado = Decisao(
        Atibainha = despAtibainha,
        Cachoeira = despCachoeira
    )

    return resultado
