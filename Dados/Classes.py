# Classe para acomodar um tipo de dado (calibracao ou validacao)
# e permitir acessar informacoes de despacho D, chuva P ou vazao Q.
# As evapotranspiracoes potenciais diarias serao todas tomadas
# como 2.4 mm
class Dado:
    def __init__(self, D, P, Q, t):
        self.D  = D
        self.P  = P
        self.Q  = Q
        self.t  = t
    EP = 2.4

# Classe para instanciar as sub-bacias de Atibaia e Valinhos
# com valores de AD (area de drenagem), Capc (capacidade de campo) e kkt (constante
# de recessao para o escoamento basico). A abstracao inicial Ai
# sera adotada como 2.5 mm para ambas.
# Os escoamentos basicos iniciais EB serao adotados como a menor vazao
# observada vezes 0.95
class Bacia:
    def __init__(self, AD, Capc, EB, kkt):
        self.AD   = AD
        self.Capc = Capc
        self.EB   = EB
        self.kkt  = kkt
    Ai = 2.5
