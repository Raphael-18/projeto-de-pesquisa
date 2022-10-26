# Classe para instanciar as sub-bacias de Atibaia e Valinhos
# com valores de AD (área de drenagem), Capc (capacidade de campo)
# e kkt (constante de recessão para o escoamento básico). A abstração
# inicial Ai será adotada como 2.5 mm para ambas.
class Bacia:
    def __init__(self, AD, Capc, kkt):
        self.AD   = AD
        self.Capc = Capc
        self.kkt  = kkt
    Ai = 2.5

# Classe de decisão diária de despacho após modelagem
class Decisao:
    def __init__(self, Atibainha, Cachoeira):
        self.Atibainha = Atibainha
        self.Cachoeira = Cachoeira

# Classe para acomodar os dados de um ponto de controle e
# permitir acessar informações de captação C, chuva P ou vazão Q.
# As evapotranspirações potenciais diárias serão todas tomadas como 2.4 mm
class Ponto:
    def __init__(self, C, P, Q, t):
        self.C = C
        self.P = P
        self.Q = Q
        self.t = t
    EP = 2.4

# Classe para acomodar os dados de um reservatório e
# permitir acessar informações de despacho D
class Reservatorio:
    def __init__(self, D, t):
        self.D = D
        self.t = t

# Classe necessária para resgatar matrizes de previsão meteorológica
class Previsao:
    def __init__(self, amostras):
        self.amostras = amostras
