from Dados.Conexao     import *
from Modelo.Calibracao import *
from Modelo.Previsao   import *
from numpy  import trapz
from timeit import default_timer as timer
import pandas as pd

# Início de cronometragem
start = timer()

######################################################################
# ETAPA 1:
# Inicialização de variáveis de interesse
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
# Função objetivo para otimizações
#  1: NSE: Nash-Sutcliffe
#  2: SSQ: Sum of Squares of Deviation
#  3: RMSE: Root-Mean-Square Error
FO = 1
# Tipo de simulação
# 'Previsoes': com previsões meteorológicas
# 'Bola de cristal': com precipitações observadas
simulacao = 'Bola de cristal'

######################################################################
# ETAPA 2:
# Calibração de variáveis hidrológicas e de routing (tradicional e inverso)
# com 4 meses de dados observados
# Pontos de controle
obsAtibaia  = DBConnection('test', 'Bacias', 'Atibaia' , 'Calibracao')
obsValinhos = DBConnection('test', 'Bacias', 'Valinhos', 'Calibracao')
# Reservatórios
revAtibainha = DBConnection('test', 'Bacias', 'Atibainha', 'Calibracao')
revCachoeira = DBConnection('test', 'Bacias', 'Cachoeira', 'Calibracao')

paramsAtibaia, paramsValinhos, resultados = Calibracao(
    obsAtibaia  , obsValinhos ,
    revAtibainha, revCachoeira,
    Atibaia     , Valinhos    ,
    FO = FO
)
resultados.to_excel('Resultados/Calibracao.xlsx')
print(resultados)

######################################################################
# ETAPA 3:
# Loop para executar o modelo ao longo de um mês (março), fazendo
# slices em vetores de calibração, para caminhar de 30 em 30 dias
# e escolhendo a cada iteração valores de previsão de chuva de 7 dias

# Dias de março
n = 31
# Respostas
despachos    = {'Atibainha': [], 'Cachoeira': []}
atendimentos = {'Atibaia'  : [], 'Valinhos' : []}
# Dicionários para armazenamento de parâmetros após calibração
startA = {'TUin': [], 'EBin': []}
startV = {'TUin': [], 'EBin': []}

# Loop para invocar o modelo e extrair uma decisão de cada dia
for j in range(n):
    # Necessário conectar ao banco de dados a cada iteração para que
    # ao fazer os slices não haja perda de informação (recorte em
    # vetores modificados e não em vetores originais)
    i = j + 29

    # 3.1. OBSERVAÇÃO
    # Pontos de controle (dados observados)
    dadosAtibaia  = DBConnection('test', 'Bacias', 'Atibaia' , 'Calibracao')
    dadosValinhos = DBConnection('test', 'Bacias', 'Valinhos', 'Calibracao')
    # Assinatura nos objetos a serem passados ao método de previsão
    obsAtibaia.C  = dadosAtibaia.C
    obsAtibaia.P  = dadosAtibaia.P
    obsValinhos.C = dadosValinhos.C
    obsValinhos.P = dadosValinhos.P
    # Slices nos pontos de controle
    obsAtibaia.C  = obsAtibaia.C[i:i + 30]
    obsAtibaia.P  = obsAtibaia.P[i:i + 30]
    obsValinhos.C = obsValinhos.C[i:i + 30]
    obsValinhos.P = obsValinhos.P[i:i + 30]

    if j == 0:
        # Slice em Atibaia
        obsAtibaia.Q  = obsAtibaia.Q[i:i + 30]
        # Slice em Valinhos
        obsValinhos.Q = obsValinhos.Q[i:i + 30]
        # Slices nos reservatorios
        revAtibainha.D = revAtibainha.D[i:i + 30]
        revCachoeira.D = revCachoeira.D[i:i + 30]

    # 3.2. PREVISÃO
    if simulacao == 'Previsoes':
        previsao  = DBConnection('test', 'Bacias', '', 'Previsao')
        # Slices nas previsões
        previsao.amostras[1] = previsao.amostras[1][i + 30]
        previsao.amostras[2] = previsao.amostras[2][i + 30]
        previsao.amostras[3] = previsao.amostras[3][i + 30]
        previsao.amostras[4] = previsao.amostras[4][i + 30]
        previsao.amostras[5] = previsao.amostras[5][i + 30]
        previsao.amostras[6] = previsao.amostras[6][i + 30]
        previsao.amostras[7] = previsao.amostras[7][i + 30]
        # Vetores de 7 dias de previsão
        prevAtibaia  = Ponto(C = [], P = [], Q = [], t = [])
        for k in range(7):
            prevAtibaia.P.append(previsao.amostras[k + 1])
        prevValinhos = Ponto(C = [], P = [], Q = [], t = [])
        for k in range(7):
            prevValinhos.P.append(previsao.amostras[k + 1])
    else:
        # Atibaia
        previsaoA = DBConnection('test', 'Bacias', '', 'Cristal_A')
        # Slices nas previsões
        previsaoA.amostras[1] = previsaoA.amostras[1][i + 30]
        previsaoA.amostras[2] = previsaoA.amostras[2][i + 30]
        previsaoA.amostras[3] = previsaoA.amostras[3][i + 30]
        previsaoA.amostras[4] = previsaoA.amostras[4][i + 30]
        previsaoA.amostras[5] = previsaoA.amostras[5][i + 30]
        previsaoA.amostras[6] = previsaoA.amostras[6][i + 30]
        previsaoA.amostras[7] = previsaoA.amostras[7][i + 30]
        # Vetores de 7 dias de previsão
        prevAtibaia = Ponto(C = [], P = [], Q = [], t = [])
        for k in range(7):
            prevAtibaia.P.append(previsaoA.amostras[k + 1])
        # Valinhos
        previsaoV = DBConnection('test', 'Bacias', '', 'Cristal_V')
        # Slices nas previsões
        previsaoV.amostras[1] = previsaoV.amostras[1][i + 30]
        previsaoV.amostras[2] = previsaoV.amostras[2][i + 30]
        previsaoV.amostras[3] = previsaoV.amostras[3][i + 30]
        previsaoV.amostras[4] = previsaoV.amostras[4][i + 30]
        previsaoV.amostras[5] = previsaoV.amostras[5][i + 30]
        previsaoV.amostras[6] = previsaoV.amostras[6][i + 30]
        previsaoV.amostras[7] = previsaoV.amostras[7][i + 30]
        # Vetores de 7 dias de previsão
        prevValinhos = Ponto(C = [], P = [], Q = [], t = [])
        for k in range(7):
            prevValinhos.P.append(previsaoV.amostras[k + 1])

    # 3.3 INVOCAÇÃO DO MODELO
    checkAtibaia, checkValinhos, resultado = Previsao(
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

    atendimentos['Atibaia']  += [checkAtibaia]
    atendimentos['Valinhos'] += [checkValinhos]

pd.DataFrame(data = despachos).to_excel('Resultados/Despachos.xlsx')
pd.DataFrame(data = atendimentos).to_excel('Resultados/Atendimentos.xlsx')
print()
print(pd.DataFrame(data = despachos))
print()
print(pd.DataFrame(data = atendimentos))

# Volumes descarregados
volAtibainha = trapz(despachos['Atibainha'], dx = 1) * (86400 / 1000000.0)
volCachoeira = trapz(despachos['Cachoeira'], dx = 1) * (86400 / 1000000.0)
# Despachos reais
despAtibainha = DBConnection('test', 'Bacias', 'Atibainha', 'Calibracao')
despCachoeira = DBConnection('test', 'Bacias', 'Cachoeira', 'Calibracao')
despAtibainha.D = despAtibainha.D[59:90]
despCachoeira.D = despCachoeira.D[59:90]
vrealAtibainha = trapz(despAtibainha.D, dx = 1) * (86400 / 1000000.0)
vrealCachoeira = trapz(despCachoeira.D, dx = 1) * (86400 / 1000000.0)
print()
print('Volumes:\n'
      'Calculado em Atibainha: %.3f hm3\n'
      'Real em Atibainha: %.3f hm3\n'
      'Calculado em Cachoeira: %.3f hm3\n'
      'Real em Cachoeira: %.3f hm3\n'
      % (volAtibainha, vrealAtibainha, volCachoeira, vrealCachoeira))

# Fim de cronometragem
end = timer()
print('Tempo de execução: %.3f s' % (end - start))
