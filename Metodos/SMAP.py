# Parametros de calibracao:
#   Str : capacidade de saturacao (mm)
#   k2t : constante de recessao para o escoamento superficial (dias)
#   Crec: recarga subterranea (%)
def SMAP(Str, k2t, Crec, Ponto, Bacia):
    # Input
    # AD: area de drenagem (km2)
    n, AD = len(Ponto.P), Bacia.AD

    # Inicializacao
    # TU: teor de umidade
    # EB: escoamento basico
    TUin, EBin = 0.0, Bacia.EB
    Q = []

    # Ai  : abstracao inicial (mm)
    # Capc: capacidade de campo (%)
    # kkt : constante de recessao para o escoamento basico (dias)
    Ai, Capc, kkt = Bacia.Ai, Bacia.Capc, Bacia.kkt

    # Reservatorios em t = 0
    RSolo = TUin * Str
    RSup = 0.0
    RSub = EBin / (1 - (0.5 ** (1 / kkt))) / AD * 86.4

    for i in range(n):
        # Teor de umidade
        TU = RSolo / Str

        # Escoamento direto
        if Ponto.P[i] > Ai:
            ES = ((Ponto.P[i] - Ai) ** 2) / (Ponto.P[i] - Ai + Str - RSolo)
        else:
            ES = 0.0

        # Evapotranspiracao real
        if (Ponto.P[i] - ES) > Ponto.EP:
            ER = Ponto.EP
        else:
            ER = Ponto.P[i] - ES + ((Ponto.EP - Ponto.P[i] + ES) * TU)

        # Recarga
        if RSolo > (Capc * Str):
            Rec = (Crec / 100.0) * TU * (RSolo - (Capc * Str))
        else:
            Rec = 0.0

        # Atualiza reservatorio-solo
        RSolo += Ponto.P[i] - ES - ER - Rec

        if RSolo > Str:
            ES += RSolo - Str
            RSolo = Str

        RSup += ES
        ED = RSup * (1 - (0.5 ** (1 / k2t)))
        RSup -= ED

        EB = RSub * (1 - (0.5 ** (1 / kkt)))
        RSub += Rec - EB

        Q.append((ED + EB) * Bacia.AD / 86.4)

    return Q
