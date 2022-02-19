import mysql.connector
from mysql.connector import errorcode

# Classe para acomodar um tipo de dado (calibracao ou validacao)
# e permitir acessar dados de chuva, evapotranspiracao potencial diaria
# ou vazao (observada)
class Dado:
    def __init__(self, P, EP, Qobs):
        self.P    = P
        self.EP   = EP
        self.Qobs = Qobs


# Estrutura do banco (user = test, db = Bacias):
# |_ Tabela 1: Areas      (Bacia + Area)
# |_ Tabela 2: Biritiba   (Dia + Evapotranspiracao + Precipitacao + Vazao)
# |_ Tabela 3: Jundiai    (Dia + Evapotranspiracao + Precipitacao + Vazao)
# |_ Tabela 4: Paraitinga (Dia + Evapotranspiracao + Precipitacao + Vazao)
# |_ Tabela 5: PonteNova  (Dia + Evapotranspiracao + Precipitacao + Vazao)
# |_ Tabela 6: Taiacupeba (Dia + Evapotranspiracao + Precipitacao + Vazao)
def StoreFromDb(user, database, bacia):
    try:
        connection = mysql.connector.connect(
            user = user,
            database = database
        )
        print("Conexão estabelecida!\n")

        cursor = connection.cursor()
        # Query
        cursor.execute("SELECT * FROM " + bacia)

        # Vetores para armazenar dados lidos
        E = []
        P = []
        Q = []

        for row in cursor.fetchall():
            E.append(row[2])
            P.append(row[3])
            Q.append(row[4])

        # Objeto tipo 'Dado'
        dados = Dado(P = P, EP = E, Qobs = Q)

        for i in range(len(dados.P)):
            print('%.3f \t %.3f \t %.3f' % (dados.P[i], dados.EP[i], dados.Qobs[i]))

    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            print("Something is wrong with your user name or password")
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            print("Database does not exist")
        else:
            print(err)

    finally:
        connection.close()
        print("\nConexão fechada")


StoreFromDb("test", "Bacias", "Biritiba")
