from Dados.Classes import *
from Metodos.Muskingum.Downstream import *
from Metodos.Muskingum.Upstream   import *
from Metodos.SMAP     import *
from scipy.optimize   import differential_evolution
from Scripts.Graficos import *
import numpy as np


def Modelo(
        obsAtibaia    , obsValinhos    ,        # Captacoes, chuvas e vazoes observadas nos pontos (p/ calibrar SMAP)
        revAtibainha  , revCachoeira   ,        # Despachos observados nos reservatorios (p/ calibrar SMAP)
        prevArtAtibaia, prevArtValinhos,        # 60 dias observados + previsoes artificiais de 10 dias em cada bacia incremental
        Atibaia       , Valinhos       ,        # Bacias (dados p/ SMAP)
        flag          , step           ,        # Flag e time step necessarios para geracao de graficos de apoio ao pos-processamento
        FO                                      # Funcao objetivo p/ otimizacoes
):
    # 1. Muskingum de jusante ate o ponto de controle de Atibaia:
    # O modelo utilizara como parametros duas trincas de variaveis Muskingum
    # (K1, X1, m1) p/ Atibainha e (K2, X2, m2) p/ Cachoeira e também uma quina
    # de variaveis SMAP (Str, k2t, Crec, TUin, EBin). O objetivo sera minimizar
    # as diferencas entre as vazoes incrementais calculadas com o routing hidrologico
    # e aquelas obtidas com o modulo chuva-vazao

    # Condicoes de contorno para variaveis que serao calibradas
    bounds = [
        [100.0, 2000.0],                # Str
        [  0.2,   10.0],                # k2t
        [  0.0,   20.0],                # Crec
        [  0.0,    1.0],                # TUin
        [  0.0, obsAtibaia.Q[0]],       # EBin
        [ 60.0,  120.0],                # K1 (entre 2.5 e 5 dias)
        [  0.0,    0.5],                # X1
        [  1.1,    3.0],                # m1 (forcando o modelo a nao escolher m = 1)
        [ 60.0,  120.0],                # K2 (entre 2.5 e 5 dias)
        [  0.0,    0.5],                # X2
        [  1.1,    3.0]                 # m2 (forcando o modelo a nao escolher m = 1)
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

        # Metrica utilizada para otimizacao
        match FO:
            case 1:
                # NSE: Nash-Sutcliffe
                a = 0
                b = 0
                Qm = np.mean(inc1)
                for i in range(n):
                    a += (inc1[i] - inc2[i]) ** 2
                    b += (inc1[i] - Qm) ** 2

                return a / b

            case 2:
                # SSQ: Sum of Squares of Deviation
                a = 0
                for i in range(n):
                    a += ((inc2[i] - inc1[i]) / inc2[i]) ** 2

                return a

            case 3:
                # (I)RMSE: (Inverse) Root-Mean-Square Error
                a = 0
                for i in range(n):
                    a += ((1 / inc1[i]) - (1 / inc2[i])) ** 2

                return np.sqrt(a / n)

    # Busca por evolucao diferencial
    result = differential_evolution(objective, bounds, maxiter=10)
    # Resultados
    print('\n''Muskingum de jusante e SMAP')
    print('Atibaia:')
    print('Status : %s' % result['message'])
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
        objAtibaia = 1 - evaluation
    else:
        print(') = %.3f' % evaluation)
        objAtibaia = evaluation

    # 2. Checagem de incrementais e conversao chuva-vazao para o periodo continuo de 60 + 10 dias em Atibaia:
    # As incrementais sao necessarias para averiguar como as vazoes obtidas com os parametros calibrados
    # adequam-se aos dados "observados" (tambem advindos de uma calibracao propria, devido a parcela de despacho)
    newQ1 = DownstreamFORK(solution[5], solution[6], solution[7] , 24.0, revAtibainha.D)
    newQ2 = DownstreamFORK(solution[8], solution[9], solution[10], 24.0, revCachoeira.D)

    incAtibaia = [0] * n
    for j in range(n):
        incAtibaia[j] = obsAtibaia.Q[j] - (newQ1[j] + newQ2[j]) + obsAtibaia.C[j]

    calcAtibaia = SMAP(solution[0], solution[1], solution[2], solution[3], solution[4], prevArtAtibaia, Atibaia)

    # 3. Muskingum de jusante ate o ponto de controle de Valinhos:
    # Semelhante ao passo 1., porem com uma trinca de variaveis Muskingum (K, X, m) ao inves de duas

    # Condicoes de contorno para variaveis que serao calibradas
    bounds = [
        [100.0, 2000.0],                # Str
        [  0.2,   10.0],                # k2t
        [  0.0,   20.0],                # Crec
        [  0.0,    1.0],                # TUin
        [  0.0, obsValinhos.Q[0]],      # EBin
        [ 84.0,  168.0],                # K (entre 3.5 e 7 dias)
        [  0.0,    0.5],                # X
        [  1.1,    3.0]                 # m (forcando o modelo a nao escolher m = 1)
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

        # Metrica utilizada para otimizacao
        match FO:
            case 1:
                # NSE: Nash-Sutcliffe
                a = 0
                b = 0
                Qm = np.mean(inc1)
                for i in range(n):
                    a += (inc1[i] - inc2[i]) ** 2
                    b += (inc1[i] - Qm) ** 2

                return a / b

            case 2:
                # SSQ: Sum of Squares of Deviation
                a = 0
                for i in range(n):
                    a += ((inc2[i] - inc1[i]) / inc2[i]) ** 2

                return a

            case 3:
                # (I)RMSE: (Inverse) Root-Mean-Square Error
                a = 0
                for i in range(n):
                    a += ((1 / inc1[i]) - (1 / inc2[i])) ** 2

                return np.sqrt(a / n)

    # Busca por evolucao diferencial
    result = differential_evolution(objective, bounds, maxiter=1000)
    # Resultados
    print()
    print('Valinhos:')
    print('Status : %s' % result['message'])
    print('Avaliacoes realizadas: %d' % result['nfev'])
    # Solucao
    solution    = result['x']
    evaluation  = objective(solution)
    print('Solucao: \n'
          'f = ( \n'
          '\t[Str = %.3f \n\t k2t = %.3f \n\t Crec = %.3f \n\t TUin = %.3f \n\t EBin = %.3f \n\t K = %.3f \n\t X = %.3f \n\t m = %.3f]'
          % (
              solution[0], solution[1], solution[2], solution[3], solution[4], solution[5], solution[6], solution[7]))
    if FO == 1:
        print(') = %.3f\n' % (1 - evaluation))
        objValinhos = 1 - evaluation
    else:
        print(') = %.3f\n' % evaluation)
        objValinhos = evaluation
    
    # 4. Checagem de incrementais e conversao chuva-vazao para o periodo continuo de 60 + 10 dias em Valinhos:
    # As incrementais sao necessarias para averiguar como as vazoes obtidas com os parametros calibrados
    # adequam-se aos dados "observados" (tambem advindos de uma calibracao propria, devido a parcela de despacho)
    newQ = DownstreamFORK(solution[5], solution[6], solution[7], 24.0, obsAtibaia.Q)

    incValinhos = [0] * n
    for j in range(n):
        incValinhos[j] = obsValinhos.Q[j] - newQ[j] + obsValinhos.C[j]

    calcValinhos = SMAP(solution[0], solution[1], solution[2], solution[3], solution[4], prevArtValinhos, Valinhos)
    
    # 5. Geracao de graficos
    if flag == 'comGraficos':
        obj = [[0] * 2 for _ in range(1)]
        obj[0][0] = objAtibaia
        obj[0][1] = objValinhos

        ChuvaVazao(
            obsAtibaia    , obsValinhos    ,
            incAtibaia    , incValinhos    ,
            prevArtAtibaia, prevArtValinhos,
            calcAtibaia   , calcValinhos   ,
            obj           , step           ,
            FO
        )
    
    # 6. Muskingum de montante ate o ponto de controle de Atibaia:
    # Depois de otimizar o modulo chuva-vazao para cada sub-bacia, e necessario tomar as
    # vazoes incrementais aferidas durante o periodo de observacao para calibrar o modulo de routing
    # reverso, ou upstream routing (de jusante para montante). Em Valinhos:
    #   Qobs.Vali. = Qinc. - capt. + Desp.Atib.
    # Portanto, convem retroceder Desp.Atib. e tomar como referencia Qobs.Atib. para calibracao
    desp = [0] * n
    for j in range(n):
        desp[j] = obsValinhos.Q[j] + obsValinhos.C[j] - incValinhos[j]

    # Condicoes de contorno para variaveis que serao calibradas
    bounds = [
        [84.0, 168.0],                  # K (entre 3.5 e 7 dias)
        [ 0.2,   0.5],                  # X (necessario controlar limite inferior de X para que o modelo nao execute potenciacao complexa)
        [ 1.1,   3.0]                   # m (forcando o modelo a nao escolher m = 1)
    ]

    # Funcao objetivo
    def objective(p):
        # Sujeitos a calibracao
        K, X, m = p

        # Routing de montante nao linear: de Valinhos para Atibaia
        Q = UpstreamFORK(K, X, m, 24.0, desp)

        # Metrica utilizada para otimizacao
        match FO:
            case 1:
                # NSE: Nash-Sutcliffe
                a = 0
                b = 0
                Qm = np.mean(obsAtibaia.Q)
                for i in range(n):
                    a += (obsAtibaia.Q[i] - Q[i]) ** 2
                    b += (obsAtibaia.Q[i] - Qm) ** 2

                return a / b

            case 2:
                # SSQ: Sum of Squares of Deviation
                a = 0
                for i in range(n):
                    a += ((obsAtibaia.Q[i] - Q[i]) / obsAtibaia.Q[i]) ** 2

                return a

            case 3:
                # (I)RMSE: (Inverse) Root-Mean-Square Error
                a = 0
                for i in range(n):
                    a += ((1 / Q[i]) - (1 / obsAtibaia.Q[i])) ** 2

                return np.sqrt(a / n)

    # Busca por evolucao diferencial
    result = differential_evolution(objective, bounds, maxiter=1000)
    # Resultados
    print('Muskingum de montante')
    print('Valinhos:')
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
    upVA = UpstreamFORK(solution[0], solution[1], solution[2], 24.0, desp)
    # Dicionario para armazenar valores calculados
    # (a serem utilizadas durante a etapa de previsao, vide ?)
    Upstream = {
        'K': [solution[0]],
        'X': [solution[1]],
        'm': [solution[2]]
    }

    # 7. Muskingum de montante ate reservatorios:
    # Depois de otimizar o modulo chuva-vazao para cada sub-bacia, e necessario tomar as
    # vazoes incrementais aferidas durante o periodo de observacao para calibrar o modulo de routing
    # reverso, ou upstream routing (de jusante para montante). Em Atibaia:
    #   Qobs.Atib. = Qinc. - capt. + (Desp.Atibain. + Desp.Cach.)
    #   (Desp.Atibain. + Desp.Cach.) = Res.
    # Como a descarga observada junto a secao corresponde a soma de duas parcelas, cada qual de uma barragem,
    # e preciso retroceder um percentual de Res. para comparar com Desp.Atibain.obs. O mesmo vale para
    # Res. e Desp.Cach.obs. Uma forma e realizar o routing de Res. hora multiplicado por um coeficiente
    # alfa (p/ Atibainha), hora multiplicado por beta (p/ Cachoeira). Assim, alem de K, X e m, uma nova
    # variavel deve ser calibrada em cada otimizacao, de modo que alfa + beta seja igual a 1
    res = [0] * n
    for j in range(n):
        res[j] = obsAtibaia.Q[j] + obsAtibaia.C[j] - incAtibaia[j]

    # Condicoes de contorno para variaveis que serao calibradas
    match FO:
        case 1 | 2:
            bounds = [
                [120.0, 180.0],                 # K    (entre 5 e 7.5 dias)
                [  0.3,   0.5],                 # X    (necessario controlar limite inferior para que o modelo nao execute potenciacao complexa)
                [  1.1,   3.0],                 # m    (forcando o modelo a nao escolher m = 1)
                [  0.5,   1.0]                  # alfa (necessario controlar limite inferior para que o modelo nao execute potenciacao complexa)
            ]
        case 3:
            bounds = [
                [120.0, 180.0],                 # K    (entre 5 e 7.5 dias)
                [  0.4,   0.5],                 # X    (necessario controlar limite inferior para que o modelo nao execute potenciacao complexa)
                [  1.1,   3.0],                 # m    (forcando o modelo a nao escolher m = 1)
                [  0.6,   1.0]                  # alfa (necessario controlar limite inferior para que o modelo nao execute potenciacao complexa)
            ]

    # Funcao objetivo
    def objective(p):
        # Sujeitos a calibracao
        K, X, m, alfa = p

        # Routing de montante nao linear: de Atibaia para Atibainha
        Q = UpstreamFORK(K, X, m, 24.0, list(np.multiply(res, alfa)))

        # Metrica utilizada para otimizacao
        match FO:
            case 1:
                # NSE: Nash-Sutcliffe
                a = 0
                b = 0
                Qm = np.mean(revAtibainha.D)
                for i in range(n):
                    a += (revAtibainha.D[i] - Q[i]) ** 2
                    b += (revAtibainha.D[i] - Qm) ** 2

                return a / b

            case 2:
                # SSQ: Sum of Squares of Deviation
                a = 0
                for i in range(n):
                    a += ((revAtibainha.D[i] - Q[i]) / revAtibainha.D[i]) ** 2

                return a

            case 3:
                # (I)RMSE: (Inverse) Root-Mean-Square Error
                a = 0
                for i in range(n):
                    a += ((1 / Q[i]) - (1 / revAtibainha.D[i])) ** 2

                return np.sqrt(a / n)

    # Busca por evolucao diferencial
    result = differential_evolution(objective, bounds, maxiter=100)
    # Resultados
    print('Muskingum de montante')
    print('Atibaia para Atibainha:')
    print('Status : %s' % result['message'])
    print('Avaliacoes realizadas: %d' % result['nfev'])
    # Solucao
    solution   = result['x']
    alfa       = solution[3]
    evaluation = objective(solution)
    print('Solucao: \n'
          'f = ( \n'
          '\t[K = %.3f \n\t X = %.3f \n\t m = %.3f \n\t alfa = %.3f]'
          % (solution[0], solution[1], solution[2], solution[3]))
    if FO == 1:
        print(') = %.3f\n' % (1 - evaluation))
    else:
        print(') = %.3f\n' % evaluation)

    # Armazenamento para plotagem
    upAA = UpstreamFORK(solution[0], solution[1], solution[2], 24.0, list(np.multiply(res, alfa)))
    # Dicionario para armazenar valores calculados
    # (a serem utilizadas durante a etapa de previsao, vide ?)
    Upstream['K'] += [solution[0]]
    Upstream['X'] += [solution[1]]
    Upstream['m'] += [solution[2]]

    # Mesmo procedimento, porem para Cachoeira e com beta
    beta = 1 - alfa

    # Condicoes de contorno para variaveis que serao calibradas
    match FO:
        case 1 | 2:
            bounds = [
                [120.0, 180.0],                  # K (entre 5 e 7.5 dias)
                [  0.4,   0.5],                  # X (necessario controlar limite inferior para que o modelo nao execute potenciacao complexa)
                [  1.1,   3.0]                   # m (forcando o modelo a nao escolher m = 1)
            ]
        case 3:
            bounds = [
                [180.0, 240.0],                  # K (entre 7.5 e 10 dias)
                [  0.4,   0.5],                  # X (necessario controlar limite inferior para que o modelo nao execute potenciacao complexa)
                [  1.1,   3.0]                   # m (forcando o modelo a nao escolher m = 1)
            ]

    # Funcao objetivo
    def objective(p):
        # Sujeitos a calibracao
        K, X, m = p

        # Routing de montante nao linear: de Atibaia para Cachoeira
        Q = UpstreamFORK(K, X, m, 24.0, list(np.multiply(res, beta)))

        # Metrica utilizada para otimizacao
        match FO:
            case 1:
                # NSE: Nash-Sutcliffe
                a = 0
                b = 0
                Qm = np.mean(revCachoeira.D)
                for i in range(n):
                    a += (revCachoeira.D[i] - Q[i]) ** 2
                    b += (revCachoeira.D[i] - Qm) ** 2

                return a / b

            case 2:
                # SSQ: Sum of Squares of Deviation
                a = 0
                for i in range(n):
                    a += ((revCachoeira.D[i] - Q[i]) / revCachoeira.D[i]) ** 2

                return a

            case 3:
                # (I)RMSE: (Inverse) Root-Mean-Square Error
                a = 0
                for i in range(n):
                    a += ((1 / Q[i]) - (1 / revCachoeira.D[i])) ** 2

                return np.sqrt(a / n)

    # Busca por evolucao diferencial
    result = differential_evolution(objective, bounds, maxiter=100)
    # Resultados
    print('Muskingum de montante')
    print('Atibaia para Cachoeira:')
    print('Status : %s' % result['message'])
    print('Avaliacoes realizadas: %d' % result['nfev'])
    # Solucao
    solution = result['x']
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
    upAC = UpstreamFORK(solution[0], solution[1], solution[2], 24.0, list(np.multiply(res, beta)))
    # Dicionario para armazenar valores calculados
    # (a serem utilizadas durante a etapa de previsao, vide ?)
    Upstream['K'] += [solution[0]]
    Upstream['X'] += [solution[1]]
    Upstream['m'] += [solution[2]]

    # 8. Geracao de graficos
    if flag == 'comGraficos':
        Routings(
            obsAtibaia, revAtibainha, revCachoeira,
            upVA, upAA, upAC,
            step
        )

    # 9. Tomada de decisao:
    # A serie de 60 dias de observacao + 10 dias de previsao em Valinhos sera transladada duas vezes,
    # uma ate o reservatorio de Atibainha com os parametros calibrados por trecho (Valinhos - Atibaia e
    # Atibaia - Atibainha) e outra ate o reservatorio de Cachoeira, de modo semelhante (Valinhos - Atibaia e
    # Atibaia - Cachoeira). Ao chegar em cada barragem, os hidrogramas finais devem ser confrontados com a minima
    # media diaria de Valinhos (10 m3/s) somada a media de captacao em seu periodo de observacao. Caso a ordenada em
    # index = 60 (dia de decisao) seja inferior as demandas, o despacho necessario sera o deficit remanescente;
    # caso contrario, despacha-se o minimo de 0.25 m3/s. Para Atibaia, o procedimento e o mesmo. Sua serie de 60 + 10
    # sera retrocedida duas vezes, uma para cada barragem, e os hidrogramas finais serao comparados com a minima
    # media diaria de 2 m3/s + media de captacao durante os primeiros 60 dias observados. Caso a ordenada em
    # index = 60 (dia de decisao) seja inferior as demandas, o despacho necessario sera o deficit remanescente;
    # caso contrario, despacha-se o minimo outorgado

    # Routings ate barragens:
    decisV = UpstreamFORK(
        Upstream['K'][0],
        Upstream['X'][0],
        Upstream['m'][0],
        24.0, calcValinhos
    )
    # de Valinhos (pt. 1)
    decisVA = UpstreamFORK(
        Upstream['K'][1],
        Upstream['X'][1],
        Upstream['m'][1],
        24.0, list(np.multiply(decisV, alfa))
    )
    # de Valinhos (pt. 2)
    decisVC = UpstreamFORK(
        Upstream['K'][2],
        Upstream['X'][2],
        Upstream['m'][2],
        24.0, list(np.multiply(decisV, beta))
    )
    # de Atibaia (pt. 1)
    decisAA = UpstreamFORK(
        Upstream['K'][1],
        Upstream['X'][1],
        Upstream['m'][1],
        24.0, list(np.multiply(calcAtibaia, alfa))
    )
    # de Atibaia (pt. 2)
    decisAC = UpstreamFORK(
        Upstream['K'][2],
        Upstream['X'][2],
        Upstream['m'][2],
        24.0, list(np.multiply(calcAtibaia, beta))
    )

    # Em Atibainha
    if decisVA[60] < 10 + np.mean(obsValinhos.C):
        defic1 = 10 + np.mean(obsValinhos.C) - decisVA[60]
    else:
        defic1 = 0.25
    if decisAA[60] <  2 + np.mean(obsAtibaia.C):
        defic2 =  2 + np.mean(obsAtibaia.C)  - decisAA[60]
    else:
        defic2 = 0.25
    despAtibainha = max(defic1, defic2)

    # Em Cachoeira
    if decisVC[60] < 10 + np.mean(obsValinhos.C):
        defic1 = 10 + np.mean(obsValinhos.C) - decisVC[60]
    else:
        defic1 = 0.25
    if decisAC[60] <  2 + np.mean(obsAtibaia.C):
        defic2 =  2 + np.mean(obsAtibaia.C)  - decisAC[60]
    else:
        defic2 = 0.25
    despCachoeira = max(defic1, defic2)

    resultado = Decisao(
        Atibainha = despAtibainha,
        Cachoeira = despCachoeira
    )

    # 10. Geracao de graficos
    if flag == 'comGraficos':
        Despachos(obsValinhos, 10, obsAtibaia, 2, decisVA, decisAA, resultado.Atibainha, step)
