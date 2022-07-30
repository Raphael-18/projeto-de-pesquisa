from Dados.Conexao  import *
from Scripts.Modelo import *
from timeit import default_timer as timer
import random

# Inicio da cronometragem do algoritmo
start = timer()

######################################################################
# ETAPA 1:
# Inicializacao de variaveis de interesse (bacias)

# (A instanciacao de EBmin sera feita via loop)
Atibaia = Bacia(
    AD   = 477,
    Capc = 0.5,
    EB   = None,
    kkt  = 40.0
)
Valinhos = Bacia(
    AD   = 1074,
    Capc = 0.4,
    EB   = None,
    kkt  = 55.0
)

######################################################################
# ETAPA 2:
# Loop para executar o modelo ao longo de um mes (marco), fazendo
# slices nos vetores de calibracao, para caminhar de 59 em 59 dias
# (2 meses) e escolhendo a cada iteracao valores aleatorios de chuva
# para simular dados de previsao de 10 em 10 dias

# Dias de marco
n = 31
# Respostas diarias
despachoAtibainha = []
despachoCachoeira = []
# Loop para invocar o modelo e extrair uma decisao de cada dia
for i in range(n):
    # Necessario conectar ao banco de dados a cada iteracao para que
    # ao fazer os slices nao haja perda de informacao (recorte em
    # vetores modificados e nao nos originais)

    # Pontos de controle (dados observados)
    obsAtibaia  = DBConnection("test", "Bacias", "Atibaia" , "Calibracao")
    obsValinhos = DBConnection("test", "Bacias", "Valinhos", "Calibracao")
    # Slices nos pontos de controle
    obsAtibaia.C  = obsAtibaia.C[i:i + 59]
    obsAtibaia.P  = obsAtibaia.P[i:i + 59]
    obsAtibaia.Q  = obsAtibaia.Q[i:i + 59]
    obsValinhos.C = obsValinhos.C[i:i + 59]
    obsValinhos.P = obsValinhos.P[i:i + 59]
    obsValinhos.Q = obsValinhos.Q[i:i + 59]

    # Reservatorios
    revAtibainha = DBConnection("test", "Bacias", "Atibainha", "Calibracao")
    revCachoeira = DBConnection("test", "Bacias", "Cachoeira", "Calibracao")
    # Slices nos reservatorios
    revAtibainha.D = revAtibainha.D[i:i + 59]
    revCachoeira.D = revCachoeira.D[i:i + 59]

    # Previsoes
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
    prevArtAtibaia = Ponto(C = [], P = [], Q = [], t = [])
    for j in range(10):
        prevArtAtibaia.P.append(prevAtibaia.amostras[random.randrange(1, 6, 1)][j])
    prevArtValinhos = Ponto(C = [], P = [], Q = [], t = [])
    for j in range(10):
        prevArtValinhos.P.append(prevValinhos.amostras[random.randrange(1, 6, 1)][j])

    # Invocacao do modelo
    decisao = Modelo(
        obsAtibaia, obsValinhos,
        revAtibainha, revCachoeira,
        prevArtAtibaia, prevArtValinhos,
        Atibaia, Valinhos
    )
    # Armazenamento em vetores
    despachoAtibainha.append(decisao.Atibainha)
    despachoCachoeira.append(decisao.Cachoeira)

print(despachoAtibainha)
print(despachoCachoeira)

# Fim da cronometragem do algoritmo
end = timer()
print("Tempo de execucao: %.3f s" % (end - start))
