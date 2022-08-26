import matplotlib.dates  as mdates
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import ticker

def ChuvaVazao(
        obsAtibaia , obsValinhos ,      # Valores observados para plotar pluviogramas de 60 dias          (azul)
        incAtibaia , incValinhos ,      # Incrementos de vazao de eventos chuvosos                        (azul)
        prevAtibaia, prevValinhos,      # Chuvas previstas de 10 dias para complementar os pluviogramas   (laranja)
        calcAtibaia, calcValinhos,      # Vazoes calculadas apos calibracao de modelo chuva-vazao (cinza + laranja)
        objetivo   , step        ,      # Objetivo calibrado de cada rodada e time step para translacao e slice de vetores
        FO                              # Funcao designada para orientar subplot(223)
):
    i = step

    fig = plt.figure(figsize=(10,6))
    # Plot para Atibaia
    ax1 = fig.add_subplot(221)
    # Eixo das precipitacoes
    plt.ylim(0.0, 150.0)
    ax1.bar(obsAtibaia.t[i:i + 60]     , obsAtibaia.P        , color='C0', alpha=0.5) # 60 dias observados (azul)
    ax1.bar(obsAtibaia.t[i + 60:i + 70], prevAtibaia.P[60:70], color='C1', alpha=0.5) # 10 dias previstos  (laranja)
    # Coloca pluviogramas de ponta cabeca
    plt.gca().invert_yaxis()

    # Eixo auxiliar para hidrogramas
    axes2 = ax1.twinx()
    axes2.set_ylim(0.0, 50.0)
    axes2.plot(obsAtibaia.t[i:i + 60],
               incAtibaia)                  # Advem de observacoes, porem com separacao de despachos e captacoes
    axes2.plot(obsAtibaia.t[i:i + 61],
               calcAtibaia[0:61] , 'C7--')  # Recalculo de vazoes durante o periodo de observacao, para checagem
    axes2.plot(obsAtibaia.t[i + 60:i + 70],
               calcAtibaia[60:70], 'C1--')  # Calculado na janela de previsao
    # Formatacao do eixo das abscissas, das datas
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%m/%Y'))
    ax1.xaxis.set_major_locator(mdates.MonthLocator())
    # Titulos dos eixos
    ax1.set_ylabel('Precipitação [mm]')
    axes2.set_ylabel('Vazão [m³/s]')
    # Shift no grafico (p/ cima)
    box = ax1.get_position()
    box.y0 = box.y0 + 0.050
    box.y1 = box.y1 + 0.050
    ax1.set_position(box)

    # Plot para Valinhos
    ax2 = fig.add_subplot(223)
    # Eixo das precipitacoes
    plt.ylim(0.0, 150.0)
    ax2.bar(obsValinhos.t[i:i + 60]     , obsValinhos.P        , color='C0', alpha=0.5)  # 60 dias observados (azul)
    ax2.bar(obsValinhos.t[i + 60:i + 70], prevValinhos.P[60:70], color='C1', alpha=0.5)  # 10 dias previstos  (laranja)
    # Coloca pluviogramas de ponta cabeca
    plt.gca().invert_yaxis()

    # Eixo auxiliar para hidrogramas
    axes3 = ax2.twinx()
    axes3.set_ylim(0.0, 50.0)
    axes3.plot(obsValinhos.t[i:i + 60],
               incValinhos)                 # Advem de observacoes, porem com separacao de despachos e captacoes
    axes3.plot(obsValinhos.t[i:i + 61],
               calcValinhos[0:61] , 'C7--') # Recalculo de vazoes durante o periodo de observacao, para checagem
    axes3.plot(obsValinhos.t[i + 60:i + 70],
               calcValinhos[60:70], 'C1--') # Calculado na janela de previsao
    # Formatacao do eixo das abscissas, das datas
    ax2.xaxis.set_major_formatter(mdates.DateFormatter('%m/%Y'))
    ax2.xaxis.set_major_locator(mdates.MonthLocator())
    # Titulos dos eixos
    ax2.set_ylabel('Precipitação [mm]')
    axes3.set_ylabel('Vazão [m³/s]')
    # Shift no grafico (p/ baixo)
    box = ax2.get_position()
    box.y0 = box.y0 - 0.050
    box.y1 = box.y1 - 0.050
    ax2.set_position(box)

    # Objetivos alcancados
    ax3 = fig.add_subplot(233)
    # Grid
    ax3.grid(b = True, which='major')
    ax3.set_axisbelow(True)
    # Pontos de Atibaia (0,0) e Valinhos (0,1)
    ax3.set_ylim( 0.0,  4.0)
    y = [1, 3]
    x = [objetivo[0][0], objetivo[0][1]]
    # Plot e comparacao com faixa ideal
    ax3.scatter(x, y)
    match FO:
        case 1:
            ax3.set_xlim(-2.0, 2.0)
            ax3.axline((1.0, 0.0), (1.0, 4.0))
            ax3.set_xlabel('Coeficiente de Nash-Sutcliffe')
        case 2:
            ax3.set_xlim(-5.0, 20.0)
            ax3.axline((0.0, 0.0), (0.0, 4.0))
            ax3.set_xlabel('Soma quadrática de diferenças')
        case 3:
            ax3.set_xlim(-1.0, 1.0)
            ax3.axline((0.0, 0.0), (0.0, 4.0))
            ax3.set_xlabel('Erro padrão de vazões inversas')
    # Ajuste do eixo das ordenadas
    positions = [0, 1, 2, 3, 4]
    labels    = ['', 'Atibaia', '', 'Valinhos', '']
    ax3.yaxis.set_major_locator(ticker.FixedLocator(positions))
    ax3.yaxis.set_major_formatter(ticker.FixedFormatter(labels))
    # Shift no grafico (p/ cima)
    box = ax3.get_position()
    box.y0 = box.y0 + 0.050
    box.y1 = box.y1 + 0.050
    ax3.set_position(box)

    # plt.show()
    fileName = str(i) + '.pdf'
    fig.savefig('/Users/raphael/PycharmProjects/projeto-de-pesquisa/Imagens/ChuvaVazao/' + fileName)

def Routings(
        observadoPonto         , revAtibainha            , revCachoeira            ,    # Medicoes
        upstreamValinhosAtibaia, upstreamAtibaiaAtibainha, upstreamAtibaiaCachoeira,    # Routings de medicoes
        step
):
    i = step

    fig = plt.figure(figsize=(10,6))
    # Valinhos - Atibaia
    ax1  = fig.add_subplot(221)

    ax1.plot(observadoPonto.t[i:i + 60], observadoPonto.Q       , 'C0'  ) # Medicoes nos primeiros 60 dias (azul)
    ax1.plot(observadoPonto.t[i:i + 60], upstreamValinhosAtibaia, 'C1--') # Routings apos calibracao       (laranja)

    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%d/%m'))
    ax1.xaxis.set_major_locator(mdates.MonthLocator())
    # Ajuste de escalas
    ax1.set_ylim(-1.0, 60.0)
    ax1.set_ylabel('Vazão [m³/s]')
    # Shift no grafico (p/ cima)
    box = ax1.get_position()
    box.y0 = box.y0 + 0.050
    box.y1 = box.y1 + 0.050
    ax1.set_position(box)

    # Atibaia - Atibainha
    ax2 = fig.add_subplot(223)

    ax2.plot(observadoPonto.t[i:i + 60], revAtibainha.D          , 'C0'  )  # Despachos nos primeiros 60 dias (azul)
    ax2.plot(observadoPonto.t[i:i + 60], upstreamAtibaiaAtibainha, 'C1--')  # Routings apos calibracao        (laranja)

    ax2.xaxis.set_major_formatter(mdates.DateFormatter('%d/%m'))
    ax2.xaxis.set_major_locator(mdates.MonthLocator())
    # Ajuste de escalas
    ax2.set_ylim(-1.0, 8.0)
    ax2.set_ylabel('Vazão [m³/s]')
    # Shift no grafico (p/ baixo)
    box = ax2.get_position()
    box.y0 = box.y0 - 0.050
    box.y1 = box.y1 - 0.050
    ax2.set_position(box)

    # Atibaia - Cachoeira
    ax3 = fig.add_subplot(222)

    ax3.plot(observadoPonto.t[i:i + 60], revCachoeira.D          , 'C0'  )  # Despachos nos primeiros 60 dias (azul)
    ax3.plot(observadoPonto.t[i:i + 60], upstreamAtibaiaCachoeira, 'C1--')  # Routings apos calibracao        (laranja)

    ax3.xaxis.set_major_formatter(mdates.DateFormatter('%d/%m'))
    ax3.xaxis.set_major_locator(mdates.MonthLocator())

    # Ajuste de escalas
    ax3.set_ylim(-1.0, 8.0)
    ax3.set_ylabel('Vazão [m³/s]')
    # Shift no grafico (p/ direita)
    box1 = ax3.get_position()
    box1.x0 = box1.x0 + 0.050
    box1.x1 = box1.x1 + 0.050
    ax3.set_position(box1)
    # Shift no grafico (p/ cima)
    box2 = ax3.get_position()
    box2.y0 = box2.y0 + 0.050
    box2.y1 = box2.y1 + 0.050
    ax3.set_position(box2)

    # plt.show()
    fileName = str(i) + '.pdf'
    fig.savefig('/Users/raphael/PycharmProjects/projeto-de-pesquisa/Imagens/Routings/' + fileName)

def Despachos(observadoPonto1, demanda1, observadoPonto2, demanda2, decisao1, decisao2, resultado, step):
    i = step
    n = 31

    fig = plt.figure(figsize=(10, 6))

    ax1 = fig.add_subplot(211)
    ax1.grid(b=True, which='major')
    ax1.set_axisbelow(True)

    # Routing desde a secao de controle ate a barragem
    ax1.plot(observadoPonto1.t[i:i + 70], decisao1    , 'r'  , alpha = 0.3)
    # Linha de outorga minima
    altura = [demanda1 + np.mean(observadoPonto1.C)] * 70
    ax1.plot(observadoPonto1.t[i:i + 70], altura      , 'r--', alpha = 0.5)
    # Referencia no dia de decisao
    ax1.plot(observadoPonto1.t[i + 60]  , decisao1[60], 'ro' , alpha = 0.7)

    # Routing desde a secao de controle ate a barragem
    ax1.plot(observadoPonto2.t[i:i + 70], decisao2    , 'b'  , alpha = 0.3)
    # Linha de outorga minima
    altura = [demanda2 + np.mean(observadoPonto2.C)] * 70
    ax1.plot(observadoPonto2.t[i:i + 70], altura      , 'b--', alpha = 0.5)
    # Referencia no dia de decisao
    ax1.plot(observadoPonto2.t[i + 60]  , decisao2[60], 'bo' , alpha = 0.7)

    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%d/%m'))
    ax1.xaxis.set_major_locator(mdates.MonthLocator())
    # Ajuste de escalas
    ax1.set_ylim(-20.0, 40.0)
    ax1.set_xlabel('Dias')
    ax1.set_ylabel('Despacho [m³/s]')
    # Shift no grafico (p/ cima)
    box = ax1.get_position()
    box.y0 = box.y0 + 0.030
    box.y1 = box.y1 + 0.030
    ax1.set_position(box)

    # Valor final
    ax2 = fig.add_subplot(212)
    ax2.grid(b=True, which='major')
    ax2.set_axisbelow(True)

    t = range(1, n + 1, 1)

    pontos = [None] * n
    pontos[step] = resultado
    ax2.scatter(t, pontos, color = 'C0', alpha = 0.5)
    # Ajuste de escalas
    ax2.set_xlim( 1.0, 31.0)
    ax2.set_ylim(-1.0, 40.0)
    ax2.set_xlabel('Dias')
    ax2.set_ylabel('Despacho [m³/s]')
    # Shift no grafico (p/ baixo)
    box = ax2.get_position()
    box.y0 = box.y0 - 0.030
    box.y1 = box.y1 - 0.030
    ax2.set_position(box)

    # plt.show()
    fileName = str(i) + '.pdf'
    fig.savefig('/Users/raphael/PycharmProjects/projeto-de-pesquisa/Imagens/Despachos/' + fileName)
