import mysql.connector
from mysql.connector import errorcode
from Dados.Classes   import *

# Banco de dados (user = test, db = Bacias):
# |_ Tabela WRF
#    |_ Bacia (Atibaia, Valinhos, Atibainha ou Cachoeira)
#    |_ Dia
#    |_ Chuva
#    |_ Vazao
#    |_ Despacho
#    |_ Tipo (Calibracao ou Previsao)
def Store(user, database, bacia, tipo):
    try:
        connection = mysql.connector.connect(
            user = user,
            database = database
        )

        cursor = connection.cursor()
        # Query de calibracao retorna chuvas, vazoes ou despachos para os dois ultimos meses de 2020
        if tipo == 'Calibracao':
            cursor.execute("SELECT * FROM WRF WHERE Bacia = '" + bacia + "' AND Tipo = '" + tipo + "' AND Dia BETWEEN '2020-11-01' AND '2020-12-31'")
        # Query de previsao retorna chuvas para as duas primeiras semanas de janeiro de 2021
        else:
            cursor.execute("SELECT * FROM WRF WHERE Bacia = '" + bacia + "' AND Dia BETWEEN '2021-01-01' AND '2021-01-14'")

        # Vetores para armazenar dados lidos
        # Se a query for de calibracao para as barragens, P e Q retornarao vetores nulos
        # Se a query for de previsao, o banco retornara zeros para as vazoes e despachos
        P = []
        Q = []
        D = []
        t = []

        for row in cursor.fetchall():
            P.append(row[3])
            Q.append(row[4])
            D.append(row[5])
            t.append(row[2])

        # Objeto tipo 'Dado'
        dados = Dado(P = P, Q = Q, D = D, t = t)
        return dados

    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            print("Something is wrong with your user name or password")
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            print("Database does not exist")
        else:
            print(err)

    finally:
        connection.close()
