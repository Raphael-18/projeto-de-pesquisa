from Metodos.Muskingum.Downstream import *
from Metodos.Muskingum.Upstream   import *
from Metodos.SMAP        import *
from Metodos.Otimizacoes import *
from scipy.optimize      import differential_evolution
import numpy  as np
import pandas as pd

def Calibracao(
        obsAtibaia  , obsValinhos ,        # Captacoes, chuvas e vazoes observadas nos pontos
        revAtibainha, revCachoeira,        # Despachos observados nos reservatorios
        Atibaia     , Valinhos    ,        # Bacias
        FO                                 # Funcao objetivo p/ otimizacoes
):
    # 1. Muskingum de jusante ate o ponto de controle de Atibaia:
    # O modelo utilizara como parametros duas trincas de variaveis Muskingum
    # (K1, X1, m1) p/ Atibainha e (K2, X2, m2) p/ Cachoeira e também uma quina
    # de variaveis SMAP (Str, k2t, Crec, TUin, EBin). O objetivo sera minimizar
    # as diferencas entre as vazoes incrementais calculadas com o routing hidrologico
    # e aquelas obtidas com o modulo chuva-vazao
    # Condicoes de contorno para variaveis que serao calibradas
    bounds = [
        [1000.0, 2000.0],       # Str
        [   0.2,    4.0],       # k2t
        [   0.0,    1.0],       # Crec
        [   0.0,    1.0],       # TUin
        [   0.0,    9.2],       # EBin
        [  60.0,   80.0],       # K1 (entre 2.5 e 3.3 dias)
        [   0.2,    0.5],       # X1
        [   1.1,    1.3],       # m1 (forcando o modelo a nao escolher m = 1)
        [  60.0,   80.0],       # K2 (entre 2.5 e 3.3 dias)
        [   0.2,    0.5],       # X2
        [   1.1,    1.3]        # m2 (forcando o modelo a nao escolher m = 1)
    ]

    n = len(obsAtibaia.Q)

    # Funcao objetivo
    def objective(p):
        # Sujeitos a calibracao
        Str, k2t, Crec, TUin, EBin, K1, X1, m1, K2, X2, m2 = p

        # Routing de jusante nao linear 1: de Atibainha para Atibaia
        Q1 = DownstreamFORK(K1, X1, m1, 24.0, revAtibainha.D)
        # Routing de jusante nao linear 2: de Cachoeira para Atibaia
        Q2 = DownstreamFORK(K2, X2, m2, 24.0, revCachoeira.D)

        # Junto ao ponto de controle, a vazao observada equivale a uma parcela
        # despachada de cada reservatorio mais uma parcela incremental de eventos chuvosos
        # menos uma parcela captada entre as barragens e a propria secao
        inc1 = [0] * n
        for j in range(n):
            inc1[j] = obsAtibaia.Q[j] - (Q1[j] + Q2[j]) + obsAtibaia.C[j]

        # Segundo vetor incremental ("obs")
        inc2 = SMAP(Str, k2t, Crec, TUin, EBin, obsAtibaia, Atibaia)

        # Restricao positiva aos routings calculados e as vazoes incrementais
        minQ1, minQ2 = min(Q1), min(Q2)
        res1 , res2  = min(inc1), min(inc2)
        if minQ1 < 0 or minQ2 < 0 or res1 < 0 or res2 < 0:
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
    print('Muskingum de jusante e SMAP')
    print('Atibaia:')
    print('Status: %s' % result['message'])
    print('Avaliacoes realizadas: %d' % result['nfev'])
    # Solucao
    solution   = result['x']
    evaluation = objective(solution)
    print('Solucao: \n'
          'f = ( \n'
          '\t[Str = %.3f \n\t k2t = %.3f \n\t Crec = %.3f \n\t TUin = %.3f \n\t EBin = %.3f \n\t K1 = %.3f \n\t X1 = %.3f \n\t m1 = %.3f \n\t K2 = %.3f \n\t X2 = %.3f \n\t m2 = %.3f]'
          % (
              solution[0], solution[1], solution[2], solution[3], solution[4], solution[5], solution[6], solution[7],
              solution[8], solution[9], solution[10]))
    if FO == 1:
        print(') = %.3f' % (1 - evaluation))
    else:
        print(') = %.3f' % evaluation)

    # Armazenamento em dicionario para utilizacao durante etapa de previsao
    # (K, X e m com final 1 referem-se a Atibainha; aqueles com final 2 sao de Cachoeira)
    paramsAtibaia = {
        'Str' : solution[0]  ,
        'k2t' : solution[1]  ,
        'Crec': solution[2]  ,
        'K1'  : [solution[5]],
        'X1'  : [solution[6]],
        'm1'  : [solution[7]],
        'K2'  : [solution[8]],
        'X2'  : [solution[9]],
        'm2'  : [solution[10]]
    }

    # 2. Checagem de incrementais e conversao chuva-vazao para o periodo observado em Atibaia:
    # As incrementais sao necessarias para averiguar como as vazoes obtidas com os parametros calibrados
    # adequam-se aos dados "observados" (tambem advindos de uma calibracao propria, devido a parcela de despacho)
    newQ1 = DownstreamFORK(solution[5], solution[6], solution[7] , 24.0, revAtibainha.D)
    newQ2 = DownstreamFORK(solution[8], solution[9], solution[10], 24.0, revCachoeira.D)

    incAtibaia = [0] * n
    for j in range(n):
        incAtibaia[j] = obsAtibaia.Q[j] - (newQ1[j] + newQ2[j]) + obsAtibaia.C[j]

    calcAtibaia = SMAP(solution[0], solution[1], solution[2], solution[3], solution[4], obsAtibaia, Atibaia)

    # 3. Muskingum de jusante ate o ponto de controle de Valinhos:
    # Semelhante ao passo 1., porem com uma trinca de variaveis Muskingum (K, X, m) ao inves de duas
    # Condicoes de contorno para variaveis que serao calibradas
    bounds = [
        [1000.0, 2000.0],       # Str
        [   0.2,    6.0],       # k2t
        [   0.0,   20.0],       # Crec
        [   0.0,    1.0],       # TUin
        [   0.0,   40.0],       # EBin
        [  60.0,  120.0],       # K (entre 2.5 e 5 dias)
        [   0.2,    0.5],       # X
        [   1.1,    1.3]        # m (forcando o modelo a nao escolher m = 1)
    ]

    # Funcao objetivo
    def objective(p):
        # Sujeitos a calibracao
        Str, k2t, Crec, TUin, EBin, K, X, m = p

        # Routing de jusante nao linear: de Atibaia para Valinhos
        Q = DownstreamFORK(K, X, m, 24.0, obsAtibaia.Q)

        # Junto ao ponto de controle, a vazao observada equivale a uma parcela
        # despachada de cada reservatorio mais uma parcela incremental de eventos chuvosos
        # menos uma parcela captada entre as barragens e a propria secao
        inc1 = [0] * n
        for j in range(n):
            inc1[j] = obsValinhos.Q[j] - Q[j] + obsValinhos.C[j]

        # Segundo vetor incremental ("obs")
        inc2 = SMAP(Str, k2t, Crec, TUin, EBin, obsValinhos, Valinhos)

        # Restricao positiva aos routings calculados e as vazoes incrementais
        minQ, res1, res2 = min(Q), min(inc1), min(inc2)
        if minQ < 0 or res1 < 0 or res2 < 0:
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
    print('Valinhos:')
    print('Status: %s' % result['message'])
    print('Avaliacoes realizadas: %d' % result['nfev'])
    # Solucao
    solution   = result['x']
    evaluation = objective(solution)
    print('Solucao: \n'
          'f = ( \n'
          '\t[Str = %.3f \n\t k2t = %.3f \n\t Crec = %.3f \n\t TUin = %.3f \n\t EBin = %.3f \n\t K = %.3f \n\t X = %.3f \n\t m = %.3f]'
          % (
              solution[0], solution[1], solution[2], solution[3], solution[4], solution[5], solution[6], solution[7]))
    if FO == 1:
        print(') = %.3f\n' % (1 - evaluation))
    else:
        print(') = %.3f\n' % evaluation)

    # Armazenamento em dicionario para utilizacao durante etapa de previsao
    paramsValinhos = {
        'Str' : solution[0]  ,
        'k2t' : solution[1]  ,
        'Crec': solution[2]  ,
        'K'   : [solution[5]],
        'X'   : [solution[6]],
        'm'   : [solution[7]]
    }

    # 4. Checagem de incrementais e conversao chuva-vazao para o periodo observado em Valinhos:
    # As incrementais sao necessarias para averiguar como as vazoes obtidas com os parametros calibrados
    # adequam-se aos dados "observados" (tambem advindos de uma calibracao propria, devido a parcela de despacho)
    newQ = DownstreamFORK(solution[5], solution[6], solution[7], 24.0, obsAtibaia.Q)

    incValinhos = [0] * n
    for j in range(n):
        incValinhos[j] = obsValinhos.Q[j] - newQ[j] + obsValinhos.C[j]

    calcValinhos = SMAP(solution[0], solution[1], solution[2], solution[3], solution[4], obsValinhos, Valinhos)

    # 5. Muskingum de montante ate o ponto de controle de Atibaia:
    # Depois de otimizar o modulo chuva-vazao para cada sub-bacia, e necessario tomar as
    # vazoes incrementais aferidas durante o periodo de observacao para calibrar o modulo de routing
    # inverso, ou upstream routing (de jusante para montante). Em Valinhos:
    #   Qobs.Vali. = Qinc. - capt. + Desp.Atib.
    # Portanto, convem retroceder Desp.Atib. e tomar como referencia Qobs.Atib. para calibracao
    desp = [0] * n
    for j in range(n):
        desp[j] = obsValinhos.Q[j] + obsValinhos.C[j] - incValinhos[j]

    # Condicoes de contorno para variaveis que serao calibradas
    bounds = [
        [84.0, 99.0],           # K (entre 3.5 e 4.1 dias)
        [ 0.2,  0.5],           # X (necessario controlar limite inferior de X para que o modelo nao execute potenciacao complexa)
        [ 1.1,  1.2]            # m (forcando o modelo a nao escolher m = 1)
    ]                           #   (valores elevados de m tornam o hidrograma transladado uma linha reta, ou 'flat'. Necessario conter limite superior)

    # Funcao objetivo
    def objective(p):
        # Sujeitos a calibracao
        K, X, m = p

        # Routing de montante nao linear: de Valinhos para Atibaia
        Q = UpstreamFORK(K, X, m, 24.0, desp)

        # Restricao positiva ao routing calculado
        res = min(Q)
        if res < 0:
            return np.inf
        else:
            # Metrica utilizada para otimizacao
            match FO:
                case 1:
                    # NSE: Nash-Sutcliffe
                    return NSE(obsAtibaia.Q, Q)

                case 2:
                    # SSQ: Sum of Squares of Deviations
                    return SSQ(obsAtibaia.Q, Q)

                case 3:
                    # RMSE: Root-Mean-Square Error
                    return RMSE(obsAtibaia.Q, Q)

    # Busca por evolucao diferencial
    result = differential_evolution(objective, bounds, maxiter=1000)
    # Resultados
    print('Muskingum de montante')
    print('Valinhos:')
    print('Status: %s' % result['message'])
    print('Avaliacoes realizadas: %d' % result['nfev'])
    # Solucao
    solution   = result['x']
    evaluation = objective(solution)
    print('Solucao: \n'
          'f = ( \n'
          '\t[K = %.3f \n\t X = %.3f \n\t m = %.3f]'
          % (solution[0], solution[1], solution[2]))
    if FO == 1:
        print(') = %.3f\n' % (1 - evaluation))
    else:
        print(') = %.3f\n' % evaluation)

    # Armazenamento para plotagem
    upVA = UpstreamFORK(solution[0], solution[1], solution[2], 24.0, desp)

    # Armazenamento em dicionario para utilizacao durante etapa de previsao
    paramsValinhos['K'] += [solution[0]]
    paramsValinhos['X'] += [solution[1]]
    paramsValinhos['m'] += [solution[2]]

    # 6. Muskingum de montante ate reservatorios:
    # Depois de otimizar o modulo chuva-vazao para cada sub-bacia, e necessario tomar as
    # vazoes incrementais aferidas durante o periodo de observacao para calibrar o modulo de routing
    # reverso, ou upstream routing (de jusante para montante). Em Atibaia:
    #   Qobs.Atib. = Qinc. - capt. + (Desp.Atibain. + Desp.Cach.)
    #   (Desp.Atibain. + Desp.Cach.) = Reserv.
    # Como a descarga observada junto a secao corresponde a soma de duas parcelas, cada qual de uma barragem,
    # e preciso retroceder um percentual de Res. para comparar com Desp.Atibain.obs. O mesmo vale para
    # Res. e Desp.Cach.obs. Uma forma e realizar o routing de Res. hora multiplicado por um coeficiente
    # alfa (p/ Atibainha), hora multiplicado por beta (p/ Cachoeira). A titulo de simplificacao, tomou-se
    # alfa = beta = 0.5
    reserv = [0] * n
    for j in range(n):
        reserv[j] = obsAtibaia.Q[j] + obsAtibaia.C[j] - incAtibaia[j]

    # Ajuste necessario para evitar exponenciacao negativa por ordenada final de hidrograma proxima de 0
    minAtibainha = revAtibainha.D[n - 1]
    minCachoeira = revCachoeira.D[n - 1]
    minReserv    = min(minAtibainha, minCachoeira)
    if reserv[n - 1] < minReserv:
        reserv[n - 1] = minReserv

    # Condicoes de contorno para variaveis que serao calibradas
    bounds = [
        [120.0, 180.0],         # K (entre 5 e 7.5 dias)
        [  0.4,   0.5],         # X (necessario controlar limite inferior para que o modelo nao execute potenciacao complexa)
        [  1.1,   1.2]          # m (forcando o modelo a nao escolher m = 1)
    ]

    # Funcao objetivo
    def objective(p):
        # Sujeitos a calibracao
        K, X, m = p

        # Routing de montante nao linear: de Atibaia para Atibainha
        Q = UpstreamFORK(K, X, m, 24.0, list(np.multiply(reserv, 0.5)))

        # Restricao positiva ao routing calculado
        res = min(Q)
        if res < 0:
            return np.inf
        else:
            # Metrica utilizada para otimizacao
            match FO:
                case 1:
                    # NSE: Nash-Sutcliffe
                    return NSE(revAtibainha.D, Q)

                case 2:
                    # SSQ: Sum of Squares of Deviations
                    return SSQ(revAtibainha.D, Q)

                case 3:
                    # RMSE: Root-Mean-Square Error
                    return RMSE(revAtibainha.D, Q)

    # Busca por evolucao diferencial
    result = differential_evolution(objective, bounds, maxiter=1000)
    # Resultados
    print('Muskingum de montante')
    print('Atibaia para Atibainha:')
    print('Status : %s' % result['message'])
    print('Avaliacoes realizadas: %d' % result['nfev'])
    # Solucao
    solution   = result['x']
    evaluation = objective(solution)
    print('Solucao: \n'
          'f = ( \n'
          '\t[K = %.3f \n\t X = %.3f \n\t m = %.3f]'
          % (solution[0], solution[1], solution[2]))
    if FO == 1:
        print(') = %.3f\n' % (1 - evaluation))
    else:
        print(') = %.3f\n' % evaluation)

    # Armazenamento para plotagem
    upAA = UpstreamFORK(solution[0], solution[1], solution[2], 24.0, list(np.multiply(reserv, 0.5)))

    # Armazenamento em dicionario para utilizacao durante etapa de previsao
    paramsAtibaia['K1'] += [solution[0]]
    paramsAtibaia['X1'] += [solution[1]]
    paramsAtibaia['m1'] += [solution[2]]

    # Mesmo procedimento, porem para Cachoeira e com beta
    beta = 0.5

    # Condicoes de contorno para variaveis que serao calibradas
    bounds = [
        [120.0, 180.0],         # K (entre 5 e 7.5 dias)
        [  0.4,   0.5],         # X (necessario controlar limite inferior para que o modelo nao execute potenciacao complexa)
        [  1.1,   1.3]          # m (forcando o modelo a nao escolher m = 1)
    ]

    # Funcao objetivo
    def objective(p):
        # Sujeitos a calibracao
        K, X, m = p

        # Routing de montante nao linear: de Atibaia para Cachoeira
        Q = UpstreamFORK(K, X, m, 24.0, list(np.multiply(reserv, beta)))

        # Restricao positiva ao routing calculado
        res = min(Q)
        if res < 0:
            return np.inf
        else:
            # Metrica utilizada para otimizacao
            match FO:
                case 1:
                    # NSE: Nash-Sutcliffe
                    return NSE(revCachoeira.D, Q)

                case 2:
                    # SSQ: Sum of Squares of Deviations
                    return SSQ(revCachoeira.D, Q)

                case 3:
                    # RMSE: Root-Mean-Square Error
                    return RMSE(revCachoeira.D, Q)

    # Busca por evolucao diferencial
    result = differential_evolution(objective, bounds, maxiter=1000)
    # Resultados
    print('Muskingum de montante')
    print('Atibaia para Cachoeira:')
    print('Status : %s' % result['message'])
    print('Avaliacoes realizadas: %d' % result['nfev'])
    # Solucao
    solution   = result['x']
    evaluation = objective(solution)
    print('Solucao: \n'
          'f = ( \n'
          '\t[K = %.3f \n\t X = %.3f \n\t m = %.3f]'
          % (solution[0], solution[1], solution[2]))
    if FO == 1:
        print(') = %.3f\n' % (1 - evaluation))
    else:
        print(') = %.3f\n' % evaluation)

    # Armazenamento para plotagem
    upAC = UpstreamFORK(solution[0], solution[1], solution[2], 24.0, list(np.multiply(reserv, beta)))

    # Armazenamento em dicionario para utilizacao durante etapa de previsao
    paramsAtibaia['K2'] += [solution[0]]
    paramsAtibaia['X2'] += [solution[1]]
    paramsAtibaia['m2'] += [solution[2]]

    # Inc1: via SMAP
    # Inc2: via Muskingum nao-linear tradicional
    resultados = pd.DataFrame(data =
                              {
                                  'Dia'              : obsAtibaia.t ,
                                  'Pluv. de Atibaia' : obsAtibaia.P ,
                                  'Pluv. de Valinhos': obsValinhos.P,
                                  'Inc2 de Atibaia'  : incAtibaia   ,
                                  'Inc1 de Atibaia'  : calcAtibaia  ,
                                  'Inc2 de Valinhos' : incValinhos  ,
                                  'Inc1 de Valinhos' : calcValinhos ,
                                  'Upst. VA': upVA,
                                  'Upst. AA': upAA,
                                  'Upst. AC': upAC
                              })

    return paramsAtibaia, paramsValinhos, resultados
