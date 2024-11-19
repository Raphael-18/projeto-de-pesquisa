import numpy as np
import pandas as pd
from scipy.optimize import differential_evolution

from Metodos.SMAP import SMAP
from Metodos.Muskingum.Downstream import DownstreamFORK
from Metodos.Muskingum.Upstream import UpstreamFORK
from Metodos.Otimizacoes import KGE, NSE, RMSE, SSQ


def Calibracao(
        # Captações, chuvas, vazões e evapotranspirações observadas nos pontos
        obsAtibaia, obsValinhos,
        revAtibainha, revCachoeira,  # Despachos observados nos reservatórios
        Atibaia, Valinhos,  # Bacias
        FO  # Função objetivo p/ otimizações
):
    # 1. Muskingum de jusante até o ponto de controle de Atibaia:
    # O modelo utilizará como parâmetros duas trincas de variáveis Muskingum
    # (K1, X1, m1) p/ Atibainha e (K2, X2, m2) p/ Cachoeira e também uma quina
    # de variáveis SMAP (Str, k2t, Crec, TUin, EBin). O objetivo será minimizar
    # as diferenças entre as vazões incrementais calculadas com o routing hidrológico
    # e aquelas obtidas com o módulo chuva-vazão.
    # Principalmente em períodos secos, pode-se observar que mesmo com os despachos em
    # cada barragem, os dados de vazão observados indicam que uma parcela de água foi
    # "perdida" entre os reservatórios e a seção de Atibaia (ou seja, Qobs + Capt. < Desp.). Para
    # corrigir o fenômeno (que leva a vazões negativas durante o routing de Muskingum), deve-se
    # introduzir um coeficiente Cp de perdas.
    # Condições de contorno para variáveis que serão calibradas:
    bounds = [
        [1000.0, 2000.0], # Str
        [0.2, 4.0], # k2t
        [0.0, 1.0], # Crec
        [0.0, 1.0], # TUin
        [0.1, 9.2], # EBin
        [0.1, 0.2] # Cp (forçando o modelo a não escolher Cp = 0)
    ]

    n = len(obsAtibaia.Q)

    # Função objetivo
    def objective(p):
        # Sujeitos a calibração
        Str, k2t, Crec, TUin, EBin, Cp = p

        # Routing de jusante não linear 1: de Atibainha para Atibaia
        Q1 = DownstreamFORK(Atibaia.K[0][0], Atibaia.X[0][0], Atibaia.m[0][0], 24.0, revAtibainha.D)
        # Routing de jusante não linear 2: de Cachoeira para Atibaia
        Q2 = DownstreamFORK(Atibaia.K[1][0], Atibaia.X[1][0], Atibaia.m[1][0], 24.0, revCachoeira.D)

        # Junto ao ponto de controle, a vazão observada equivale a uma parcela
        # despachada de cada reservatório mais uma parcela incremental de eventos chuvosos
        # menos uma parcela captada entre as barragens e a própria seção e menos uma perda
        # por infiltração entre os pontos.
        inc1 = pd.DataFrame([0] * n)
        Q1 = pd.DataFrame(Q1)
        Q2 = pd.DataFrame(Q2)
        inc1 = np.array(obsAtibaia.Q - ((1 - Cp) * (Q1 + Q2)) + obsAtibaia.C)

        # Segundo vetor incremental ("calc")
        inc2 = np.array(SMAP(Str, k2t, Crec, TUin, EBin, obsAtibaia, Atibaia))

        print('Tentando calibrar (Atibaia)...')

        # Restrição positiva aos routings calculados e às vazões incrementais
        if np.min(Q1) < 0 or np.min(Q2) < 0 or np.min(inc1) < 0 or np.min(inc2) < 0:
            return float('inf')
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
    print('Muskingum de jusante e SMAP')
    print('Atibaia:')
    print('Status: %s' % result['message'])
    print('Avaliações realizadas: %d' % result['nfev'])
    # Solução
    solution = result['x']
    evaluation = objective(solution)
    print('Solução: \n'
          'f = ( \n'
          '\t[Str = %.3f \n\t k2t = %.3f \n\t Crec = %.3f \n\t TUin = %.3f \n\t EBin = %.3f \n\t Cp = %.2f]'
          % (
              solution[0], solution[1], solution[2], solution[3], solution[4], solution[5]))
    if FO == 1 or FO == 4:
        print(') = %.3f' % (1 - evaluation))
    else:
        print(') = %.3f' % evaluation)

    # Armazenamento em dicionário para utilização durante etapa de previsão
    # (K, X e m com final 1 referem-se a Atibainha; aqueles com final 2 são de Cachoeira)
    paramsAtibaia = {
        'Str': solution[0],
        'k2t': solution[1],
        'Crec': solution[2],
        'Cp': solution[5]
    }

    # 2. Checagem de incrementais e conversão chuva-vazão para o período observado em Atibaia:
    # As incrementais são necessárias para averiguar como as vazões obtidas com os parâmetros calibrados
    # adequam-se aos dados "observados" (também advindos de uma calibração própria, devido à parcela de despacho).
    newQ1 = DownstreamFORK(Atibaia.K[0][0], Atibaia.X[0][0], Atibaia.m[0][0], 24.0, revAtibainha.D)
    newQ2 = DownstreamFORK(Atibaia.K[1][0], Atibaia.X[1][0], Atibaia.m[1][0], 24.0, revCachoeira.D)

    incAtibaia = pd.DataFrame([0] * n)
    newQ1 = pd.DataFrame(newQ1)
    newQ2 = pd.DataFrame(newQ2)
    incAtibaia = obsAtibaia.Q - ((1 - solution[5]) * (newQ1 + newQ2)) + obsAtibaia.C

    calcAtibaia = SMAP(solution[0], solution[1], solution[2],
                       solution[3], solution[4], obsAtibaia, Atibaia)

    # 3. Muskingum de jusante até o ponto de controle de Valinhos:
    # Semelhante ao passo 1., porém com uma trinca de variáveis Muskingum (K, X, m) ao invés de duas.
    # Condições de contorno para variáveis que serão calibradas:
    bounds = [
        [1000.0, 2000.0], # Str
        [0.2, 6.0], # k2t
        [0.0, 20.0], # Crec
        [0.0, 1.0], # TUin
        [0.1, 40.0], # EBin
        [0.1, 0.2] # Cp (forçando o modelo a não escolher Cp = 0)
    ]

    # Função objetivo
    def objective(p):
        # Sujeitos a calibração
        Str, k2t, Crec, TUin, EBin, Cp = p

        # Routing de jusante não linear: de Atibaia para Valinhos
        Q = DownstreamFORK(Valinhos.K[0], Valinhos.X[0], Valinhos.m[0], 24.0, obsAtibaia.Q)

        # Junto ao ponto de controle, a vazão observada equivale a uma parcela
        # despachada de cada reservatório mais uma parcela incremental de eventos chuvosos
        # menos uma parcela captada entre as barragens e a própria seção e menos uma perda
        # por infiltração entre os pontos.
        inc1 = pd.DataFrame([0] * n)
        Q = pd.DataFrame(Q)
        inc1 = obsValinhos.Q - ((1 - Cp) * Q) + obsValinhos.C

        # Segundo vetor incremental ("calc")
        inc2 = SMAP(Str, k2t, Crec, TUin, EBin, obsValinhos, Valinhos)

        print('Tentando calibrar (Valinhos)...')

        # Restrição positiva aos routings calculados e às vazões incrementais
        minQ, res1, res2 = min(Q), min(inc1), min(inc2)
        if minQ < 0 or res1 < 0 or res2 < 0:
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
    print()
    print('Valinhos:')
    print('Status: %s' % result['message'])
    print('Avaliações realizadas: %d' % result['nfev'])
    # Solução
    solution = result['x']
    evaluation = objective(solution)
    print('Solução: \n'
          'f = ( \n'
          '\t[Str = %.3f \n\t k2t = %.3f \n\t Crec = %.3f \n\t TUin = %.3f \n\t EBin = %.3f \n\t Cp = %.2f]'
          % (
              solution[0], solution[1], solution[2], solution[3], solution[4], solution[5]))
    if FO == 1 or FO == 4:
        print(') = %.3f\n' % (1 - evaluation))
    else:
        print(') = %.3f\n' % evaluation)

    # Armazenamento em dicionário para utilização durante etapa de previsão
    paramsValinhos = {
        'Str': solution[0],
        'k2t': solution[1],
        'Crec': solution[2],
        'Cp': solution[5]
    }

    # 4. Checagem de incrementais e conversão chuva-vazão para o período observado em Valinhos:
    # As incrementais são necessárias para averiguar como as vazões obtidas com os parâmetros calibrados
    # adequam-se aos dados "observados" (também advindos de uma calibração própria, devido à parcela de despacho).
    newQ = DownstreamFORK(Valinhos.K[0], Valinhos.X[0], Valinhos.m[0], 24.0, obsAtibaia.Q)
    
    incValinhos = pd.DataFrame([0] * n)
    newQ = pd.DataFrame(newQ)
    incValinhos = obsValinhos.Q - ((1 - solution[5]) * newQ) + obsValinhos.C

    calcValinhos = SMAP(solution[0], solution[1], solution[2],
                        solution[3], solution[4], obsValinhos, Valinhos)

    # 5. Muskingum de montante até o ponto de controle de Atibaia:
    desp = pd.DataFrame([0] * n)
    desp = (obsValinhos.Q + obsValinhos.C - incValinhos) / (1 - paramsValinhos['Cp'])
    # Armazenamento para plotagem
    upVA = UpstreamFORK(Valinhos.K[1], Valinhos.X[1], Valinhos.m[1], 24.0, desp)

    # 6. Muskingum de montante até reservatórios:
    reserv = pd.DataFrame([0] * n)
    reserv = (obsAtibaia.Q + obsAtibaia.C - incAtibaia) / (1 - paramsAtibaia['Cp'])

    alfa = 0.5
    upAA = UpstreamFORK(Atibaia.K[0][1], Atibaia.X[0][1], Atibaia.m[0][1], 24.0, list(
        np.multiply(reserv, alfa)))

    beta = 0.5
    upAC = UpstreamFORK(Atibaia.K[1][1], Atibaia.X[1][1], Atibaia.m[1][1], 24.0, list(
        np.multiply(reserv, beta)))

    resultados = pd.DataFrame(data={
        'Dia':  obsAtibaia.t,
        'Pluv. de Atibaia': obsAtibaia.P,
        'Pluv. de Valinhos': obsValinhos.P,
        'Vazao de Atibaia': obsAtibaia.Q,
        'Musk de Atibaia': incAtibaia,
        'SMAP de Atibaia': calcAtibaia,
        'Vazao de Valinhos': obsValinhos.Q,
        'Musk de Valinhos': incValinhos,
        'SMAP de Valinhos': calcValinhos,
        'Upst. VA': upVA,
        'Upst. AA': upAA,
        'Upst. AC': upAC
    })

    return paramsAtibaia, paramsValinhos, resultados
