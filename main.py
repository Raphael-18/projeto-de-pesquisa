import os
import configparser

import numpy as np
import pandas as pd
from timeit import default_timer as timer
from tqdm import tqdm

from Dados.Classes import Bacia, Ponto
from Scripts.Modelo.Calibracao import Calibracao
from Scripts.Modelo.Previsao import Previsao

config = configparser.ConfigParser()
config.read('config.ini')

start = timer()

# region Inicialização de variáveis de interesse
Atibaia = Bacia(
    AD = 477,
    Capc = 0.5,
    kkt = 60.0,
    K = [[75.445, 123.071], [74.383, 127.039]],
    X = [[0.254, 0.400], [0.226, 0.400]],
    m = [[1.206, 1.144], [1.240, 1.144]]
)
Valinhos = Bacia(
    AD = 1074,
    Capc = 0.5,
    kkt = 60.0,
    K = [104.408, 99.000],
    X = [0.200, 0.281],
    m = [1.100, 1.200]
)

FO = int(config['ObjectiveFunction']['FO'])

simulacao_dict = {
    1: 'Previsoes',
    2: 'Observacoes'
}

flag = int(config['Simulation']['simulation_flag'])
simulacao = simulacao_dict.get(flag, 'Unknown')

# endregion Inicialização de variáveis de interesse

# region Calibração de variáveis hidrológicas e de routing
# Pontos de controle

def normalize_point(df) -> pd.DataFrame:
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

    df_slice = df.head(732) # Primeiros 2 anos da calibração

    return df_slice


def normalize_reservoir(df) -> pd.DataFrame:
    """
    Função auxiliar para substituir classe
    DBConnection por pandas.DataFrame.
    """
    columns = {'Dia': 't',
               'Despacho': 'D'}
    df = df.rename(columns=columns)
    df['D'] = df['D'].replace(0, 0.25)
    df['t'] = pd.to_datetime(df['t'], format='%Y-%m-%d')

    df_slice = df.head(732) # Primeiros 2 anos da calibração

    return df_slice


def normalize_forecast(path):
    df = pd.read_csv(path, sep=';')
    df['Dia'] = pd.to_datetime(df['Dia'], format='%Y-%m-%d')

    matrix = [df[col].tolist() for col in df.columns]

    previsao = Previsao(amostras=matrix)
    return previsao


obsAtibaia = pd.read_csv('Dados/CSVs/ChuvasEVazoes_A.csv', sep=';')
obsValinhos = pd.read_csv('Dados/CSVs/ChuvasEVazoes_V.csv', sep=';')
obsAtibaia = normalize_point(obsAtibaia)
obsValinhos = normalize_point(obsValinhos)
# Reservatórios
revAtibainha = pd.read_csv('Dados/CSVs/Descargas_A.csv', sep=';')
revCachoeira = pd.read_csv('Dados/CSVs/Descargas_C.csv', sep=';')
revAtibainha = normalize_reservoir(revAtibainha)
revCachoeira = normalize_reservoir(revCachoeira)

paramsAtibaia, paramsValinhos, resultados = Calibracao(
    obsAtibaia, obsValinhos,
    revAtibainha, revCachoeira,
    Atibaia, Valinhos,
    FO=FO
)
resultados.to_excel(
    os.path.join(config['ExportDirectory']['results'], 'Calibracao.xlsx'))
print(resultados)

# endregion Calibração de variáveis hidrológicas e de routing
"""
# region Loop do método
# ETAPA 3:
# Loop para executar o modelo, fazendo slices em vetores de calibração,
# para caminhar de 30 em 30 dias e escolhendo a cada iteração valores
# de previsão de chuva de 7 dias

# Dias a serem simulados
n = int(config['Simulation']['simulation_days'])
# Respostas
despachos = {'Atibainha': [], 'Cachoeira': []}
atendimentos = {'Atibaia': [], 'Valinhos': []}
# Dicionários para armazenamento de parâmetros após calibração
startA = {'TUin': [], 'EBin': []}
startV = {'TUin': [], 'EBin': []}

# Loop para invocar o modelo e extrair uma decisão de cada dia
for j in tqdm(range(n), desc="Previsão"):
    # Necessário conectar ao banco de dados a cada iteração para que
    # ao fazer os slices não haja p'erda de informação (recorte em
    # vetores modificados e não em vetores originais)
    i = j  # + 29
    # 3.1. OBSERVAÇÃO
    # Pontos de controle (dados observados)
    dadosAtibaia = obsAtibaia.copy()
    dadosValinhos = obsValinhos.copy()
    # Assinatura nos objetos a serem passados ao método de previsão
    obsAtibaia.C = dadosAtibaia.C
    obsAtibaia.E = dadosAtibaia.E
    obsAtibaia.P = dadosAtibaia.P
    obsValinhos.C = dadosValinhos.C
    obsValinhos.E = dadosValinhos.E
    obsValinhos.P = dadosValinhos.P
    # Slices nos pontos de controle
    obsAtibaia.C = obsAtibaia.C[i:i + 37]
    obsAtibaia.E = obsAtibaia.E[i:i + 37]
    obsAtibaia.P = obsAtibaia.P[i:i + 37]
    obsValinhos.C = obsValinhos.C[i:i + 37]
    obsValinhos.E = obsValinhos.E[i:i + 37]
    obsValinhos.P = obsValinhos.P[i:i + 37]

    if j == 0:
        # Slices nos pontos
        obsAtibaia.Q = obsAtibaia.Q[i:i + 30]
        obsValinhos.Q = obsValinhos.Q[i:i + 30]
        # Slices nos reservatorios
        revAtibainha.D = revAtibainha.D[i:i + 30]
        revCachoeira.D = revCachoeira.D[i:i + 30]

    # 3.2. PREVISÃO
    # Atibaia
    previsaoA = normalize_forecast('Dados/CSVs/SIMEPAR_Atibaia.csv')

    # Slices nas previsões
    previsaoA.amostras[1] = previsaoA.amostras[1][i + 30]
    previsaoA.amostras[2] = previsaoA.amostras[2][i + 30]
    previsaoA.amostras[3] = previsaoA.amostras[3][i + 30]
    previsaoA.amostras[4] = previsaoA.amostras[4][i + 30]
    previsaoA.amostras[5] = previsaoA.amostras[5][i + 30]
    previsaoA.amostras[6] = previsaoA.amostras[6][i + 30]
    previsaoA.amostras[7] = previsaoA.amostras[7][i + 30]
    # Vetores de 7 dias de previsão
    prevAtibaia = Ponto(C=[], E=[], P=[], Q=[], t=[])
    for k in range(7):
        prevAtibaia.P.append(previsaoA.amostras[k + 1])
    # Valinhos
    previsaoV = normalize_forecast('Dados/CSVs/SIMEPAR_Valinhos.csv')
    # Slices nas previsões
    previsaoV.amostras[1] = previsaoV.amostras[1][i + 30]
    previsaoV.amostras[2] = previsaoV.amostras[2][i + 30]
    previsaoV.amostras[3] = previsaoV.amostras[3][i + 30]
    previsaoV.amostras[4] = previsaoV.amostras[4][i + 30]
    previsaoV.amostras[5] = previsaoV.amostras[5][i + 30]
    previsaoV.amostras[6] = previsaoV.amostras[6][i + 30]
    previsaoV.amostras[7] = previsaoV.amostras[7][i + 30]
    # Vetores de 7 dias de previsão
    prevValinhos = Ponto(C=[], E=[], P=[], Q=[], t=[])
    for k in range(7):
        prevValinhos.P.append(previsaoV.amostras[k + 1])

    # 3.3 INVOCAÇÃO DO MODELO
    checkAtibaia, checkValinhos, resultado = Previsao(
        obsAtibaia, obsValinhos,
        prevAtibaia, prevValinhos,
        paramsAtibaia, paramsValinhos,
        revAtibainha, revCachoeira,
        startA, startV,
        Atibaia, Valinhos,
        FO=FO, step=j + 1
    )

    despachos['Atibainha'] += [resultado.Atibainha]
    despachos['Cachoeira'] += [resultado.Cachoeira]

    atendimentos['Atibaia'] += [checkAtibaia]
    atendimentos['Valinhos'] += [checkValinhos]

pd.DataFrame(data=despachos).to_excel(
    os.path.join(config['ExportDirectory']['results'], 'Despachos.xlsx'))
pd.DataFrame(data=atendimentos).to_excel(
    os.path.join(config['ExportDirectory']['results'], 'Atendimentos.xlsx'))

print('\nDespachos')
print(pd.DataFrame(data=despachos))
print('\nAtendimentos')
print(pd.DataFrame(data=atendimentos))

# Volumes descarregados
unit_factor = 86400 / 1_000_000.0
volAtibainha = np.trapz(despachos['Atibainha'], dx=1) * unit_factor
volCachoeira = np.trapz(despachos['Cachoeira'], dx=1) * unit_factor
# Despachos reais
despAtibainha = normalize_reservoir(pd.read_csv('Dados/CSVs/Descargas_A.csv', sep=';'))
despCachoeira = normalize_reservoir(pd.read_csv('Dados/CSVs/Descargas_C.csv', sep=';'))

despAtibainha.D = despAtibainha.D[2194:3587]
despCachoeira.D = despCachoeira.D[2194:3587]
vrealAtibainha = np.trapz(despAtibainha.D, dx=1) * unit_factor
vrealCachoeira = np.trapz(despCachoeira.D, dx=1) * unit_factor

print(
    '\n'
    'Volumes:\n'
    f'Calculado em Atibainha: {volAtibainha:.3f} hm3\n'
    f'Real em Atibainha: {vrealAtibainha:.3f} hm3\n'
    f'Calculado em Cachoeira: {volCachoeira:.3f} hm3\n'
    f'Real em Cachoeira: {vrealCachoeira:.3f} hm3\n'
)
"""
end = timer()
print(f'Tempo de execução: {end - start:.3f} s')

# endregion Loop do método
