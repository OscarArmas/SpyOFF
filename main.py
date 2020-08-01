from utils.NikeCrawl import *
from utils.util import send_email

def main():
	#===========================INICIO========
	#crawl para pagina principal
	crawl = nike_crawler()

	crawl.obtain_save_data()

	status_data = crawl.verbose()
	#===========================FIN========




	#===========================INICIO========
	#crawl para pagina Liquidacion
	crawl_Liq = nike_crawler_Liquidacion()

	crawl_Liq.obtain_save_data()
	#Enviamos el email de status
	status_data_liq = crawl_Liq.verbose()
	#===========================FIN========
	
	status_data = status_data +status_data_liq

	send_email(status_data,'saga_cth@hotmail.com')




	#================INICIO

if __name__ == '__main__':
    main()