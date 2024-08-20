import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import json
import re
import random
import logging
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
import os
import asyncio
from aiohttp import ClientSession, ClientTimeout
from sources import RUTA_SALIDA, USER_AGENTS, CONSULTAS

# Configuración de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Precompilación de patrones para mejorar el rendimiento
PATRONES_EXCLUIDOS = [re.compile(patron) for patron in [
    r'https://www.elmostrador.cl/noticias/pais/$',
    r'https://www.meganoticias.cl/nacional/\?page=\d+$',
    r'https://www.24horas.cl/actualidad/nacional/p/\d+$',
    r'https://www.24horas.cl/actualidad/nacional\?$',
    r'https://www.24horas.cl/actualidad/nacional$',
    r'https://cambio21.cl/politica$',
    r'https://www.df.cl/mercados$',
    r'https://www.eldinamo.cl/pais/page/\d+/$',
    r'https://www.elciudadano.com/actualidad/page/\d+/$',
    r'https://www.elciudadano.com/actualidad/\?filter_by=\w+$',
    r'https://www.elciudadano.com/actualidad/\?amp$',
    r'https://www.chilevision.cl/noticias/nacional/?(\?.*)?$',  # Ajuste para coincidir con o sin / y con parámetros
    r'https://www.adnradio.cl/noticias/$',
    r'https://www.adnradio.cl/noticias/economia/$',
    r'https://www.adnradio.cl/noticias/nacional/$',
    r'https://www.adnradio.cl/noticias/politica/$',
    r'https://www.eldinamo.cl/pais/page/\d+/\?page=\d+$',
    r'https://www.24horas.cl/deportes$',
    r'https://www.24horas.cl/deportes/futbol-internacional$',
    r'https://www.24horas.cl/deportes/futbol-nacional$',
    r'https://www.24horas.cl/deportes/futbol-nacional/colo-colo$',
    r'https://www.ex-ante.cl/$',
    r'https://www.cnnchile.com/deportes/$',
    r'https://www.adnradio.cl/noticias/ciencia-y-tecnologia/$',
    r'https://www.publimetro.cl/deportes/$'
]]

def obtener_user_agent():
    """Devuelve un User-Agent aleatorio de la lista."""
    return random.choice(USER_AGENTS)

async def obtener_enlaces_google(consulta, session):
    """Realiza una búsqueda en Google y obtiene los enlaces de resultados."""
    url = f"https://www.google.cl/search?q=site:{consulta['site']}+after:{datetime.now().strftime('%Y-%m-%d')}"
    headers = {'User-Agent': obtener_user_agent()}

    try:
        async with session.get(url, headers=headers) as response:
            response.raise_for_status()
            text = await response.text()
            soup = BeautifulSoup(text, 'html.parser')
            resultados = soup.find_all('div', class_='yuRUbf')
            enlaces = [resultado.find('a')['href'] for resultado in resultados if resultado.find('a')]
            await asyncio.sleep(random.uniform(1, 3))
            return enlaces
    except Exception as err:
        logging.error(f"Error al solicitar {consulta['source']}: {err}")
        return []


def limpiar_y_filtrar_enlaces(enlaces):
    """Limpia los enlaces y filtra los que coinciden con los patrones de exclusión."""
    enlaces_filtrados = []
    for enlace in enlaces:
        enlace_limpio = re.sub(r"(?:\?.*?utm.*|&.*|#.*)", "", enlace)
        if not any(patron.match(enlace_limpio) for patron in PATRONES_EXCLUIDOS):
            enlaces_filtrados.append(enlace_limpio)
        else:
            logging.info(f"Enlace excluido por patrón: {enlace_limpio}")
    return enlaces_filtrados

async def generar_json():
    """Genera un JSON con los enlaces obtenidos y limpios."""
    async with ClientSession() as session:
        tareas = [obtener_enlaces_google(consulta, session) for consulta in CONSULTAS]
        resultados = await asyncio.gather(*tareas)
    
    resultados_json = []
    for consulta, enlaces in zip(CONSULTAS, resultados):
        enlaces_filtrados = limpiar_y_filtrar_enlaces(enlaces)
        for enlace in enlaces_filtrados:
            resultados_json.append({
                "url": enlace,
                "category": consulta["category"],
                "source": consulta["source"],
                "diminutive": consulta["diminutive"],
                "date": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "content_length": "",   # Campo vacío para content_length
                "sentiment": "",        # Campo vacío para sentiment
                "keywords": "",         # Campo vacío para keywords
                "popularity": "",       # Campo vacío para popularity
                "subcategory": "",      # Campo vacío para subcategory
                "holding": "",          # Campo vacío para holding
                "update_frequency": consulta.get("update_frequency", ""),
                "content_type": consulta.get("content_type", "")
            })
    logging.debug(f"JSON generado: {resultados_json}")
    return resultados_json

async def cargar_resultados_anteriores():
    """Carga los resultados del archivo JSON de la hora anterior si existe."""
    hora_actual = datetime.now()
    tareas = []

    for i in range(1, 25):  # Intentar las últimas 24 horas
        hora_anterior = (hora_actual - timedelta(hours=i)).strftime("%Y%m%d_%H")
        nombre_archivo_anterior = os.path.join(RUTA_SALIDA, f'linkerer_{hora_anterior}.json')
        if os.path.exists(nombre_archivo_anterior):
            tareas.append(cargar_json(nombre_archivo_anterior))

    resultados_anteriores = await asyncio.gather(*tareas)
    resultados_anteriores_flat = [resultado for lista in resultados_anteriores for resultado in lista]
    logging.debug(f"Resultados anteriores cargados: {resultados_anteriores_flat}")
    return resultados_anteriores_flat

async def cargar_json(ruta):
    """Carga el archivo JSON de la ruta dada."""
    try:
        with open(ruta, 'r') as archivo_json:
            return json.load(archivo_json)
    except IOError as e:
        logging.error(f"Error al cargar el archivo JSON {ruta}: {e}")
        return []

def filtrar_nuevos_resultados(resultados_nuevos, resultados_anteriores):
    """Filtra los resultados nuevos para eliminar los que ya existen en los resultados anteriores."""
    urls_anteriores = {resultado['url'] for resultado in resultados_anteriores}
    resultados_filtrados = [resultado for resultado in resultados_nuevos if resultado['url'] not in urls_anteriores]
    logging.debug(f"Resultados filtrados: {resultados_filtrados}")
    return resultados_filtrados

def guardar_resultados(resultados):
    """Guarda los resultados en un archivo JSON en la ruta especificada."""
    timestamp = datetime.now().strftime("%Y%m%d_%H")
    nombre_archivo = os.path.join(RUTA_SALIDA, f'linkerer_{timestamp}.json')
    try:
        with open(nombre_archivo, 'w') as archivo_json:
            json.dump(resultados, archivo_json, indent=2)
        logging.info(f"Archivo JSON generado: {nombre_archivo}")
        return nombre_archivo  # Devuelve el nombre del archivo generado
    except IOError as e:
        logging.error(f"Error al guardar el archivo JSON: {e}")
        return None

def enviar_a_api(nombre_archivo):
    """Envía el archivo JSON generado a la API de acortamiento de enlaces."""
    api_url = "http://192.168.2.113:5000/shortener/"
    try:
        with open(nombre_archivo, 'rb') as file:
            response = requests.post(api_url, files={"file": file})
            response.raise_for_status()
            logging.info(f"Respuesta de la API: {response.json()}")
    except requests.exceptions.RequestException as err:
        logging.error(f"Error al enviar el archivo a la API: {err}")

async def main():
    """Función principal que será invocada por DigitalOcean Functions."""
    logging.info("Inicio de la función main")

    resultados_anteriores = await cargar_resultados_anteriores()
    resultados_nuevos = await generar_json()

    if resultados_nuevos:
        resultados_filtrados = filtrar_nuevos_resultados(resultados_nuevos, resultados_anteriores)

        if resultados_filtrados:
            nombre_archivo = guardar_resultados(resultados_filtrados)
            if nombre_archivo:
                enviar_a_api(nombre_archivo)
            else:
                logging.error("No se generó ningún archivo para enviar a la API.")
        else:
            logging.info("No hay nuevos resultados después de filtrar.")
    else:
        logging.info("No se generaron nuevos resultados.")

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
