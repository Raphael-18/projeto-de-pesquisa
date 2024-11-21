class Bacia:
    """
    Classe para instanciar as sub-bacias de Atibaia e Valinhos
    com valores de AD (área de drenagem), Capc (capacidade de campo)
    e kkt (constante de recessão para o escoamento básico). A abstração
    inicial Ai será adotada como 2.5 mm para ambas.
    """

    def __init__(self, AD, Capc, kkt, K, X, m):
        self.AD = AD
        self.Capc = Capc
        self.kkt = kkt
        self.K = K
        self.X = X
        self.m = m
    Ai = 2.5


class Decisao:
    """
    Classe de decisão diária de despacho após modelagem.
    """

    def __init__(self, Atibainha, Cachoeira):
        self.Atibainha = Atibainha
        self.Cachoeira = Cachoeira


class Ponto:
    """
    Classe para acomodar os dados de um ponto de controle e
    permitir acessar informações de captação C, chuva P ou vazão Q.
    As evapotranspirações potenciais diárias estão prefixadas no banco e serão
    armazenadas em E.
    """

    def __init__(self, C, E, P, Q, t):
        self.C = C
        self.E = E
        self.P = P
        self.Q = Q
        self.t = t


class Reservatorio:
    """
    Classe para acomodar os dados de um reservatório e
    permitir acessar informações de despacho D.
    """

    def __init__(self, D, t):
        self.D = D
        self.t = t


class PrevisaoClass:
    """
    Classe necessária para resgatar matrizes de previsão meteorológica.
    """

    def __init__(self, amostras):
        self.amostras = amostras

    def __str__(self):
        texto = ''
        for amostra in self.amostras:
            texto += str(amostra)
            texto += '\n'
        return texto
