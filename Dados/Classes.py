# Classe para acomodar um tipo de dado (calibracao ou validacao)
# e permitir acessar informacoes de chuva ou vazao.
# As evapotranspiracoes potenciais diarias serao todas tomadas
# como 2.4 mm
class Dado:
    def __init__(self, P, Q):
        self.P  = P
        self.Q  = Q
    EP = 2.4

# Classe para instanciar as sub-bacias de Atibaia e Valinhos
# com valores de AD (area de drenagem), Capc (capacidade de campo) e kkt (constante
# de recessao para o escoamento basico). A abstracao inicial Ai
# sera adotada como 2.5 mm para ambas.
# Por conveniência ao calibrar e aplicar o modelo SMAP, os escoamentos
# basicos iniciais EB foram pre-calculados e serao passados aos objetos
# (7.5899 para Atibaia e 11.1456 para Valinhos)
class Bacia:
    def __init__(self, AD, Capc, EB, kkt):
        self.AD   = AD
        self.Capc = Capc
        self.EB   = EB
        self.kkt  = kkt
    Ai = 2.5
