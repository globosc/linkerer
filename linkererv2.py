import requests
from bs4 import BeautifulSoup
from datetime import datetime
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

async def generar_json():
    """Genera un JSON con los enlaces obtenidos y limpios."""
    async with ClientSession() as session:
        tareas = [obtener_enlaces_google(consulta, session) for consulta in CONSULTAS]
        resultados = await asyncio.gather(*tareas)
    
    resultados_json = []
    for consulta, enlaces in zip(CONSULTAS, resultados):
        enlaces_limpios = limpiar_enlaces(enlaces)
        for enlace in enlaces_limpios:
            resultados_json.append({
                "url": enlace,
                "category": consulta["category"],
                "source": consulta["source"],
                "diminutive": consulta["diminutive"]
            })
    return resultados_json

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
    api_url = "http://172.22.0.2:5000/shortener/"
    try:
        with open(nombre_archivo, 'rb') as file:
            response = requests.post(api_url, files={"file": file})
            response.raise_for_status()
            logging.info(f"Respuesta de la API: {response.json()}")
    except requests.exceptions.RequestException as err:
        logging.error(f"Error al enviar el archivo a la API: {err}")

async def main():
    """Función principal que será invocada por DigitalOcean Functions."""
    resultados_json = await generar_json()
    if resultados_json:
        nombre_archivo = guardar_resultados(resultados_json)
        if nombre_archivo:
            enviar_a_api(nombre_archivo)
        return {"status": "success", "message": "Archivo JSON generado y enviado a la API correctamente."}
    else:
        return {"status": "failure", "message": "No se pudieron generar los resultados."}

if __name__ == "__main__":
    asyncio.run(main())
