# Parâmetros de calibração:
#   Str : capacidade de saturação (mm)
#   k2t : constante de recessão para o escoamento superficial (dias)
#   Crec: recarga subterrânea (%)
#   TUin: teor de umidade inicial (adimensional)
#   EBin: escoamento básico inicial (m3/s)
def SMAP(Str, k2t, Crec, TUin, EBin, Ponto, Bacia):
    """
    Simulates the Soil Moisture Accounting Procedure (SMAP)
    for hydrological modeling.
    Parameters:
    Str (float): Soil tension storage capacity (mm).
    k2t (float): Recession constant for surface runoff (days).
    Crec (float): Recharge coefficient (%).
    TUin (float): Initial soil moisture content (mm).
    EBin (float): Initial baseflow (mm).
    Ponto (object): Object containing precipitation (P)
    and evapotranspiration (E) data.
    Bacia (object): Object containing basin characteristics
    such as drainage area
    (AD), initial abstraction (Ai), field capacity (Capc), and
    baseflow recession constant (kkt).
    Returns:
    list: Simulated streamflow (Q) for each time step.
    """
    # Input
    # AD: área de drenagem (km2)
    n, AD = len(Ponto.P), Bacia.AD

    # Inicialização
    Q = []

    # Ai  : abstração inicial (mm)
    # Capc: capacidade de campo (%)
    # kkt : constante de recessão para o escoamento básico (dias)
    Ai, Capc, kkt = Bacia.Ai, Bacia.Capc, Bacia.kkt

    # Reservatórios em t = 0
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

        # Evapotranspiração real
        if (Ponto.P[i] - ES) > Ponto.E[i]:
            ER = Ponto.E[i]
        else:
            ER = Ponto.P[i] - ES + ((Ponto.E[i] - Ponto.P[i] + ES) * TU)

        # Recarga
        if RSolo > (Capc * Str):
            Rec = (Crec / 100.0) * TU * (RSolo - (Capc * Str))
        else:
            Rec = 0.0

        # Atualiza reservatório-solo
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
