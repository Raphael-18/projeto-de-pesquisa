from scipy.optimize import differential_evolution
import numpy as np

# Classe para acomodar um tipo de dado (calibracao ou validacao)
# e permitir acessar dados de chuva, evapotranspiracao potencial diaria
# ou vazao (observada)
class Dado:
    def __init__(self, P, EP, Qobs):
        self.P    = P
        self.EP   = EP
        self.Qobs = Qobs


# Metodo de leitura de arquivos .txt
def Ler(arquivo):
    file = open(arquivo, "r")
    dado = file.read().splitlines()
    file.close()
    return np.asarray(dado, dtype=float)


# Inicializacao de objeto 'Calibrar' tipo Dado
Calibrar = Dado(Ler("Dados/P.txt"), Ler("Dados/EP.txt"), Ler("Dados/Q.txt"))

def SMAP(Str, k2t, Crec, Dados):
    # Input
    n, AD = len(Dados.P), 109.08

    # Inicializacao
    TUin, EBin = 0.0, min(Dados.Qobs) * 0.95
    Q = []

    Ai, Capc, kkt = 2.5, 0.4, 90.0

    # Reservatorios em t = 0
    RSolo = TUin * Str
    RSup  = 0.0
    RSub  = EBin / (1 - (0.5 ** (1 / kkt))) / AD * 86.4

    for i in range(n):
        # Teor de umidade
        TU = RSolo / Str

        # Escoamento direto
        if Dados.P[i] > Ai:
            ES = ((Dados.P[i] - Ai) ** 2) / (Dados.P[i] - Ai + Str - RSolo)
        else:
            ES = 0.0

        # Evapotranspiracao real
        if (Dados.P[i] - ES) > Dados.EP[i]:
            ER = Dados.EP[i]
        else:
            ER = Dados.P[i] - ES + ((Dados.EP[i] - Dados.P[i] + ES) * TU)

        # Recarga
        if RSolo > (Capc * Str):
            Rec = (Crec / 100.0) * TU * (RSolo - (Capc * Str))
        else:
            Rec = 0.0

        # Atualiza reservatorio-solo
        RSolo += Dados.P[i] - ES - ER - Rec

        if RSolo > Str:
            ES += RSolo - Str
            RSolo = Str

        RSup += ES
        ED = RSup * (1 - (0.5 ** (1 / k2t)))
        RSup -= ED

        EB = RSub * (1 - (0.5 ** (1 / kkt)))
        RSub += Rec - EB

        Q.append((ED + EB) * AD / 86.4)

    return Q


# Objective function
def objective(p):
    Str, k2t, Crec = p

    Q = SMAP(Str, k2t, Crec, Calibrar)

    sum = 0
    for i in range(len(Q)):
        sum += ((Calibrar.Qobs[i] - Q[i]) / Calibrar.Qobs[i]) ** 2

    return sum


# Bounds on the search
bounds = [[100.0, 2000.0], [0.2, 10.0], [0.0, 20.0]]

# Differential Evolution search
result = differential_evolution(objective, bounds)

# Summarize the result
print('Status : %s' % result['message'])
print('Total Evaluations: %d' % result['nfev'])

# Evaluate solution
solution = result['x']
evaluation = objective(solution)
print('Solution: f([%.3f \t %.3f \t %.3f]) = %.3f' % (solution[0], solution[1], solution[2], evaluation))

Qcalc = SMAP(solution[0], solution[1], solution[2], Calibrar)

# Coeficiente de eficiencia de Nash-Sutcliffe
def NSE(Qobs, Q):
    a = 0
    b = 0
    Qm = np.mean(Qobs)
    for i in range(len(Qobs)):
        a += (Qobs[i] - Q[i]) ** 2
        b += (Qobs[i] - Qm) ** 2

    return 1 - (a / b)


print('Nash-Sutcliffe: %.3f' % NSE(Calibrar.Qobs, Qcalc))

print()
print('Qcalc \t Qobs')
for j in range(len(Qcalc)):
    print('%.3f \t %.3f' % (Qcalc[j], Calibrar.Qobs[j]))
