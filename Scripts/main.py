from Dados.Conexao  import *
from Scripts.Modelo import *
from timeit import default_timer as timer
import random

# Inicio de cronometragem
start = timer()

######################################################################
# ETAPA 1:
# Inicializacao de variaveis de interesse (bacias)
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

######################################################################
# ETAPA 2:
# Loop para executar o modelo ao longo de um mes (marco), fazendo
# slices em vetores de calibracao, para caminhar de 60 em 60 dias
# (2 meses), e escolhendo a cada iteracao valores aleatorios de chuva
# para simular dados de previsao de 10 em 10 dias

# Dias de marco
n = 31
# Com ou sem graficos
flag = 'comGraficos'
# Funcao objetivo para otimizacoes
#  1: NSE: Nash-Sutcliffe
#  2: SSQ: Sum of Squares of Deviation
#  3: (I)RMSE: (Inverse) Root-Mean-Square Error
FO = 3

# Loop para invocar o modelo e extrair uma decisao de cada dia
for i in range(n):
    # Necessario conectar ao banco de dados a cada iteracao para que
    # ao fazer os slices nao haja perda de informacao (recorte em
    # vetores modificados e nao em vetores originais)

    # 2.1. OBSERVACAO
    # Pontos de controle (dados observados)
    obsAtibaia  = DBConnection("test", "Bacias", "Atibaia" , "Calibracao")
    obsValinhos = DBConnection("test", "Bacias", "Valinhos", "Calibracao")
    # Slices nos pontos de controle
    obsAtibaia.C  = obsAtibaia.C[i:i + 60]
    obsAtibaia.P  = obsAtibaia.P[i:i + 60]
    obsAtibaia.Q  = obsAtibaia.Q[i:i + 60]
    obsValinhos.C = obsValinhos.C[i:i + 60]
    obsValinhos.P = obsValinhos.P[i:i + 60]
    obsValinhos.Q = obsValinhos.Q[i:i + 60]
    # Reservatorios
    revAtibainha = DBConnection("test", "Bacias", "Atibainha", "Calibracao")
    revCachoeira = DBConnection("test", "Bacias", "Cachoeira", "Calibracao")
    # Slices nos reservatorios
    revAtibainha.D = revAtibainha.D[i:i + 60]
    revCachoeira.D = revCachoeira.D[i:i + 60]

    # 2.2. PREVISAO
    prevAtibaia  = DBConnection("test", "Bacias", "Atibaia" , "Previsoes")
    prevValinhos = DBConnection("test", "Bacias", "Valinhos", "Previsoes")
    # Slices nas previsoes de Atibaia
    prevAtibaia.amostras[1] = prevAtibaia.amostras[1][i + 1:i + 11]
    prevAtibaia.amostras[2] = prevAtibaia.amostras[2][i + 1:i + 11]
    prevAtibaia.amostras[3] = prevAtibaia.amostras[3][i + 1:i + 11]
    prevAtibaia.amostras[4] = prevAtibaia.amostras[4][i + 1:i + 11]
    prevAtibaia.amostras[5] = prevAtibaia.amostras[5][i + 1:i + 11]
    # Slices nas previsoes de Valinhos
    prevValinhos.amostras[1] = prevValinhos.amostras[1][i + 1:i + 11]
    prevValinhos.amostras[2] = prevValinhos.amostras[2][i + 1:i + 11]
    prevValinhos.amostras[3] = prevValinhos.amostras[3][i + 1:i + 11]
    prevValinhos.amostras[4] = prevValinhos.amostras[4][i + 1:i + 11]
    prevValinhos.amostras[5] = prevValinhos.amostras[5][i + 1:i + 11]
    # Randomizacao de observacoes de 2016 a 2020 para construir artificialmente
    # uma previsao de 10 dias consecutivos
    # Importante: para executar o modelo SMAP e necessario fornecer como input
    # uma serie continua de dados de observacao (utilizados para calibrar variaveis)
    # + previsao. Logo, os vetores artificiais devem conter 70 entradas (60 + 10)
    prevArtAtibaia    = Ponto(C = [], P = [], Q = [], t = [])
    prevArtAtibaia.P  = prevArtAtibaia.P  + obsAtibaia.P
    for j in range(10):
        prevArtAtibaia.P.append(prevAtibaia.amostras[random.randrange(1, 6, 1)][j])
    prevArtValinhos   = Ponto(C = [], P = [], Q = [], t = [])
    prevArtValinhos.P = prevArtValinhos.P + obsValinhos.P
    for j in range(10):
        prevArtValinhos.P.append(prevValinhos.amostras[random.randrange(1, 6, 1)][j])

    # 2.3 INVOCACAO DO MODELO
    Modelo(
        obsAtibaia    , obsValinhos    ,
        revAtibainha  , revCachoeira   ,
        prevArtAtibaia, prevArtValinhos,
        Atibaia       , Valinhos       ,
        flag          , step = i       ,
        FO = FO
    )

# Fim de cronometragem
end = timer()
print("Tempo de execucao: %.3f s" % (end - start))
