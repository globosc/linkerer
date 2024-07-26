import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import json
import re
import random
import time
import logging
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
import os
import asyncio
from aiohttp import ClientSession
from sources import RUTA_SALIDA, USER_AGENTS, CONSULTAS

# Configuración de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Lista de patrones exactos a excluir
PATRONES_EXCLUIDOS = [
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
    r'https://www.chilevision.cl/noticias/nacional$'
]


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

def limpiar_enlaces(enlaces):
    """Elimina los parámetros UTM y otros parámetros de seguimiento de los enlaces."""
    return [re.sub(r"(?:\?.*?utm.*|&.*|#.*)", "", enlace) for enlace in enlaces]

def filtrar_exclusiones(enlaces):
    """Filtra los enlaces que coinciden con los patrones de exclusión."""
    return [enlace for enlace in enlaces if not any(re.match(patron, enlace) for patron in PATRONES_EXCLUIDOS)]

async def generar_json():
    """Genera un JSON con los enlaces obtenidos y limpios."""
    async with ClientSession() as session:
        tareas = [obtener_enlaces_google(consulta, session) for consulta in CONSULTAS]
        resultados = await asyncio.gather(*tareas)
    
    resultados_json = []
    for consulta, enlaces in zip(CONSULTAS, resultados):
        enlaces_limpios = limpiar_enlaces(enlaces)
        enlaces_filtrados = filtrar_exclusiones(enlaces_limpios)
        for enlace in enlaces_filtrados:
            resultados_json.append({
                "url": enlace,
                "category": consulta["category"],
                "source": consulta["source"],
                "diminutive": consulta["diminutive"]
            })
    return resultados_json

def cargar_resultados_anteriores():
    """Carga los resultados del archivo JSON de la hora anterior si existe."""
    hora_actual = datetime.now()
    for i in range(1, 25):  # Intentar las últimas 24 horas
        hora_anterior = (hora_actual - timedelta(hours=i)).strftime("%Y%m%d_%H")
        nombre_archivo_anterior = os.path.join(RUTA_SALIDA, f'linkerer_{hora_anterior}.json')
        if os.path.exists(nombre_archivo_anterior):
            try:
                with open(nombre_archivo_anterior, 'r') as archivo_json:
                    return json.load(archivo_json)
            except IOError as e:
                logging.error(f"Error al cargar el archivo JSON anterior: {e}")
                return []
    return []

def filtrar_nuevos_resultados(resultados_nuevos, resultados_anteriores):
    """Filtra los resultados nuevos para eliminar los que ya existen en los resultados anteriores."""
    urls_anteriores = {resultado['url'] for resultado in resultados_anteriores}
    return [resultado for resultado in resultados_nuevos if resultado['url'] not in urls_anteriores]

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
    resultados_anteriores = cargar_resultados_anteriores()
    resultados_nuevos = await generar_json()
    if resultados_nuevos:
        resultados_filtrados = filtrar_nuevos_resultados(resultados_nuevos, resultados_anteriores)
        if resultados_filtrados:
            nombre_archivo = guardar_resultados(resultados_filtrados)
            if nombre_archivo:
                enviar_a_api(nombre_archivo)
            return {"status": "success", "message": "Archivo JSON generado y enviado a la API correctamente."}
        else:
            logging.info("No hay nuevos resultados para guardar.")
            return {"status": "success", "message": "No hay nuevos resultados para guardar."}
    else:
        return {"status": "failure", "message": "No se pudieron generar los resultados."}

if __name__ == "__main__":
    asyncio.run(main())
