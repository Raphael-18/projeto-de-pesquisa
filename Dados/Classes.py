# Classe para instanciar as sub-bacias de Atibaia e Valinhos
# com valores de AD (area de drenagem), Capc (capacidade de campo)
# e kkt (constante de recessao para o escoamento basico). A abstracao
# inicial Ai sera adotada como 2.5 mm para ambas. Os escoamentos
# basicos iniciais EB serao adotados como a menor vazao observada vezes 0.95
class Bacia:
    def __init__(self, AD, Capc, EB, kkt):
        self.AD   = AD
        self.Capc = Capc
        self.EB   = EB
        self.kkt  = kkt
    Ai = 2.5

# Classe de decisao diaria de despacho apos modelagem
class Decisao:
    def __init__(self, Atibainha, Cachoeira):
        self.Atibainha = Atibainha
        self.Cachoeira = Cachoeira

# Classe para acomodar os dados de um ponto de controle e
# permitir acessar informacoes de captacao C, chuva P ou vazao Q.
# As evapotranspiracoes potenciais diarias serao todas tomadas como 2.4 mm
class Ponto:
    def __init__(self, C, P, Q, t):
        self.C = C
        self.P = P
        self.Q = Q
        self.t = t
    EP = 2.4

# Classe para acomodar os dados de um reservatorio e
# permitir acessar informacoes de despacho D
class Reservatorio:
    def __init__(self, D, t):
        self.D = D
        self.t = t

# Classe necessaria para resgatar matrizes de observacoes amostrais, cujas
# informacoes serao escolhidas aleatoriamente para compor uma janela de previsao
class Previsao:
    def __init__(self, amostras):
        self.amostras = amostras
