from Dados.Classes import *
from Metodos.Muskingum.Downstream import *
from Metodos.Muskingum.Upstream   import *
from Metodos.SMAP        import *
from Metodos.Otimizacoes import *
from scipy.optimize      import differential_evolution
import numpy as np

def Previsao(
        obsAtibaia   , obsValinhos   ,     # Chuvas observadas nos pontos (p/ calibrar TUin e EBin)
        prevAtibaia  , prevValinhos  ,     # Previsões de 7 dias em cada bacia incremental
        paramsAtibaia, paramsValinhos,     # Parâmetros calibrados com 4 meses de observação
        revAtibainha , revCachoeira  ,     # Despachos observados nos reservatórios (p/ calibrar TUin e EBin)
        startAtibaia , startValinhos ,     # Dicionários para armazenamento de parâmetros após calibração
        Atibaia      , Valinhos      ,     # Bacias (dados p/ SMAP)
        FO           , step                # Função objetivo p/ otimizações e variável de controle de iterações
):
    # 1. Translado de vazões observadas em Atibaia para calibrar TUin e EBin
    # e invocar o modelo SMAP para previsão em Valinhos
    bounds = [
        [0.0,  1.0],            # TUin
        [0.0, 40.0]             # EBin
    ]

    n = len(obsAtibaia.Q)

    # Routing de jusante não linear de Atibainha para Atibaia (#1) e de Cachoeira para Atibaia (#2)
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
    # Routing de jusante não linear de Atibaia para Valinhos
    Q = DownstreamFORK(
        paramsValinhos['K'][0],
        paramsValinhos['X'][0],
        paramsValinhos['m'][0],
        24.0, obsAtibaia.Q)

    # Junto ao ponto de controle, a vazão observada equivale a uma parcela
    # despachada de cada reservatório mais uma parcela incremental de eventos chuvosos
    # menos uma parcela captada entre as barragens e a própria seção
    inc1 = [0] * n
    for j in range(n):
        inc1[j] = obsValinhos.Q[j] - Q[j] + obsValinhos.C[j]

    # Função objetivo
    def objective(p):
        # Sujeitos a calibração
        TUin, EBin = p

        # Segundo vetor incremental ("calc")
        inc2 = SMAP(
            paramsValinhos['Str']  ,
            paramsValinhos['k2t']  ,
            paramsValinhos['Crec'] ,
            TUin, EBin, obsValinhos, Valinhos)

        # Restrição positiva aos routings calculados e às vazões incrementais
        minQ = min(inc2)
        if minQ < 0:
            return np.inf
        else:
            # Métrica utilizada para otimização
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

    # Busca por evolução diferencial
    result = differential_evolution(objective, bounds, maxiter = 1000)
    # Resultados
    print()
    print('Step: %d' % step)
    print('SMAP em Valinhos:')
    print('Status: %s' % result['message'])
    print('Avaliações realizadas: %d' % result['nfev'])
    # Solução
    solution   = result['x']
    evaluation = objective(solution)
    print('Solução: \n'
          'f = ( \n'
          '\t[TUin = %.3f \n\t EBin = %.3f]'
          % (solution[0], solution[1]))
    if FO == 1:
        print(') = %.3f' % (1 - evaluation))
    else:
        print(') = %.3f' % evaluation)

    startValinhos['TUin'] += [solution[0]]
    startValinhos['EBin'] += [solution[1]]

    previsao1   = Ponto(C = [], P = [], Q = [], t = [])
    previsao1.P = obsValinhos.P + prevValinhos.P
    # 2. Vetor de vazões contínuas (observado 30 dias + previsto 7 dias)
    calcValinhos = SMAP(
            paramsValinhos['Str']  ,
            paramsValinhos['k2t']  ,
            paramsValinhos['Crec'] ,
            solution[0], solution[1], previsao1, Valinhos)

    # 3. Translado de despachos observadas em Atibainha e Cachoeira para calibrar TUin e EBin
    # e invocar o modelo SMAP para previsão em Atibaia
    bounds = [
        [0.0, 1.0],            # TUin
        [0.0, 9.2]             # EBin
    ]
    # Q1 e Q2 já calculados
    # Junto ao ponto de controle, a vazão observada equivale a uma parcela
    # despachada de cada reservatório mais uma parcela incremental de eventos chuvosos
    # menos uma parcela captada entre as barragens e a própria seção
    inc1 = [0] * n
    for j in range(n):
        inc1[j] = obsAtibaia.Q[j] - (Q1[j] + Q2[j]) + obsAtibaia.C[j]

    # Função objetivo
    def objective(p):
        # Sujeitos a calibração
        TUin, EBin = p

        # Segundo vetor incremental ("calc")
        inc2 = SMAP(
            paramsAtibaia['Str']  ,
            paramsAtibaia['k2t']  ,
            paramsAtibaia['Crec'] ,
            TUin, EBin, obsAtibaia, Atibaia)

        # Restrição positiva aos routings calculados e às vazões incrementais
        minQ = min(inc2)
        if minQ < 0:
            return np.inf
        else:
            # Métrica utilizada para otimização
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

    # Busca por evolução diferencial
    result = differential_evolution(objective, bounds, maxiter=1000)
    # Resultados
    print()
    print('SMAP em Atibaia:')
    print('Status: %s' % result['message'])
    print('Avaliações realizadas: %d' % result['nfev'])
    # Solução
    solution   = result['x']
    evaluation = objective(solution)
    print('Solução: \n'
          'f = ( \n'
          '\t[TUin = %.3f \n\t EBin = %.3f]'
          % (solution[0], solution[1]))
    if FO == 1:
        print(') = %.3f' % (1 - evaluation))
    else:
        print(') = %.3f' % evaluation)

    startAtibaia['TUin'] += [solution[0]]
    startAtibaia['EBin'] += [solution[1]]

    previsao2   = Ponto(C = [], P = [], Q = [], t = [])
    previsao2.P = obsAtibaia.P + prevAtibaia.P
    # 4. Vetor de vazões contínuas (observado 30 dias + previsto 7 dias)
    calcAtibaia = SMAP(
        paramsAtibaia['Str'] ,
        paramsAtibaia['k2t'] ,
        paramsAtibaia['Crec'],
        solution[0], solution[1], previsao2, Atibaia)

    # 5. Tomada de decisão:
    # A série de 30 dias de observação + 7 dias de previsão em Valinhos será transladada duas vezes,
    # uma até o reservatório de Atibainha com os parâmetros calibrados por trecho (Valinhos - Atibaia e
    # Atibaia - Atibainha) e outra até o reservatório de Cachoeira, de modo semelhante (Valinhos - Atibaia e
    # Atibaia - Cachoeira). Ao chegar em cada barragem, os hidrogramas finais devem ser confrontados com a mínima
    # média diária de Valinhos (10 m3/s) somada à média de captação em seu período de observação. Caso a ordenada em
    # index = 30 (dia de decisão) seja inferior às demandas, o despacho necessário será o déficit remanescente;
    # caso contrário, despacha-se o mínimo de 0.25 m3/s. Para Atibaia, o procedimento é o mesmo. Sua série de 30 + 7
    # será retrocedida duas vezes, uma para cada barragem, e os hidrogramas finais serão comparados com a mínima
    # média diária de 2 m3/s + média de captação durante os primeiros 30 dias observados. Caso a ordenada em
    # index = 30 (dia de decisão) seja inferior às demandas, o despacho necessário será o déficit remanescente;
    # caso contrário, despacha-se o mínimo outorgado

    # Routings até barragens:
    decisV = UpstreamFORK(
        paramsValinhos['K'][1],
        paramsValinhos['X'][1],
        paramsValinhos['m'][1],
        24.0, calcValinhos
    )
    # Valinhos recebe a contribuição de sua bacia mais a de Atibaia
    decisV = np.add(decisV, calcAtibaia)
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

    demanda1 = 0.5 * (10 + np.mean(obsValinhos.C))
    demanda2 = 0.5 * ( 2 + np.mean(obsAtibaia.C ))
    # Em Atibainha
    if decisVA[30] < demanda1:
        defic1 = demanda1 - decisVA[31]
    else:
        defic1 = 0.25
    if decisAA[30] <  demanda2:
        defic2 =  demanda2  - decisAA[31]
    else:
        defic2 = 0.25
    despAtibainha = max(defic1, defic2)

    # Em Cachoeira
    if decisVC[30] < demanda1:
        defic1 = demanda1 - decisVC[31]
    else:
        defic1 = 0.25
    if decisAC[30] <  demanda2:
        defic2 =  demanda2  - decisAC[31]
    else:
        defic2 = 0.25
    despCachoeira = max(defic1, defic2)

    resultado = Decisao(
        Atibainha = despAtibainha,
        Cachoeira = despCachoeira
    )

    # Depois de definir a decisão ao final de uma iteração, deve-se atualizar os vetores de
    # despacho de cada reservatório para que o passo seguinte 'lembre-se' de seu antecessor.
    # Descarta primeiro dia
    revAtibainha.D.pop(0)
    revCachoeira.D.pop(0)
    # Adiciona última decisão
    revAtibainha.D.append(despAtibainha)
    revCachoeira.D.append(despCachoeira)

    # Vazões observadas após decisão atual
    # Em Atibaia
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
    # Série recortada de previsão
    previsao2.P = previsao2.P[1:31]
    termoCV = SMAP(
        paramsAtibaia['Str'],
        paramsAtibaia['k2t'],
        paramsAtibaia['Crec'],
        startAtibaia['TUin'][step - 1], startAtibaia['EBin'][step - 1], previsao2, Atibaia)
    for i in range(0, n - 1, 1):
        obsAtibaia.Q[i] = Q1[i] + Q2[i] + termoCV[i] - obsAtibaia.C[i]
    obsAtibaia.Q[n - 1] = Q1[n - 1] + Q2[n - 1] + termoCV[n - 1] - np.mean(obsAtibaia.C)

    # Em Valinhos
    Q = DownstreamFORK(
        paramsValinhos['K'][0],
        paramsValinhos['X'][0],
        paramsValinhos['m'][0],
        24.0, obsAtibaia.Q)
    # Série recortada de previsão
    previsao1.P = previsao1.P[1:31]
    termoCV = SMAP(
        paramsValinhos['Str'],
        paramsValinhos['k2t'],
        paramsValinhos['Crec'],
        startValinhos['TUin'][step - 1], startValinhos['EBin'][step - 1], previsao1, Valinhos)
    for i in range(0, n - 1, 1):
        obsValinhos.Q[i] = Q[i] + termoCV[i] - obsValinhos.C[i]
    obsValinhos.Q[n - 1] = Q[n - 1] + termoCV[n - 1] - np.mean(obsValinhos.C)

    return obsAtibaia.Q[29], obsValinhos.Q[29], resultado
