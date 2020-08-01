from utils.NikeCrawl import *
from utils.util import *
import pandas as pd
from datetime import date
import os
import unidecode

def update_full_sneaker_dic():
    list_dataf = glob.glob("data/liquidacion/*.json")
    list_dataf = [z[-15:] for z in list_dataf]
    info= ReportTM('data/Liquidacion/')
    dataframes = []
    #guardamos los dataframes
    for data in list_dataf:
        dataframes.append(info.generate_DF(data))
    #Extraemos solo informacion importante
    df = pd.concat(dataframes, sort=False)#[['id','title','portrait_url','url']]

    #df = 
    #df.loc[df['id'] == 'eff479e3-dab9-38e3-b814-4e8b49f371d6']

    df =df.drop_duplicates(subset=['title'])
    df.to_csv('data/liquidacion/dic_products/productsLiq.csv', encoding='utf-8')
    

def check_new_list_sneaker(day = None):
    #leemos el archivo con todos los tenis que han estad disponibles en liquidacion
    entire_df = pd.read_csv('data/Liquidacion/dic_products/productsLiq.csv')
    #borramos la primer columna incesesaria
    entire_df= entire_df.drop(['Unnamed: 0'], axis=1)
    # obtenemos el dia actual
    if day == None:
        today = date.today()
        actual_day = today.strftime("%Y-%m-%d")
    else:
        actual_day = day
        
    #leemos el archivo de el dia de hoy
    file_name= actual_day+'.json'
    if os.path.isfile('data/liquidacion/'+file_name):
        file_= ReportTM_LIQ('data/Liquidacion/')
        df_today = file_.generate_DF(file_name)
        s = set(entire_df.title.values)
        temp3 = [x for x in df_today.title.values if x not in s]
        df_today_util = df_today[df_today['title'].isin(temp3)]
        if df_today_util.shape[0] <0 : 
            return False
        df_today_util= df_today_util.drop(['id','colorDescription','Stock','isNew','subtitle','date','squarishURL' ],1)
        print(df_today_util.columns)
        df_today_util.columns = ['url_img','actual', 'prev','title','url']
        df_today_util['url'] = df_today_util['url'].apply(lambda x: 'https://www.nike.com/mx'+x[13:])
        df_today_util['url'] = df_today_util['url'].apply(lambda x: unidecode.unidecode(x))

        
        '''
        
        df_all_new_products = df_today.merge(entire_df.drop_duplicates(), on=['title'], 
                       how='left', indicator=True)
        df_all_new_products = df_all_new_products[df_all_new_products['_merge'] == 'left_only']
        if df_all_new_products.shape[0] <0 : 
            return False
        print(df_all_new_products.columns.values)
        df_all_new_products = df_all_new_products.drop(['id_x','colorDescription','Stock','isNew','subtitle','date','id_y','portrait_url_y','url_y','_merge','squarishURL'], 1)
        df_all_new_products.columns = ['url_img', 'prev','actual','title','url']
        df_all_new_products['url'] = df_all_new_products['url'].apply(lambda x: 'https://www.nike.com/mx'+x[13:])
        '''
    #comvertimos a formatod dic para enviar por correo
    else:
            raise ValueError(
                    "Nombres de archivo no validos. "
                        f"file: {file_name}"
                    )
    return  df_today_util.to_dict(orient='records')#df_all_new_products.to_dict(orient='records')



data = check_new_list_sneaker('2020-07-30')
print(data)
if data:
	send_email_Bcase1(data, ['saga_cth@hotmail.com'])
else:
	print('No hubo cambios')


