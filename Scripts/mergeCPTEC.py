import mysql.connector
from mysql.connector import errorcode
import numpy as np
import pygrib

def MergePCJ(path):
    gribfile = pygrib.open(path)

    selectedBand = gribfile.select(name = 'Precipitation')[0]
    data, lat, long = selectedBand.data()

    # Dados recortados para bacia de interesse
    slice = data[544:556,717:740]

    # Matriz de referência para filtragem
    matrix = np.array([
        [0,0,0,0,0,0,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
        [0,0,0,0,0,0,1,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
        [0,0,0,0,0,1,1,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
        [1,1,0,0,0,1,1,1,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0],
        [0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0,0,0,0,0,0,0,0],
        [0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0,0,0,0,0,0],
        [0,0,0,0,0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0,0,0],
        [0,0,0,0,0,0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0,0,0],
        [0,0,0,0,0,0,0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
        [0,0,0,0,0,0,0,0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0],
        [0,0,0,0,0,0,0,0,0,0,0,1,1,1,1,1,1,1,1,1,1,1,0],
        [0,0,0,0,0,0,0,0,0,0,0,1,1,1,1,1,1,1,1,0,1,0,0]
    ])

    for i in range(len(matrix[:,0])):
        for j in range(len(matrix[0,:])):
            slice[i][j] *= matrix[i][j]

    return np.mean(slice)


url = 'Dados/MERGE/MERGE_CPTEC_2021'
meses = ['01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12']

dias = []
Qobs = []

count = 0
# Loop para acessar o CPTEC e salvar os arquivos .grib2 diários ao longo de 2021
for mes in meses:
    index = int(mes)
    if index <= 7:
        if index % 2 != 0:
            for i in range(31):
                path = url + mes + str(i + 1).zfill(2) + '.grib2'
                dias.append('2021-' + mes + '-' + str(i + 1).zfill(2))
                Qobs.append(MergePCJ(path))
                count = count + 1
                print('%d de 365' % count)
        else:
            if index == 2:
                for i in range(28):
                    path = url + mes + str(i + 1).zfill(2) + '.grib2'
                    dias.append('2021-' + mes + '-' + str(i + 1).zfill(2))
                    Qobs.append(MergePCJ(path))
                    count = count + 1
                    print('%d de 365' % count)
            else:
                for i in range(30):
                    path = url + mes + str(i + 1).zfill(2) + '.grib2'
                    dias.append('2021-' + mes + '-' + str(i + 1).zfill(2))
                    Qobs.append(MergePCJ(path))
                    count = count + 1
                    print('%d de 365' % count)
    else:
        if index % 2 == 0:
            for i in range(31):
                path = url + mes + str(i + 1).zfill(2) + '.grib2'
                dias.append('2021-' + mes + '-' + str(i + 1).zfill(2))
                Qobs.append(MergePCJ(path))
                count = count + 1
                print('%d de 365' % count)
        else:
            for i in range(30):
                path = url + mes + str(i + 1).zfill(2) + '.grib2'
                dias.append('2021-' + mes + '-' + str(i + 1).zfill(2))
                Qobs.append(MergePCJ(path))
                count = count + 1
                print('%d de 365' % count)

for j in range(len(dias)):
    print('%s \t %.5f' % (dias[j], Qobs[j]))

try:
    connection = mysql.connector.connect(
        user = 'test',
        database = 'Bacias'
    )
    print("Conexão estabelecida!")

    cursor = connection.cursor()
    # Query
    for i in range(len(dias)):
        cursor.execute("INSERT INTO QMerge (Dia, Vazao) VALUES ('%s', %s)" % (dias[i], Qobs[i]))

    connection.commit()

except mysql.connector.Error as err:
    if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
        print("Something is wrong with your user name or password")
    elif err.errno == errorcode.ER_BAD_DB_ERROR:
        print("Database does not exist")
    else:
        print(err)

finally:
    cursor.close()
    connection.close()
    print("\nConexão fechada")
