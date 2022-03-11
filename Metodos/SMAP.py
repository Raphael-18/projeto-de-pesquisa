def SMAP(Str, k2t, Crec, Dados, Bacia):
    # Input
    n, AD = len(Dados.P), Bacia.AD

    # Inicializacao
    TUin, EBin = 0.0, Bacia.EB
    Q = []

    Ai, Capc, kkt = Bacia.Ai, Bacia.Capc, Bacia.kkt

    # Reservatorios em t = 0
    RSolo = TUin * Str
    RSup = 0.0
    RSub = EBin / (1 - (0.5 ** (1 / kkt))) / AD * 86.4

    for i in range(n):
        # Teor de umidade
        TU = RSolo / Str

        # Escoamento direto
        if Dados.P[i] > Ai:
            ES = ((Dados.P[i] - Ai) ** 2) / (Dados.P[i] - Ai + Str - RSolo)
        else:
            ES = 0.0

        # Evapotranspiracao real
        if (Dados.P[i] - ES) > Dados.EP:
            ER = Dados.EP
        else:
            ER = Dados.P[i] - ES + ((Dados.EP - Dados.P[i] + ES) * TU)

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

        Q.append((ED + EB) * Bacia.AD / 86.4)

    return Q
