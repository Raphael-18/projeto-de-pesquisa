# O routing de montante para jusante
# recebe um hidrograma de montante (upstream)
def DownstreamRouting(upstream, K, x, T):
    # Coeficientes
    C0 = (T - (2 * K * x)) / ((2 * K * (1 - x)) + T)
    C1 = (T + (2 * K * x)) / ((2 * K * (1 - x)) + T)
    C2 = ((2 * K * (1 - x)) - T) / ((2 * K * (1 - x)) + T)

    n = len(upstream)
    downstream = [0] * n
    # Valor inicial de jusante é igual ao de montante
    downstream[0] = upstream[0]
    # Loop entre segunda e ultima entradas
    for i in range(1, n):
        downstream[i] = C0 * upstream[i] + C1 * upstream[i - 1] + C2 * downstream[i - 1]

    return downstream

sample = [274.000, 314.000, 355.000, 404.000, 495.000, 566.000, 586.000, 572.000, 575.000, 572.000, 571.000,
          676.000,1026.000,1156.000,1081.000,1001.000, 816.000, 681.000, 568.000, 538.000, 534.000, 535.000,
          551.000, 555.000, 549.000, 544.000, 493.000, 428.000, 376.000, 357.000, 301.000, 274.000, 271.000]

answer = [274.000, 259.342, 271.476, 295.022, 315.825, 378.837, 464.508, 530.007, 549.774, 563.408, 568.044,
          531.034, 474.806, 701.052, 954.597,1046.723,1091.798,1004.228, 885.028, 738.492, 640.335, 587.131,
          555.364, 551.730, 555.553, 554.129, 567.786, 554.445, 510.671, 450.716, 424.671, 373.114, 324.964]

resultado = DownstreamRouting(sample, 66.0, 0.45, 24.0)

print("Resultados:")
for i in range(len(resultado)):
    print('%.3f \t %.3f' % (resultado[i], answer[i]))
