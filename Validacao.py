import numpy  as np
import pandas as pd
from scipy.optimize import differential_evolution

from Dados.Classes import Bacia, Ponto, Reservatorio
from Metodos.SMAP  import SMAP
from Metodos.Muskingum.Downstream import DownstreamFORK
from Metodos.Muskingum.Upstream   import UpstreamFORK
from Metodos.Otimizacoes import NSE, RMSE, SSQ, KGE


# Inicialização de variáveis de interesse
Atibaia = Bacia(
    AD   = 477,
    Capc =   0.5,
    kkt  =  60.0,
    K = [[75.445, 123.071], [74.383, 127.039]],
    X = [[ 0.254,   0.400], [ 0.226,   0.400]],
    m = [[ 1.206,   1.144], [ 1.240,   1.144]]
)
Valinhos = Bacia(
    AD   = 1074,
    Capc =    0.5,
    kkt  =   60.0,
    K = [104.408, 99.000],
    X = [  0.200,  0.281],
    m = [  1.100,  1.200]
)

# Parâmetros SMAP calibrados durante rodada de 6 anos
paramsAtibaia = {
    'Str' : 1323.256, # 1303.999,
    'k2t' :    3.500, # 3.720,
    'Crec':    0.246  # 0.235
}

paramsValinhos = {
    'Str' : 1619.303, # 1107.297,
    'k2t' :    4.912, # 5.611,
    'Crec':    0.220  # 0.105
}

# Carregamento de dados
def normalize_point(df):
    """
    Função auxiliar para substituir classe
    DBConnection por pandas.DataFrame.
    """
    columns = {'Dia': 't',
               'Precipitacao': 'P',
               'Vazao': 'Q',
               'Captacao': 'C',
               'Evapotranspiracao': 'E'}
    df = df.rename(columns=columns)
    df[['P']] = df[['P']].fillna(0)
    df[['Q']] = df[['Q']].fillna(df[['Q']].mean())
    df['t'] = pd.to_datetime(df['t'], format='%Y-%m-%d')

    df_slice = df.iloc[2193:][:] # Período de 4 anos de validação/previsão

    return Ponto(
        C = df_slice['C'].to_list(),
        E = df_slice['E'].to_list(),
        P = df_slice['P'].to_list(),
        Q = df_slice['Q'].to_list(),
        t = df_slice['t'].to_list()
    )


def normalize_reservoir(df):
    """
    Função auxiliar para substituir classe
    DBConnection por pandas.DataFrame.
    """
    columns = {'Dia': 't',
               'Despacho': 'D'}
    df = df.rename(columns=columns)
    df['D'] = df['D'].replace(0, 0.25)
    df['t'] = pd.to_datetime(df['t'], format='%Y-%m-%d')

    df_slice = df.iloc[2193:][:] # Período de 4 anos de validação/previsão

    return Reservatorio(
        D = df_slice['D'].to_list(),
        t = df_slice['t'].to_list()
    )


# Chuvas, vazões e captações
obsAtibaia  = normalize_point(pd.read_csv('Dados/CSVs/ChuvasEVazoes_A.csv', sep=';'))
obsValinhos = normalize_point(pd.read_csv('Dados/CSVs/ChuvasEVazoes_V.csv', sep=';'))
# Despachos reais
revAtibainha = normalize_reservoir(pd.read_csv('Dados/CSVs/Descargas_A.csv', sep=';'))
revCachoeira = normalize_reservoir(pd.read_csv('Dados/CSVs/Descargas_C.csv', sep=';'))

##################################################
# Parte 1: Cálculo das vazões reais em Atibaia
# Routing dos despachos de Atibainha e Cachoeira
# + Vazão da chuva-vazão em Atibaia - captações
n = len(obsAtibaia.Q)

Q_Atibainha = DownstreamFORK(
    Atibaia.K[0][0],
    Atibaia.X[0][0],
    Atibaia.m[0][0],
    24.0, revAtibainha.D)
Q_Cachoeira = DownstreamFORK(
    Atibaia.K[1][0],
    Atibaia.X[1][0],
    Atibaia.m[1][0],
    24.0, revCachoeira.D)

# Necessário fazer calibração de aquecimento do SMAP para determinar TUin e EBin
# Primeiro vetor incremental (routing)
inc1 = [0] * n
for j in range(n):
    inc1[j] = obsAtibaia.Q[j] - (Q_Atibainha[j] + Q_Cachoeira[j]) + obsAtibaia.C[j]

bounds = [
    [0.0, 0.7],   # TUin
    [0.1, 4.5]    # EBin (vazão mínima do período 02/01/21 - 25/10/24)
]

# Função objetivo
def objective(p):
    # Sujeitos a calibração
    TUin, EBin = p

    # Segundo vetor incremental ("calc")
    inc2 = SMAP(
        paramsAtibaia['Str'],
        paramsAtibaia['k2t'],
        paramsAtibaia['Crec'],
        TUin, EBin, obsAtibaia, Atibaia)

    # Restrição positiva aos routings calculados e às vazões incrementais
    if min(inc2) < 0:
        return np.inf
    else:
        return NSE(inc1, inc2)

# Busca por evolução diferencial
result = differential_evolution(objective, bounds, maxiter=10)

solution = result['x']

chuva_vazao_A = SMAP(
    paramsAtibaia['Str'],
    paramsAtibaia['k2t'],
    paramsAtibaia['Crec'],
    solution[0], solution[1], obsAtibaia, Atibaia)

# Primeiro balanço de vazões
balanco_A = [0] * n
for i in range(n):
    balanco_A[i] = Q_Atibainha[i] + Q_Cachoeira[i] + chuva_vazao_A[i] - obsAtibaia.C[i]

##################################################
# Parte 2: Cálculo das vazões reais em Valinhos
# Routing das vazões calculadas em Atibaia
# + Vazão da chuva-vazão em Valinhos - captações
Q_Atibaia = DownstreamFORK(
    Valinhos.K[0],
    Valinhos.X[0],
    Valinhos.m[0],
    24.0, obsAtibaia.Q)

# Necessário fazer calibração de aquecimento do SMAP para determinar TUin e EBin
# Primeiro vetor incremental (routing)
inc1 = [0] * n
for j in range(n):
    inc1[j] = obsValinhos.Q[j] - Q_Atibaia[j] + obsValinhos.C[j]

bounds = [
    [0.0, 0.7],   # TUin
    [0.1, 7.4]    # EBin (vazão mínima do período 02/01/21 - 25/10/24)
]

# Função objetivo
def objective(p):
    # Sujeitos a calibração
    TUin, EBin = p

    # Segundo vetor incremental ("calc")
    inc2 = SMAP(
        paramsValinhos['Str'],
        paramsValinhos['k2t'],
        paramsValinhos['Crec'],
        TUin, EBin, obsValinhos, Valinhos)

    # Restrição positiva aos routings calculados e às vazões incrementais
    if min(inc2) < 0:
        return np.inf
    else:
        return NSE(inc1, inc2)

# Busca por evolução diferencial
result = differential_evolution(objective, bounds, maxiter=10)

solution = result['x']

chuva_vazao_V = SMAP(
    paramsValinhos['Str'],
    paramsValinhos['k2t'],
    paramsValinhos['Crec'],
    solution[0], solution[1], obsValinhos, Valinhos)

# Segundo balanço de vazões
balanco_V = [0] * n
for i in range(n):
    balanco_V[i] = Q_Atibaia[i] + chuva_vazao_V[i] - obsValinhos.C[i]

print('Vazões calculadas em Atibaia:')
print(f'{pd.DataFrame(balanco_A)} \n')
print('Vazões calculadas em Valinhos:')
print(f'{pd.DataFrame(balanco_V)} \n')

##################################################
# Parte 3: Checagem de calculado VS real com indicadores
print(f'NSE de Atibaia:  {1 - NSE(obsAtibaia.Q , balanco_A)}')
print(f'NSE de Valinhos: {1 - NSE(obsValinhos.Q, balanco_V)}')
print()
print(f'KGE de Atibaia:  {1 - KGE(obsAtibaia.Q , balanco_A)}')
print(f'KGE de Valinhos: {1 - KGE(obsValinhos.Q, balanco_V)}')

pd.DataFrame(balanco_A).to_csv('Scripts/Resultados/validacao_atibaia_sim.csv')
pd.DataFrame(balanco_V).to_csv('Scripts/Resultados/validacao_valinhos_sim.csv')
