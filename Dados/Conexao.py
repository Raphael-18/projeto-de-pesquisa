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
# |_ Previsao
#    |_ Dia
#    |_ PrevD1
#    |_ PrevD2
#    |_ PrevD3
#    |_ PrevD4
#    |_ PrevD5
#    |_ PrevD6
#    |_ PrevD7
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

        # Query de previsao retorna dados de chuva previstos em uma janela de sete dias
        # para os quatro primeiros meses de 2021
        else:
            query = "SELECT * FROM " + tipo
            cursor.execute(query)
            # Vetores para armazenar dados lidos
            t  = []
            D1 = []
            D2 = []
            D3 = []
            D4 = []
            D5 = []
            D6 = []
            D7 = []

            for row in cursor.fetchall():
                t.append(row[1])
                D1.append(row[2])
                D2.append(row[3])
                D3.append(row[4])
                D4.append(row[5])
                D5.append(row[6])
                D6.append(row[7])
                D7.append(row[8])

            matrix = [t, D1, D2, D3, D4, D5, D6, D7]

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
