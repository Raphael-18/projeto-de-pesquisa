from Dados.Conexao import *
from Metodos.Muskingum.Upstream import *
from Metodos.SMAP import *
from scipy.optimize import differential_evolution
import numpy as np

# Logica de conexao e busca de dados (banco)
Calibracao = Store("test", "Bacias", "Valinhos", "Calibração")
Previsao   = Store("test", "Bacias", "Valinhos", "Previsão"  )
# Inicializacao de objetos
Valinhos = Bacia(
    AD   = 1074,
    Capc = 0.4,
    EB   = 11.1456,
    kkt  = 55.0
)
# Condicoes de contorno para variaveis que serao calibradas
bounds = [[100.0, 2000.0], [0.2, 10.0], [0.0, 20.0]]
# Funcao objetivo que maximiza coeficiente
# de Nash-Sutcliffe (para Valinhos)
def objective1(p):
    Str, k2t, Crec = p

    Q = SMAP(Str, k2t, Crec, Calibracao, Valinhos)

    a = 0
    b = 0
    Qm = np.mean(Calibracao.Q)
    for i in range(len(Calibracao.Q)):
        a += (Calibracao.Q[i] - Q[i]) ** 2
        b += (Calibracao.Q[i] - Qm) ** 2

    return a / b


# Busca por evolucao diferencial
result1 = differential_evolution(objective1, bounds)

# Resultados
print('Valinhos:')
print('Status : %s' % result1['message'])
print('Avaliações realizadas: %d' % result1['nfev'])

# Solucao
solution1 = result1['x']
evaluation1 = objective1(solution1)
print('Solução: f([%.3f \t %.3f \t %.3f]) = %.3f' % (solution1[0], solution1[1], solution1[2], evaluation1))

Qcalc = SMAP(solution1[0], solution1[1], solution1[2], Previsao, Valinhos)
# Verificacao de atendimento ao minimo outorgavel em Valinhos (10 m3/s)
# e repasse para o hidrograma que sera deslocado ate Atibaia
deficit = []
for i in range(len(Qcalc)):
    if Qcalc[i] > 14:
        deficit.append(0)
    else:
        deficit.append(14 - Qcalc[i])

# Muskingum para Atibaia
# K = 3.5 dias (de Valinhos para Atibaia)
# X = 0.3 (fator de amortecimento geral)
pAtibaia = UpstreamRouting(deficit, 3.5, 0.3)

# Logica de conexao e busca de dados (banco)
Calibracao = Store("test", "Bacias", "Atibaia", "Calibração")
Previsao   = Store("test", "Bacias", "Atibaia", "Previsão"  )
# Inicializacao de objetos
Atibaia = Bacia(
    AD   = 477,
    Capc = 0.5,
    EB   = 7.5899,
    kkt  = 40.0
)
# Funcao objetivo que maximiza coeficiente
# de Nash-Sutcliffe (para Valinhos)
def objective2(p):
    Str, k2t, Crec = p

    Q = SMAP(Str, k2t, Crec, Calibracao, Atibaia)

    a = 0
    b = 0
    Qm = np.mean(Calibracao.Q)
    for i in range(len(Calibracao.Q)):
        a += (Calibracao.Q[i] - Q[i]) ** 2
        b += (Calibracao.Q[i] - Qm) ** 2

    return a / b


# Busca por evolucao diferencial
result2 = differential_evolution(objective2, bounds)

# Resultados
print('Atibaia:')
print('Status : %s' % result1['message'])
print('Avaliações realizadas: %d' % result1['nfev'])

# Solucao
solution2 = result2['x']
evaluation2 = objective2(solution2)
print('Solução: f([%.3f \t %.3f \t %.3f]) = %.3f' % (solution2[0], solution2[1], solution2[2], evaluation2))

Qcalc = SMAP(solution2[0], solution2[1], solution2[2], Previsao, Atibaia)
# Verificacao de atendimento ao minimo outorgavel em Atibaia (2 m3/s)
deficit = []
for i in range(len(Qcalc)):
    if Qcalc[i] > 10:
        deficit.append(0)
    else:
        deficit.append(10 - Qcalc[i])
# Verificacao com o translado de Valinhos para Atibaia
deficit2 = []
for i in range(len(pAtibaia)):
    if pAtibaia[i] != 0:
        if Qcalc[i] > pAtibaia[i]:
            deficit2.append(0)
        else:
            deficit2.append(pAtibaia[i] - Qcalc[i])
    else:
        deficit2.append(0)
# Necessario comparar a maior diferenca nao nula entre
# os dois deficits antes de dividir para os reservatorios
pReservatorios = []
for i in range(len(deficit)):
    pReservatorios.append(max(deficit[i], deficit2[i]))

# Regra simples: separar vazoes ao meio e encaminhar para
# Atibainha e Cachoeira
for i in range(len(pReservatorios)):
    pReservatorios[i] /= 2.0
# Muskingum para Atibainha
# K = 4.9 dias (de Atibaia para Atibainha)
# X = 0.3 (fator de amortecimento geral)
pAtibainha = UpstreamRouting(pReservatorios, 4.9, 0.3)
# Muskingum para Cachoeira
# K = 2.6 dias (de Atibaia para Cachoeira)
# X = 0.3 (fator de amortecimento geral)
pCachoeira = UpstreamRouting(pReservatorios, 2.6, 0.3)
