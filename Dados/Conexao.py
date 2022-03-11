import mysql.connector
from mysql.connector import errorcode
from Classes import *


# Banco de dados (user = test, db = Bacias):
# |_ Tabela WRF
#    |_ Bacia (Atibaia ou Valinhos)
#    |_ Dia
#    |_ Chuva
#    |_ Tipo (Calibracao ou Previsao)
def Store(user, database, bacia, tipo):
    try:
        connection = mysql.connector.connect(
            user = user,
            database = database
        )

        cursor = connection.cursor()
        # Query
        if tipo == 'Calibração':
            cursor.execute("SELECT * FROM WRF WHERE Bacia = '" + bacia + "' AND Tipo = '" + tipo + "'")
        else:
            cursor.execute("SELECT * FROM WRF WHERE Bacia = '" + bacia + "' AND Dia BETWEEN '2021-01-01' AND '2021-01-14'")

        # Vetores para armazenar dados lidos
        # Se a query for de previsao, o banco retornara null para as vazoes
        P = []
        Q = []

        for row in cursor.fetchall():
            P.append(row[3])
            Q.append(row[4])

        # Objeto tipo 'Dado'
        dados = Dado(P = P, Q = Q)
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
