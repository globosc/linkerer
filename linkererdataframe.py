import os
import re
import random
import logging
import asyncio
import pandas as pd
from aiohttp import ClientSession
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
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
    r'https://www.elciudadano.com/actualidad/\?amp$'
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

async def generar_dataframe():
    """Genera un DataFrame con los enlaces obtenidos y limpios."""
    async with ClientSession() as session:
        tareas = [obtener_enlaces_google(consulta, session) for consulta in CONSULTAS]
        resultados = await asyncio.gather(*tareas)
    
    data = []
    for consulta, enlaces in zip(CONSULTAS, resultados):
        enlaces_limpios = limpiar_enlaces(enlaces)
        enlaces_filtrados = filtrar_exclusiones(enlaces_limpios)
        for enlace in enlaces_filtrados:
            data.append({
                "url": enlace,
                "category": consulta["category"],
                "source": consulta["source"],
                "diminutive": consulta["diminutive"]
            })
    
    df = pd.DataFrame(data)
    return df

def cargar_resultados_anteriores():
    """Carga los resultados del archivo CSV de la hora anterior si existe."""
    hora_actual = datetime.now()
    for i in range(1, 25):  # Intentar las últimas 24 horas
        hora_anterior = (hora_actual - timedelta(hours=i)).strftime("%Y%m%d_%H")
        nombre_archivo_anterior = os.path.join(RUTA_SALIDA, f'linkerer_{hora_anterior}.csv')
        if os.path.exists(nombre_archivo_anterior):
            try:
                df = pd.read_csv(nombre_archivo_anterior)
                if 'url' in df.columns:
                    return df
                else:
                    logging.error(f"El archivo {nombre_archivo_anterior} no contiene la columna 'url'.")
                    return pd.DataFrame(columns=['url', 'category', 'source', 'diminutive'])
            except IOError as e:
                logging.error(f"Error al cargar el archivo CSV anterior: {e}")
                return pd.DataFrame(columns=['url', 'category', 'source', 'diminutive'])
    return pd.DataFrame(columns=['url', 'category', 'source', 'diminutive'])

def filtrar_nuevos_resultados(resultados_nuevos, resultados_anteriores):
    """Filtra los resultados nuevos para eliminar los que ya existen en los resultados anteriores."""
    urls_anteriores = set(resultados_anteriores['url'])
    return resultados_nuevos[~resultados_nuevos['url'].isin(urls_anteriores)]

def guardar_resultados(resultados):
    """Guarda los resultados en un archivo CSV en la ruta especificada."""
    timestamp = datetime.now().strftime("%Y%m%d_%H")
    nombre_archivo = os.path.join(RUTA_SALIDA, f'linkerer_{timestamp}.csv')
    try:
        resultados.to_csv(nombre_archivo, index=False)
        logging.info(f"Archivo CSV generado: {nombre_archivo}")
        return nombre_archivo  # Devuelve el nombre del archivo generado
    except IOError as e:
        logging.error(f"Error al guardar el archivo CSV: {e}")
        return None

# Comentado: Envío a la API
# def enviar_a_api(nombre_archivo):
#     """Envía el archivo CSV generado a la API de acortamiento de enlaces."""
#     api_url = "http://172.22.0.2:5000/shortener/"
#     try:
#         with open(nombre_archivo, 'rb') as file:
#             response = requests.post(api_url, files={"file": file})
#             response.raise_for_status()
#             logging.info(f"Respuesta de la API: {response.json()}")
#     except requests.exceptions.RequestException as err:
#         logging.error(f"Error al enviar el archivo a la API: {err}")

async def main():
    """Función principal."""
    resultados_anteriores = cargar_resultados_anteriores()
    resultados_nuevos = await generar_dataframe()
    if not resultados_nuevos.empty:
        resultados_filtrados = filtrar_nuevos_resultados(resultados_nuevos, resultados_anteriores)
        if not resultados_filtrados.empty:
            nombre_archivo = guardar_resultados(resultados_filtrados)
            print(resultados_filtrados)  # Imprime el DataFrame generado
            return {"status": "success", "message": "Archivo CSV generado correctamente."}
        else:
            logging.info("No hay nuevos resultados para guardar.")
            return {"status": "success", "message": "No hay nuevos resultados para guardar."}
    else:
        return {"status": "failure", "message": "No se pudieron generar los resultados."}

if __name__ == "__main__":
    asyncio.run(main())
