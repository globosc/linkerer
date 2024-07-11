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

# Configuración de la carpeta de salida
RUTA_SALIDA = "/home/globoscx/unews/salidas/input"
os.makedirs(RUTA_SALIDA, exist_ok=True)

# Configuración de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Definir los User-Agents
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Firefox/88.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.96 Safari/537.36"
]

# Definir las consultas de búsqueda y las fuentes de noticias
CONSULTAS = [
    {"category": "Nacional", "site": "https://www.latercera.com/nacional/noticia/", "source": "La Tercera", "diminutive": "LT"},
    {"category": "Nacional", "site": "https://www.biobiochile.cl/noticias/nacional/", "source": "Radio BioBio", "diminutive": "RBB"},
    {"category": "Nacional", "site": "https://www.emol.com/noticias/Nacional/", "source": "EMOL", "diminutive": "EMOL"},
    {"category": "Nacional", "site": "https://www.eldesconcierto.cl/nacional/", "source": "El Desconcierto", "diminutive": "ELDS"},
    {"category": "Nacional", "site": "https://www.eldinamo.cl/pais/", "source": "El Dinamo", "diminutive": "ELDI"},
    {"category": "Nacional", "site": "https://www.elciudadano.com/actualidad/", "source": "El Ciudadano", "diminutive": "ELCI"},
    {"category": "Nacional", "site": "https://cambio21.cl/politica", "source": "Cambio21", "diminutive": "C21"},
    {"category": "Nacional", "site": "https://www.df.cl/mercados/", "source": "Diario Financiero", "diminutive": "DF"},
    {"category": "Nacional", "site": "https://www.chilevision.cl/noticias/nacional/", "source": "Chilevision", "diminutive": "CHV"},
    {"category": "Nacional", "site": "https://www.24horas.cl/actualidad/nacional/", "source": "24 Horas", "diminutive": "24H"},
    {"category": "Nacional", "site": "https://www.cooperativa.cl/noticias/pais/", "source": "Cooperativa", "diminutive": "Coop"},
    {"category": "Nacional", "site": "https://www.cnnchile.com/pais/", "source": "CNN Chile", "diminutive": "CNN"},
    {"category": "Nacional", "site": "https://www.t13.cl/noticia/nacional/", "source": "Teletrece", "diminutive": "T13"},
    {"category": "Nacional", "site": "https://www.elmostrador.cl/noticias/pais/", "source": "El Mostrador", "diminutive": "ELMO"},
    {"category": "Nacional", "site": "https://www.publimetro.cl/noticias/", "source": "Publimetro", "diminutive": "PM"},
    {"category": "Nacional", "site": "https://www.meganoticias.cl/nacional/", "source": "Meganoticias", "diminutive": "MN"},
]

def obtener_user_agent():
    """Devuelve un User-Agent aleatorio de la lista."""
    return random.choice(USER_AGENTS)

def obtener_enlaces_google(consulta):
    """Realiza una búsqueda en Google y obtiene los enlaces de resultados."""
    url = f"https://www.google.cl/search?q=site:{consulta['site']}+after:{datetime.now().strftime('%Y-%m-%d')}"
    headers = {'User-Agent': obtener_user_agent()}
    session = requests.Session()
    retries = Retry(total=3, backoff_factor=0.3, status_forcelist=[500, 502, 503, 504])
    session.mount('https://', HTTPAdapter(max_retries=retries))

    try:
        response = session.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        resultados = soup.find_all('div', class_='yuRUbf')
        enlaces = [resultado.find('a')['href'] for resultado in resultados if resultado.find('a')]
        time.sleep(random.uniform(1, 3))
        return enlaces
    except requests.exceptions.RequestException as err:
        logging.error(f"Error al solicitar {consulta['source']}: {err}")
        return []

def limpiar_enlaces(enlaces):
    """Elimina los parámetros UTM y otros parámetros de seguimiento de los enlaces."""
    return [re.sub(r"(?:\?.*?utm.*|&.*|#.*)", "", enlace) for enlace in enlaces]

def generar_json():
    """Genera un JSON con los enlaces obtenidos y limpios."""
    resultados = []
    for consulta in CONSULTAS:
        logging.info(f"Buscando enlaces para {consulta['source']} ({consulta['category']})")
        enlaces = obtener_enlaces_google(consulta)
        enlaces_limpios = limpiar_enlaces(enlaces)
        for enlace in enlaces_limpios:
            resultados.append({
                "url": enlace,
                "category": consulta["category"],
                "source": consulta["source"],
                "diminutive": consulta["diminutive"]
            })
    return resultados

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

def main():
    """Función principal que será invocada por DigitalOcean Functions."""
    resultados_json = generar_json()
    if resultados_json:
        nombre_archivo = guardar_resultados(resultados_json)
        if nombre_archivo:
            enviar_a_api(nombre_archivo)
        return {"status": "success", "message": "Archivo JSON generado y enviado a la API correctamente."}
    else:
        return {"status": "failure", "message": "No se pudieron generar los resultados."}

if __name__ == "__main__":
    main()
