import requests
import json
from datetime import date
import pandas as pd



class nike_crawler:
    array_anchors = []
    full_product_list = []
    errors = []
    total_pages = 0
    total_products = 0
    date_today = ''
    state_pages=[]
    base_url = 'https://api.nike.com/cic/browse/v1?queryid=products&anonymousId=199C86923837F9429AB85910D6EC7B97&country=mx&endpoint=%2Fproduct_feed%2Frollup_threads%2Fv2%3Ffilter%3Dmarketplace(MX)%26filter%3Dlanguage(es-419)%26filter%3DemployeePrice(true)%26filter%3DattributeIds(0f64ecc7-d624-4e91-b171-b83a03dd8550%2C16633190-45e5-4830-a068-232ac7aea82c)%26anchor%3D24%26consumerChannelId%3Dd9a5bc42-4b9c-4976-858a-f159cf99c647%26count%3D24&language=es-419&localizedRangeStr=%7BlowestPrice%7D%20%E2%80%94%20%7BhighestPrice%7D'


    def obtain_pre_info(self):
        self.date_today = str(date.today())

        try:
            base_request = requests.get(self.base_url)
            base_json = base_request.json()
             #vemos todas los productos disponibles
            self.total_products = base_json.get('data')['products']['pages']['totalResources']

            #vemos todas las paginas disponibles
            self.total_pages = base_json.get('data')['products']['pages']['totalPages']

            last_product = self.total_pages * 24
            self.array_anchors = list(range(0, last_product,24))

        except:
            print('No se pudo acceder al url')
            self.errors.append(1)


    def obtain_save_data(self):
        #llamamos la funcion de llenado de informacio basica para la clase
        self.obtain_pre_info()

        assert len(self.errors) == 0
        #assert len(self.array_anchors) > 5
        for anchor in self.array_anchors:
            try:
                base_page = 'https://api.nike.com/cic/browse/v1?queryid=products&anonymousId=199C86923837F9429AB85910D6EC7B97&country=mx&endpoint=%2Fproduct_feed%2Frollup_threads%2Fv2%3Ffilter%3Dmarketplace(MX)%26filter%3Dlanguage(es-419)%26filter%3DemployeePrice(true)%26filter%3DattributeIds(0f64ecc7-d624-4e91-b171-b83a03dd8550%2C16633190-45e5-4830-a068-232ac7aea82c)%26anchor%3D{}%26consumerChannelId%3Dd9a5bc42-4b9c-4976-858a-f159cf99c647%26count%3D24&language=es-419&localizedRangeStr=%7BlowestPrice%7D%20%E2%80%94%20%7BhighestPrice%7D'.format(anchor)

                base_request = requests.get(base_page)
                self.full_product_list = self.full_product_list + base_request.json()['data']['products']['products']
                self.state_pages.append('OK')
            except:
                print('No se pudo acceder al url')
                self.errors.append(1)
                self.state_pages.append('ERROR')

        assert len(self.errors) == 0
        assert self.date_today != ''

        #guardamos todos los datos
        with open('data/%s.json'%self.date_today, 'w', encoding='utf-8') as f:
            json.dump(self.full_product_list, f, ensure_ascii=False, indent=4)

        #Imprimimos el verbose
        print(self.verbose())




    def verbose(self):
        text= 'STATUS: ' + self.date_today+'\n'
        #print('STATUS:',self.date_today )
        for indx, element in enumerate(self.state_pages):
            #print(self.array_anchors[indx],element)
            text+=str(self.array_anchors[indx]) + ' ---> '+ str(element) + '\n'
        #print('Expected pages: ', self.total_pages)
        text += 'Expected pages: '+ str(self.total_pages) + '\n'
        #print('Expected products: ',self.total_products)
        text += 'Expected products: '+ str(self.total_products) + '\n'
        #print('==============================')
        text += '=============================='+'\n'
        #print('Collected products: ',len(self.full_product_list))
        text += 'Collected products: '+ str(len(self.full_product_list)) + '\n'
        return text



class ReportTM:
    #Funcion para generar un dataframe dado el nombre del archivo Json
    def generate_DF(self,name_file):
        with open('data/'+name_file, encoding='utf-8') as fh:
            data = json.load(fh)

        price_date_name = 'currentPrice_'+str(name_file[:-5])
        Data_products = {
            "id" : [],
            'colorDescription' : [],
            'portrait_url' : [],
            'squarishURL' : [],
            'Stock' : [],
            'isNew' : [],
            price_date_name : [],
            'fullPrice' : [],
            'subtitle' : [],
            'title' : [],
            'date':[]
        }

        for product in data:
            Data_products['id'].append(product['id'])
            Data_products['colorDescription'].append(product['colorDescription'])
            Data_products['portrait_url'].append(product['images']['portraitURL'])
            Data_products['squarishURL'].append(product['images']['squarishURL'])
            Data_products['Stock'].append(product['inStock'])
            Data_products['isNew'].append(product['colorways'][0]['isNew'])
            Data_products[price_date_name].append(product['price']['currentPrice'])
            Data_products['fullPrice'].append(product['price']['fullPrice'])
            Data_products['subtitle'].append(product['subtitle'])
            Data_products['title'].append(product['title'])
            Data_products['date'].append(name_file[:-5])

        return pd.DataFrame(Data_products)
    #Funcion para generar la serie de tiempo, de los archivos JSON indicados, en ORDEN
    def generate_time_serie(self,*files):
        array_dataframes =[]
        for file in files:
            with open('data/'+file, encoding='utf-8') as fh:
                data = json.load(fh)

            price_date_name = file[:-5]
            Data_products = {
                "id" : [],
                price_date_name : []

            }

            for product in data:
                Data_products['id'].append(product['id'])
                Data_products[price_date_name].append(product['price']['currentPrice'])
            array_dataframes.append(pd.DataFrame(Data_products))

        # merge a la lista de dataframes

        df_final = reduce(lambda left,right: pd.merge(left,right,on='id', how='outer'), array_dataframes)

        return df_final
    #funcion para checar si existe un cambio de precion entre un dia, y su dia anterior
    #NOTA:
    #Solo se ingresa la fecha del dia despues, el dia anterior lo se obtiene dentro de la funcion
    def check_changes_2days(self, day):

        #obtenemos el dia anterior a la fecha dada
        date = datetime.strptime(day, "%Y-%m-%d")
        modified_date = date - timedelta(days=1)
        prev_day = datetime.strftime(modified_date, "%Y-%m-%d")

        day_file = day +'.json'
        prev_day_file = prev_day+'.json'
                #comprobamos que existan archivos para los dos dias

        if os.path.isfile('data/'+day_file) and os.path.isfile('data/'+prev_day_file) :
            df_time = self.generate_time_serie(prev_day_file,day_file)
            df_time['change'] = df_time[prev_day_file[:-5]] - df_time[day_file[:-5]]
            return df_time.loc[df_time['change']>0].sort_values(by = 'change',ascending = False)
            #
        else:
            raise ValueError(
                    "Nombres de archivo no validos. "
                        f"Archivos: {prev_day_file,day_file}"
                    )





class nike_crawler_Liquidacion:
    array_anchors = []
    full_product_list = []
    errors = []
    total_pages = 0
    total_products = 0
    date_today = ''
    state_pages=[]
    base_url = 'https://api.nike.com/cic/browse/v1?queryid=products&anonymousId=DE9CEB2891D6D710B49C8CABEDC222DC&country=mx&endpoint=%2Fproduct_feed%2Frollup_threads%2Fv2%3Ffilter%3Dmarketplace(MX)%26filter%3Dlanguage(es-419)%26filter%3DemployeePrice(true)%26filter%3DattributeIds(0f64ecc7-d624-4e91-b171-b83a03dd8550%2C16633190-45e5-4830-a068-232ac7aea82c%2C5b21a62a-0503-400c-8336-3ccfbff2a684)%26anchor%3D0%26consumerChannelId%3Dd9a5bc42-4b9c-4976-858a-f159cf99c647%26count%3D24&language=es-419&localizedRangeStr=%7BlowestPrice%7D%20%E2%80%94%20%7BhighestPrice%7D'


    def obtain_pre_info(self):
        self.date_today = str(date.today())

        try:
            base_request = requests.get(self.base_url)
            base_json = base_request.json()
             #vemos todas los productos disponibles
            self.total_products = base_json.get('data')['products']['pages']['totalResources']

            #vemos todas las paginas disponibles
            self.total_pages = base_json.get('data')['products']['pages']['totalPages']

            last_product = self.total_pages * 24
            self.array_anchors = list(range(0, last_product,24))

        except:
            print('No se pudo acceder al url')
            self.errors.append(1)


    def obtain_save_data(self):
        #llamamos la funcion de llenado de informacio basica para la clase
        self.obtain_pre_info()

        assert len(self.errors) == 0
        #assert len(self.array_anchors) > 5
        for anchor in self.array_anchors:
            try:
                base_page = 'https://api.nike.com/cic/browse/v1?queryid=products&anonymousId=DE9CEB2891D6D710B49C8CABEDC222DC&country=mx&endpoint=%2Fproduct_feed%2Frollup_threads%2Fv2%3Ffilter%3Dmarketplace(MX)%26filter%3Dlanguage(es-419)%26filter%3DemployeePrice(true)%26filter%3DattributeIds(0f64ecc7-d624-4e91-b171-b83a03dd8550%2C16633190-45e5-4830-a068-232ac7aea82c%2C5b21a62a-0503-400c-8336-3ccfbff2a684)%26anchor%3D{}%26consumerChannelId%3Dd9a5bc42-4b9c-4976-858a-f159cf99c647%26count%3D24&language=es-419&localizedRangeStr=%7BlowestPrice%7D%20%E2%80%94%20%7BhighestPrice%7D'.format(anchor)

                base_request = requests.get(base_page)
                self.full_product_list = self.full_product_list + base_request.json()['data']['products']['products']
                self.state_pages.append('OK')
            except:
                print('No se pudo acceder al url')
                self.errors.append(1)
                self.state_pages.append('ERROR')

        assert len(self.errors) == 0
        assert self.date_today != ''

        #guardamos todos los datos
        with open('data/Liquidacion/%s.json'%self.date_today, 'w', encoding='utf-8') as f:
            json.dump(self.full_product_list, f, ensure_ascii=False, indent=4)

        #Imprimimos el verbose
        print(self.verbose())

    def verbose(self):
        text = '--------Seccion Liquidacion---------'+'\n'
        text+= 'STATUS: ' + self.date_today+'\n'
        #print('STATUS:',self.date_today )
        for indx, element in enumerate(self.state_pages):
            #print(self.array_anchors[indx],element)
            text+=str(self.array_anchors[indx]) + ' ---> '+ str(element) + '\n'
        #print('Expected pages: ', self.total_pages)
        text += 'Expected pages: '+ str(self.total_pages) + '\n'
        #print('Expected products: ',self.total_products)
        text += 'Expected products: '+ str(self.total_products) + '\n'
        #print('==============================')
        text += '=============================='+'\n'
        #print('Collected products: ',len(self.full_product_list))
        text += 'Collected products: '+ str(len(self.full_product_list)) + '\n'
        return text

class ReportTM_LIQ(ReportTM):
    def __init__(self,path):
        self.path = path

    def generate_DF(self,name_file):
        with open(self.path+name_file, encoding='utf-8') as fh:
            data = json.load(fh)

        price_date_name = 'currentPrice_'+str(name_file[:-5])
        Data_products = {
            "id" : [],
            'colorDescription' : [],
            'portrait_url' : [],
            'squarishURL' : [],
            'Stock' : [],
            'isNew' : [],
            price_date_name : [],
            'fullPrice' : [],
            'subtitle' : [],
            'title' : [],
            'date':[],
            'url':[]
        }

        for product in data:
            Data_products['id'].append(product['id'])
            Data_products['colorDescription'].append(product['colorDescription'])
            Data_products['portrait_url'].append(product['images']['portraitURL'])
            Data_products['squarishURL'].append(product['images']['squarishURL'])
            Data_products['Stock'].append(product['inStock'])
            Data_products['isNew'].append(product['colorways'][0]['isNew'])
            Data_products[price_date_name].append(product['price']['currentPrice'])
            Data_products['fullPrice'].append(product['price']['fullPrice'])
            Data_products['subtitle'].append(product['subtitle'])
            Data_products['title'].append(product['title'])
            Data_products['date'].append(name_file[:-5])
            Data_products['url'].append(product['url'])

        return pd.DataFrame(Data_products)
'''
class ReportTM_LIQ:

    def generate_DF(self,name_file):
        with open('data/liquidacion/'+name_file, encoding='utf-8') as fh:
            data = json.load(fh)

        price_date_name = 'currentPrice_'+str(name_file[:-5])
        Data_products = {
            "id" : [],
            'colorDescription' : [],
            'portrait_url' : [],
            'squarishURL' : [],
            'Stock' : [],
            'isNew' : [],
            price_date_name : [],
            'fullPrice' : [],
            'subtitle' : [],
            'title' : [],
            'date':[],
            'url':[]
        }

        for product in data:
            Data_products['id'].append(product['id'])
            Data_products['colorDescription'].append(product['colorDescription'])
            Data_products['portrait_url'].append(product['images']['portraitURL'])
            Data_products['squarishURL'].append(product['images']['squarishURL'])
            Data_products['Stock'].append(product['inStock'])
            Data_products['isNew'].append(product['colorways'][0]['isNew'])
            Data_products[price_date_name].append(product['price']['currentPrice'])
            Data_products['fullPrice'].append(product['price']['fullPrice'])
            Data_products['subtitle'].append(product['subtitle'])
            Data_products['title'].append(product['title'])
            Data_products['date'].append(name_file[:-5])
            Data_products['url'].append(product['url'])

        return pd.DataFrame(Data_products)

    def generate_time_serie(self,*files):
        array_dataframes =[]
        for file in files:
            with open('data/'+file, encoding='utf-8') as fh:
                data = json.load(fh)

            price_date_name = file[:-5]
            Data_products = {
                "id" : [],
                price_date_name : []

            }

            for product in data:
                Data_products['id'].append(product['id'])
                Data_products[price_date_name].append(product['price']['currentPrice'])
            array_dataframes.append(pd.DataFrame(Data_products))

        # merge a la lista de dataframes

        df_final = reduce(lambda left,right: pd.merge(left,right,on='id', how='outer'), array_dataframes)

        return df_final

    def check_changes_2days(self, day):

        #obtenemos el dia anterior a la fecha dada
        date = datetime.strptime(day, "%Y-%m-%d")
        modified_date = date - timedelta(days=1)
        prev_day = datetime.strftime(modified_date, "%Y-%m-%d")
        #comprobamos que existan archivos para los dos dias
        day_file = day +'.json'
        prev_day_file = prev_day+'.json'
        if os.path.isfile('data/'+day_file) and os.path.isfile('data/'+prev_day_file) :
            df_time = self.generate_time_serie(prev_day_file,day_file)
            df_time['change'] = df_time[prev_day_file[:-5]] - df_time[day_file[:-5]]
            return df_time.loc[df_time['change']>0]
            #
        else:
            raise ValueError(
                    "Nombres de archivo no validos. "
                        f"Only one file per ZIP: {prev_day_file,day_file}"
                    )
    #funcion para checar si existe un cambio de precion entre un dia, y su dia anterior
    #NOTA:
    #Solo se ingresa la fecha del dia despues, el dia anterior lo se obtiene dentro de la funcion
    def check_changes_2days(self, day):

        #obtenemos el dia anterior a la fecha dada
        date = datetime.strptime(day, "%Y-%m-%d")
        modified_date = date - timedelta(days=1)
        prev_day = datetime.strftime(modified_date, "%Y-%m-%d")

        day_file = day +'.json'
        prev_day_file = prev_day+'.json'
                #comprobamos que existan archivos para los dos dias

        if os.path.isfile('data/'+day_file) and os.path.isfile('data/'+prev_day_file) :
            df_time = self.generate_time_serie(prev_day_file,day_file)
            df_time['change'] = df_time[prev_day_file[:-5]] - df_time[day_file[:-5]]
            return df_time.loc[df_time['change']>0].sort_values(by = 'change',ascending = False)
            #
        else:
            raise ValueError(
                    "Nombres de archivo no validos. "
                        f"Archivos: {prev_day_file,day_file}"
                    )

'''
