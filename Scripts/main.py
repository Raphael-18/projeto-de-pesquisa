from Dados.Conexao import *
from Metodos.Muskingum.Downstream import *
from Metodos.Muskingum.Upstream   import *
from Metodos.SMAP   import *
from scipy.optimize import differential_evolution
import numpy as np

# 1. Conexao com banco para resgatar despachos de Atibainha e Cachoeira
Atibainha = Store("test", "Bacias", "Atibainha", "Calibracao")
Cachoeira = Store("test", "Bacias", "Cachoeira", "Calibracao")

# 2. Muskingum de jusante ate o posto de controle de Atibaia
# K = 4.9 dias (de Atibainha para Atibaia)
# K = 2.6 dias (de Cachoeira para Atibaia)
# X = 0.3 (fator de amortecimento geral)
# p/ Atibainha: necessario subdividir o metodo em 5 passos
j = 1
pAtibaia1  = DownstreamRouting(Atibainha.D, 4.9 / 5, 0.3, 1.0)
while j < 5:
    pAtibaia1 = DownstreamRouting(pAtibaia1, 4.9 / 5, 0.3, 1.0)
    j = j + 1
# p/ Cachoeira: necessario subdividir o metodo em 3 passos
j = 1
pAtibaia2  = DownstreamRouting(Cachoeira.D, 2.6 / 3, 0.3, 1.0)
while j < 3:
    pAtibaia2 = DownstreamRouting(pAtibaia2, 2.6 / 3, 0.3, 1.0)
    j = j + 1
# Somatorio de hidrogramas transladados
despachado = []
n = len(Atibainha.D)
for i in range(n):
    despachado.append(pAtibaia1[i] + pAtibaia2[i])

# 3.1. Resgate de vazoes observadas em Atibaia
Dados1 = Store("test", "Bacias", "Atibaia", "Calibracao")

# 3.2. Muskingum de jusante ate o posto de controle de Valinhos
# K = 3.5 dias (de Atibaia para Valinhos)
# X = 0.3 (fator de amortecimento geral)
# p/ Valinhos: necessario subdividir o metodo em 4 passos
j = 1
pValinhos  = DownstreamRouting(Dados1.Q, 3.5 / 4, 0.3, 1.0)
while j < 4:
    pValinhos = DownstreamRouting(pValinhos, 3.5 / 4, 0.3, 1.0)
    j = j + 1

# 4.1. Resgate de vazoes observadas e dados em Valinhos
Dados2 = Store("test", "Bacias", "Valinhos", "Calibracao")

# 4.2. Separacao de vazoes em Valinhos para obter as incrementais
incrementais = []
for i in range(n):
    incrementais.append(Dados2.Q[i] - pValinhos[i])

# 4.3. Objeto
Valinhos = Bacia(
    AD   = 1074,
    Capc = 0.4,
    EB   = 0.95 * min(incrementais),
    kkt  = 55.0
)

# 4.4. Calibracao SMAP para Valinhos
# Condicoes de contorno para variaveis que serao calibradas
bounds = [[100.0, 2000.0], [0.2, 10.0], [0.0, 20.0]]
# Funcao objetivo que maximiza NSE
def objective1(p):
    Str, k2t, Crec = p
    Q = SMAP(Str, k2t, Crec, Dados2, Valinhos)

    a = 0
    b = 0
    Qm = np.mean(incrementais)
    for i in range(n):
        a += (incrementais[i] - Q[i]) ** 2
        b += (incrementais[i] - Qm) ** 2

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

# 5.1. Separacao de vazoes em Atibaia para obter as incrementais
incrementais = []
for i in range(n):
    incrementais.append(Dados1.Q[i] - despachado[i])

# 5.2. Objeto
Atibaia = Bacia(
    AD   = 477,
    Capc = 0.5,
    EB   = 0.95 * min(incrementais),
    kkt  = 40.0
)

# 5.3. Calibracao SMAP para Atibaia
# Funcao objetivo que maximiza NSE
def objective2(p):
    Str, k2t, Crec = p
    Q = SMAP(Str, k2t, Crec, Dados1, Atibaia)

    a = 0
    b = 0
    Qm = np.mean(incrementais)
    for i in range(n):
        a += (incrementais[i] - Q[i]) ** 2
        b += (incrementais[i] - Qm) ** 2

    return a / b
# Busca por evolucao diferencial
result2 = differential_evolution(objective2, bounds)
# Resultados
print()
print('Atibaia:')
print('Status : %s' % result2['message'])
print('Avaliações realizadas: %d' % result2['nfev'])
# Solucao
solution2 = result2['x']
evaluation2 = objective2(solution2)
print('Solução: f([%.3f \t %.3f \t %.3f]) = %.3f' % (solution2[0], solution2[1], solution2[2], evaluation2))

# 6. Conexao com banco para resgatar previsoes de chuva
Dados3 = Store("test", "Bacias", "Atibaia" , "Previsao")
Dados4 = Store("test", "Bacias", "Valinhos", "Previsao")

# 7. Calculo de vazoes previstas com parametros SMAP calibrados para cada sub-bacia
calcAtibaia  = SMAP(solution2[0], solution2[1], solution2[2], Dados3, Atibaia )
calcValinhos = SMAP(solution1[0], solution1[1], solution1[2], Dados4, Valinhos)

# 8.1. Verificacao de atendimento ao minimo outorgavel em Valinhos (10 m3/s)
# e repasse para o hidrograma que sera deslocado ate Atibaia
m = len(calcValinhos)
deficit = []
for i in range(m):
    if calcValinhos[i] > 10:
        deficit.append(0)
    else:
        deficit.append(10 - calcValinhos[i])

# 8.2. Muskingum para Atibaia
# K = 3.5 dias (de Valinhos para Atibaia)
# X = 0.3 (fator de amortecimento geral)
uAtibaia = UpstreamRouting(deficit, 3.5, 0.3)

# 8.3.1. Verificacao de atendimento ao minimo outorgavel em Atibaia (2 m3/s)
deficit = []
for i in range(m):
    if calcAtibaia[i] > 2:
        deficit.append(0)
    else:
        deficit.append(2 - calcAtibaia[i])
# 8.3.2. Verificacao com o translado de Valinhos para Atibaia
deficit2 = []
for i in range(m):
    if uAtibaia[i] != 0:
        if calcAtibaia[i] > uAtibaia[i]:
            deficit2.append(0)
        else:
            deficit2.append(uAtibaia[i] - calcAtibaia[i])
    else:
        deficit2.append(0)

# 8.4. Necessario comparar a maior diferenca nao nula entre
# os dois deficits antes de dividir para os reservatorios
pReservatorios = []
for i in range(m):
    pReservatorios.append(max(deficit[i], deficit2[i]))

# 9. Regra simples: separar vazoes ao meio e encaminhar para
# Atibainha e Cachoeira
for i in range(m):
    pReservatorios[i] /= 2.0
# Muskingum para Atibainha
# K = 4.9 dias (de Atibaia para Atibainha)
# X = 0.3 (fator de amortecimento geral)
pAtibainha = UpstreamRouting(pReservatorios, 4.9, 0.3)
# Muskingum para Cachoeira
# K = 2.6 dias (de Atibaia para Cachoeira)
# X = 0.3 (fator de amortecimento geral)
pCachoeira = UpstreamRouting(pReservatorios, 2.6, 0.3)
