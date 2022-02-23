from urllib import request

# Método para download de arquivos
def Download(url):
    with request.urlopen(url) as response:
        data = response.read()
        name = url[62:]
        with open('/Users/raphael/PycharmProjects/projeto-de-pesquisa/Dados/MERGE/' + name, 'wb') as file:
            file.write(data)

url = 'http://ftp.cptec.inpe.br/modelos/tempo/MERGE/GPM/DAILY/2021/'
meses = ['01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12']

# Loop para acessar o CPTEC e salvar os arquivos .grib2 diários ao longo de 2021
for mes in meses:
    index = int(mes)
    if index <= 7:
        if index % 2 != 0:
            for i in range(31):
                path = url + mes + '/' + 'MERGE_CPTEC_2021' + mes + str(i + 1).zfill(2) + '.grib2'
                Download(path)
        else:
            if index == 2:
                for i in range(28):
                    path = url + mes + '/' + 'MERGE_CPTEC_2021' + mes + str(i + 1).zfill(2) + '.grib2'
                    Download(path)
            else:
                for i in range(30):
                    path = url + mes + '/' + 'MERGE_CPTEC_2021' + mes + str(i + 1).zfill(2) + '.grib2'
                    Download(path)
    else:
        if index % 2 == 0:
            for i in range(31):
                path = url + mes + '/' + 'MERGE_CPTEC_2021' + mes + str(i + 1).zfill(2) + '.grib2'
                Download(path)
        else:
            for i in range(30):
                path = url + mes + '/' + 'MERGE_CPTEC_2021' + mes + str(i + 1).zfill(2) + '.grib2'
                Download(path)
