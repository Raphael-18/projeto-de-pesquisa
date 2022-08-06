import mysql.connector
from mysql.connector import errorcode
from Dados.Classes   import *

# Banco de dados (user = test, db = Bacias):
# |_ Atibaia/Valinhos
#    |_ Dia
#    |_ Precipitacao
#    |_ Vazao
#    |_ Captacao
# |_ Atibainha/Cachoeira
#    |_ Dia
#    |_ Despacho
# |_ Prev_(Mar/Abr)_(A/V)
#    |_ Dia
#    |_ Y2016
#    |_ Y2017
#    |_ Y2018
#    |_ Y2019
#    |_ Y2020
def DBConnection(user, database, secao, tipo):
    try:
        connection = mysql.connector.connect(
            user     = user,
            database = database
        )

        cursor = connection.cursor()
        # Query de calibracao retorna captacoes, chuvas, vazoes ou
        # despachos (reservatorios) para os quatro primeiros meses de 2021
        if tipo == 'Calibracao':
            query = "SELECT * FROM " + secao
            cursor.execute(query)

            # Pontos de controle
            if secao == 'Atibaia' or secao == 'Valinhos':
                # Vetores para armazenar dados lidos
                C = []
                P = []
                Q = []
                t = []

                for row in cursor.fetchall():
                    C.append(row[4])
                    P.append(row[2])
                    Q.append(row[3])
                    t.append(row[1])

                # Objeto tipo 'Ponto'
                dados = Ponto(C = C, P = P, Q = Q, t = t)
                return dados
            # Reservatorios
            else:
                # Vetores para armazenar dados lidos
                D = []
                t = []

                for row in cursor.fetchall():
                    D.append(row[2])
                    t.append(row[1])

                # Objeto tipo 'Reservatorio'
                dados = Reservatorio(D = D, t = t)
                return dados

        # Query de previsao retorna amostras de chuvas de marco e abril de 2016 a 2020
        else:
            query = "SELECT * FROM " + tipo + " WHERE Ponto = %s"
            cursor.execute(query, [secao])
            # Vetores para armazenar dados lidos
            t     = []
            Y2016 = []
            Y2017 = []
            Y2018 = []
            Y2019 = []
            Y2020 = []

            for row in cursor.fetchall():
                t.append(row[1])
                Y2016.append(row[2])
                Y2017.append(row[3])
                Y2018.append(row[4])
                Y2019.append(row[5])
                Y2020.append(row[6])

            matrix = [t, Y2016, Y2017, Y2018, Y2019, Y2020]

            previsao = Previsao(amostras = matrix)
            return previsao

    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            print("Something is wrong with your user name or password")
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            print("Database does not exist")
        else:
            print(err)

    finally:
        connection.close()
