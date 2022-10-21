from Dados.Conexao     import *
from Modelo.Calibracao import *
from Modelo.Previsao   import *
from timeit import default_timer as timer
import pandas as pd

# Inicio de cronometragem
start = timer()

######################################################################
# ETAPA 1:
# Inicializacao de variaveis de interesse
Atibaia = Bacia(
    AD   = 477,
    Capc = 0.5,
    kkt  = 40.0
)
Valinhos = Bacia(
    AD   = 1074,
    Capc = 0.4,
    kkt  = 55.0
)
# Funcao objetivo para otimizacoes
#  1: NSE: Nash-Sutcliffe
#  2: SSQ: Sum of Squares of Deviation
#  3: RMSE: Root-Mean-Square Error
FO = 1

######################################################################
# ETAPA 2:
# Calibracao de variaveis hidrologicas e de routing (tradicional e inverso)
# com 4 meses de dados observados
# Pontos de controle
obsAtibaia  = DBConnection('test', 'Bacias', 'Atibaia' , 'Calibracao')
obsValinhos = DBConnection('test', 'Bacias', 'Valinhos', 'Calibracao')
# Reservatorios
revAtibainha = DBConnection('test', 'Bacias', 'Atibainha', 'Calibracao')
revCachoeira = DBConnection('test', 'Bacias', 'Cachoeira', 'Calibracao')

paramsAtibaia, paramsValinhos, resultados = Calibracao(
    obsAtibaia  , obsValinhos ,
    revAtibainha, revCachoeira,
    Atibaia     , Valinhos    ,
    FO = FO
)
print(resultados)
resultados.to_csv('Resultados/Calibracao.csv')

######################################################################
# ETAPA 3:
# Loop para executar o modelo ao longo de um mes (marco), fazendo
# slices em vetores de calibracao, para caminhar de 30 em 30 dias
# e escolhendo a cada iteracao valores de previsao de chuva de 7 dias

# Dias de marco
n = 31
# Respostas
despachos = {'Atibainha': [], 'Cachoeira': []}
# Dicionarios para armazenamento de parametros apos calibracao
startA = {'TUin': [], 'EBin': []}
startV = {'TUin': [], 'EBin': []}

# Loop para invocar o modelo e extrair uma decisao de cada dia
for j in range(n):
    # Necessario conectar ao banco de dados a cada iteracao para que
    # ao fazer os slices nao haja perda de informacao (recorte em
    # vetores modificados e nao em vetores originais)

    i = j + 29

    # 3.1. OBSERVACAO
    # Pontos de controle (dados observados)
    obsAtibaia  = DBConnection('test', 'Bacias', 'Atibaia' , 'Calibracao')
    obsValinhos = DBConnection('test', 'Bacias', 'Valinhos', 'Calibracao')
    # Slices nos pontos de controle
    obsAtibaia.C  = obsAtibaia.C[i:i + 31]
    obsAtibaia.P  = obsAtibaia.P[i:i + 31]
    obsAtibaia.Q  = obsAtibaia.Q[i:i + 31]
    obsValinhos.C = obsValinhos.C[i:i + 31]
    obsValinhos.P = obsValinhos.P[i:i + 31]
    obsValinhos.Q = obsValinhos.Q[i:i + 31]
    # Reservatorios
    revAtibainha = DBConnection('test', 'Bacias', 'Atibainha', 'Calibracao')
    revCachoeira = DBConnection('test', 'Bacias', 'Cachoeira', 'Calibracao')
    # Slices nos reservatorios
    revAtibainha.D = revAtibainha.D[i:i + 31]
    revCachoeira.D = revCachoeira.D[i:i + 31]

    # 3.2. PREVISAO
    previsao  = DBConnection('test', 'Bacias', '' , 'Previsao')
    # Slices nas previsoes
    previsao.amostras[1] = previsao.amostras[1][i + 30]
    previsao.amostras[2] = previsao.amostras[2][i + 30]
    previsao.amostras[3] = previsao.amostras[3][i + 30]
    previsao.amostras[4] = previsao.amostras[4][i + 30]
    previsao.amostras[5] = previsao.amostras[5][i + 30]
    previsao.amostras[6] = previsao.amostras[6][i + 30]
    previsao.amostras[7] = previsao.amostras[7][i + 30]
    # Importante: para executar o modelo SMAP e necessario fornecer como input
    # uma serie continua de dados de observacao (utilizados para calibrar variaveis)
    # + previsao. Logo, os vetores artificiais devem conter 37 entradas (30 + 7)
    prevAtibaia    = Ponto(C = [], P = [], Q = [], t = [])
    prevAtibaia.P  = prevAtibaia.P  + obsAtibaia.P
    for k in range(7):
        prevAtibaia.P.append(previsao.amostras[k + 1])
    prevValinhos   = Ponto(C = [], P = [], Q = [], t = [])
    prevValinhos.P = prevValinhos.P + obsValinhos.P
    for k in range(7):
        prevValinhos.P.append(previsao.amostras[k + 1])

    # 3.3 INVOCACAO DO MODELO
    resultado = Previsao(
        obsAtibaia   , obsValinhos   ,
        prevAtibaia  , prevValinhos  ,
        paramsAtibaia, paramsValinhos,
        revAtibainha , revCachoeira  ,
        startA       , startV        ,
        Atibaia      , Valinhos      ,
        FO = FO      , step = j + 1
    )

    despachos['Atibainha'] += [resultado.Atibainha]
    despachos['Cachoeira'] += [resultado.Cachoeira]

print()
print(pd.DataFrame(data = despachos))
pd.DataFrame(data = despachos).to_csv('Resultados/Despachos.csv')
# pd.DataFrame(data = startA).to_csv('Resultados/StartA.csv')
# pd.DataFrame(data = startV).to_csv('Resultados/StartV.csv')

# Fim de cronometragem
end = timer()
print('Tempo de execucao: %.3f s' % (end - start))
