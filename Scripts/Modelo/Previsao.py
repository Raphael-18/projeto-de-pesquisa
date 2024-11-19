import numpy as np
import pandas as pd
from scipy.optimize import differential_evolution

from Dados.Classes import Ponto, Decisao
from Metodos.SMAP import SMAP
from Metodos.Muskingum.Downstream import DownstreamFORK
from Metodos.Muskingum.Upstream import UpstreamFORK
from Metodos.Otimizacoes import NSE, RMSE, SSQ, KGE


def Previsao(
        # Chuvas observadas nos pontos (p/ calibrar TUin e EBin)
        obsAtibaia, obsValinhos,
        prevAtibaia, prevValinhos,  # Previsões de 7 dias em cada bacia incremental
        paramsAtibaia, paramsValinhos,  # Parâmetros calibrados com 2 anos de observação
        # Despachos observados nos reservatórios (p/ calibrar TUin e EBin)
        revAtibainha, revCachoeira,
        # Dicionários para armazenamento de parâmetros após calibração
        startAtibaia, startValinhos,
        Atibaia, Valinhos,  # Bacias (dados p/ SMAP)
        FO, step  # Função objetivo p/ otimizações e variável de controle de iterações
):
    # 1. Translado de vazões observadas em Atibaia para calibrar TUin e EBin
    # e invocar o modelo SMAP para previsão em Valinhos
    bounds = [
        [0.0,  1.0],  # TUin
        [0.1, 40.0]  # EBin
    ]

    n = len(obsAtibaia.Q)

    # Routing de jusante não linear de Atibaia para Valinhos
    Q = DownstreamFORK(
        Valinhos.K[0],
        Valinhos.X[0],
        Valinhos.m[0],
        24.0, obsAtibaia.Q)

    # Junto ao ponto de controle, a vazão observada equivale a uma parcela
    # despachada de cada reservatório mais uma parcela incremental de eventos chuvosos
    # menos uma parcela captada entre as barragens e a própria seção.
    inc1 = pd.DataFrame([0] * n)
    Q = pd.DataFrame(Q)
    inc1 = obsValinhos.Q - Q + obsValinhos.C

    # O objeto obsValinhos é passado ao modelo com 37 dados observados (para que seja possível
    # calcular a nova vazão observada ao final de cada previsão). Para calibrar o módulo SMAP com
    # TUin e EBin é preciso copiar o objeto obsValinhos em uma nova instância e recortar o vetor
    # de precipitações.
    instValinhos = Ponto(C=[], E=[], P=[], Q=[], t=[])
    instValinhos.E = obsValinhos.E[0:30]
    instValinhos.P = obsValinhos.P[0:30]

    # Função objetivo
    def objective(p):
        # Sujeitos a calibração
        TUin, EBin = p

        # Segundo vetor incremental ("calc")
        inc2 = SMAP(
            paramsValinhos['Str'],
            paramsValinhos['k2t'],
            paramsValinhos['Crec'],
            TUin, EBin, instValinhos, Valinhos)

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
                case 4:
                    # KGE: Kling-Gupta
                    return KGE(inc1, inc2)

    # Busca por evolução diferencial
    result = differential_evolution(objective, bounds, maxiter=10)
    # Resultados
    # print()
    # print('Step: %d' % step)
    # print('SMAP em Valinhos:')
    # print('Status: %s' % result['message'])
    # print('Avaliações realizadas: %d' % result['nfev'])
    # Solução
    solution = result['x']
    # evaluation = objective(solution)
    # print('Solução: \n'
    #      'f = ( \n'
    #      '\t[TUin = %.3f \n\t EBin = %.3f]'
    #      % (solution[0], solution[1]))
    # if FO == 1 or FO == 4:
    #    print(') = %.3f' % (1 - evaluation))
    # else:
    #    print(') = %.3f' % evaluation)

    startValinhos['TUin'] += [solution[0]]
    startValinhos['EBin'] += [solution[1]]

    previsao1 = Ponto(C=[], E=[], P=[], Q=[], t=[])
    previsao1.E = obsValinhos.E
    previsao1.P = obsValinhos.P[0:30] + prevValinhos.P
    # 2. Vetor de vazões contínuas (observado 30 dias + previsto 7 dias)
    calcValinhos = SMAP(
        paramsValinhos['Str'],
        paramsValinhos['k2t'],
        paramsValinhos['Crec'],
        solution[0], solution[1], previsao1, Valinhos)

    # 3. Translado de despachos observadas em Atibainha e Cachoeira para calibrar TUin e EBin
    # e invocar o modelo SMAP para previsão em Atibaia
    bounds = [
        [0.0, 1.0],             # TUin
        [0.1, 9.2]              # EBin
    ]

    # Routing de jusante não linear de Atibainha para Atibaia (#1) e de Cachoeira para Atibaia (#2)
    Q1 = DownstreamFORK(
        Atibaia.K[0][0],
        Atibaia.X[0][0],
        Atibaia.m[0][0],
        24.0, revAtibainha.D)
    Q2 = DownstreamFORK(
        Atibaia.K[1][0],
        Atibaia.X[1][0],
        Atibaia.m[1][0],
        24.0, revCachoeira.D)

    # Junto ao ponto de controle, a vazão observada equivale a uma parcela
    # despachada de cada reservatório mais uma parcela incremental de eventos chuvosos
    # menos uma parcela captada entre as barragens e a própria seção.
    inc1 = pd.DataFrame([0] * n)
    Q1 = pd.DataFrame(Q1)
    Q2 = pd.DataFrame(Q2)
    inc1 = obsAtibaia.Q - (Q1 + Q2) + obsAtibaia.C

    # O objeto obsAtibaia é passado ao modelo com 37 dados observados (para que seja possível
    # calcular a nova vazão observada ao final da previsão). Para calibrar o módulo SMAP com
    # TUin e EBin é preciso copiar o objeto obsAtibaia em uma nova instância e recortar o vetor
    # de precipitações.
    instAtibaia = Ponto(C=[], E=[], P=[], Q=[], t=[])
    instAtibaia.E = obsAtibaia.E[0:30]
    instAtibaia.P = obsAtibaia.P[0:30]

    # Função objetivo
    def objective(p):
        # Sujeitos a calibração
        TUin, EBin = p

        # Segundo vetor incremental ("calc")
        inc2 = SMAP(
            paramsAtibaia['Str'],
            paramsAtibaia['k2t'],
            paramsAtibaia['Crec'],
            TUin, EBin, instAtibaia, Atibaia)

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
                case 4:
                    # KGE: Kling-Gupta
                    return KGE(inc1, inc2)

    # Busca por evolução diferencial
    result = differential_evolution(objective, bounds, maxiter=10)
    # Resultados
    # print()
    # print('SMAP em Atibaia:')
    # print('Status: %s' % result['message'])
    # print('Avaliações realizadas: %d' % result['nfev'])
    # Solução
    solution = result['x']
    # evaluation = objective(solution)
    # print('Solução: \n'
    #      'f = ( \n'
    #      '\t[TUin = %.3f \n\t EBin = %.3f]'
    #      % (solution[0], solution[1]))
    # if FO == 1 or FO == 4:
    #    print(') = %.3f' % (1 - evaluation))
    # else:
    #    print(') = %.3f' % evaluation)

    startAtibaia['TUin'] += [solution[0]]
    startAtibaia['EBin'] += [solution[1]]

    previsao2 = Ponto(C=[], E=[], P=[], Q=[], t=[])
    previsao2.E = obsAtibaia.E
    previsao2.P = obsAtibaia.P[0:30] + prevAtibaia.P
    # 4. Vetor de vazões contínuas (observado 30 dias + previsto 7 dias)
    calcAtibaia = SMAP(
        paramsAtibaia['Str'],
        paramsAtibaia['k2t'],
        paramsAtibaia['Crec'],
        solution[0], solution[1], previsao2, Atibaia)

    # 5. Tomada de decisão:
    # A série de 30 dias de observação + 7 dias de previsão em Valinhos será transladada duas vezes,
    # uma até o reservatório de Atibainha com os parâmetros calibrados por trecho (Valinhos - Atibaia e
    # Atibaia - Atibainha) e outra até o reservatório de Cachoeira, de modo semelhante (Valinhos - Atibaia e
    # Atibaia - Cachoeira). Ao chegar em cada barragem, os hidrogramas finais devem ser confrontados com a mínima
    # média diária de Valinhos (10 m3/s) somada à média de captação em seu período de observação.
    # Caso a ordenada em index = 30 (dia de decisão) seja inferior às demandas, o despacho necessário será
    # o déficit remanescente; caso contrário, despacha-se o mínimo de 0.25 m3/s. Para Atibaia, o procedimento é o mesmo.
    # Sua série de 30 + 7 será retrocedida duas vezes, uma para cada barragem, e os hidrogramas finais serão
    # comparados com a mínima média diária de 2 m3/s + média de captação durante os primeiros 30 dias observados.
    # Caso a ordenada em index = 30 (dia de decisão) seja inferior às demandas, o despacho necessário será o déficit
    # remanescente; caso contrário, despacha-se o mínimo outorgado.

    # Routings até barragens:
    decisV = UpstreamFORK(
        Valinhos.K[1],
        Valinhos.X[1],
        Valinhos.m[1],
        24.0, calcValinhos
    )
    # Valinhos recebe a contribuição de sua bacia mais a de Atibaia
    decisV = np.add(decisV, calcAtibaia)
    # de Valinhos (pt. 1)
    decisVA = UpstreamFORK(
        Atibaia.K[0][1],
        Atibaia.X[0][1],
        Atibaia.m[0][1],
        24.0, list(np.multiply(decisV, 0.5))
    )
    # de Valinhos (pt. 2)
    decisVC = UpstreamFORK(
        Atibaia.K[1][1],
        Atibaia.X[1][1],
        Atibaia.m[1][1],
        24.0, list(np.multiply(decisV, 0.5))
    )
    # de Atibaia (pt. 1)
    decisAA = UpstreamFORK(
        Atibaia.K[0][1],
        Atibaia.X[0][1],
        Atibaia.m[0][1],
        24.0, list(np.multiply(calcAtibaia, 0.5))
    )
    # de Atibaia (pt. 2)
    decisAC = UpstreamFORK(
        Atibaia.K[1][1],
        Atibaia.X[1][1],
        Atibaia.m[1][1],
        24.0, list(np.multiply(calcAtibaia, 0.5))
    )

    # Necessário recortar as precipitações para andar um dia ao verificar a vazão observada esperada
    obsAtibaia.C = obsAtibaia.C[1:31]
    obsAtibaia.E = obsAtibaia.E[1:31]
    obsAtibaia.P = obsAtibaia.P[1:31]
    obsValinhos.C = obsValinhos.C[1:31]
    obsValinhos.E = obsValinhos.E[1:31]
    obsValinhos.P = obsValinhos.P[1:31]

    # Regra da média móvel de 15 dias
    mediaA = 0.5 * (((3 - np.mean(obsAtibaia.C)) * 15) -
                    np.sum(obsAtibaia.Q[16:30]))
    mediaV = 0.5 * (((12 - np.mean(obsAtibaia.C) -
                    np.mean(obsValinhos.C)) * 15) - np.sum(obsValinhos.Q[16:30]))

    # Em Atibainha
    if decisVA[30] < mediaV:
        defic1 = mediaV - decisVA[30]
    else:
        defic1 = 0.25
    if decisAA[30] < mediaA:
        defic2 = mediaA - decisAA[30]
    else:
        defic2 = 0.25
    despAtibainha = max(defic1, defic2)

    # Em Cachoeira
    if decisVC[30] < mediaV:
        defic1 = mediaV - decisVC[30]
    else:
        defic1 = 0.25
    if decisAC[30] < mediaA:
        defic2 = mediaA - decisAC[30]
    else:
        defic2 = 0.25
    despCachoeira = max(defic1, defic2)

    resultado = Decisao(
        Atibainha=despAtibainha,
        Cachoeira=despCachoeira
    )

    # Depois de definir a decisão ao final de uma iteração, deve-se atualizar os vetores de
    # despacho de cada reservatório para que o passo seguinte 'lembre-se' de seu antecessor.
    # Descarta primeiro dia
    revAtibainha.D.pop(0)
    revCachoeira.D.pop(0)
    # Adiciona últimas decisões
    revAtibainha.D.append(despAtibainha)
    revCachoeira.D.append(despCachoeira)

    # Vazões observadas após decisão atual
    # Em Atibaia
    Q1 = DownstreamFORK(
        Atibaia.K[0][0],
        Atibaia.X[0][0],
        Atibaia.m[0][0],
        24.0, revAtibainha.D)
    Q2 = DownstreamFORK(
        Atibaia.K[1][0],
        Atibaia.X[1][0],
        Atibaia.m[1][0],
        24.0, revCachoeira.D)

    termoCVA = SMAP(
        paramsAtibaia['Str'],
        paramsAtibaia['k2t'],
        paramsAtibaia['Crec'],
        startAtibaia['TUin'][step - 1], startAtibaia['EBin'][step - 1], obsAtibaia, Atibaia)

    for i in range(n):
        obsAtibaia.Q[i] = (Q1[i] + Q2[i]) + termoCVA[i] - obsAtibaia.C[i]

    # Em Valinhos
    Q = DownstreamFORK(
        Valinhos.K[0],
        Valinhos.X[0],
        Valinhos.m[0],
        24.0, obsAtibaia.Q)

    termoCVV = SMAP(
        paramsValinhos['Str'],
        paramsValinhos['k2t'],
        paramsValinhos['Crec'],
        startValinhos['TUin'][step - 1], startValinhos['EBin'][step - 1], obsValinhos, Valinhos)

    for i in range(n):
        obsValinhos.Q[i] = Q[i] + termoCVV[i] - obsValinhos.C[i]

    return obsAtibaia.Q[29], obsValinhos.Q[29], resultado
