import requests
from bs4 import BeautifulSoup
from datetime import datetime
import json
import re
import random
import time

# Configuración básica
FECHA_ACTUAL = datetime.now().strftime("%Y-%m-%d")

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

def obtener_enlaces_google(consulta):
    """Realiza una búsqueda en Google y obtiene los enlaces de resultados."""
    url = f"https://www.google.cl/search?q=site:{consulta['site']} after:{FECHA_ACTUAL}"
    headers = {'User-Agent': random.choice(USER_AGENTS)}
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        resultados = soup.find_all('div', class_='yuRUbf')
        enlaces = [resultado.find('a')['href'] for resultado in resultados if resultado.find('a')]
        
        # Pausa para evitar la detección
        time.sleep(random.uniform(2, 5))
        
        return enlaces
    except requests.exceptions.HTTPError as err:
        print(f"Error HTTP al solicitar {consulta['source']}: {err}")
    except requests.exceptions.RequestException as err:
        print(f"Error al solicitar {consulta['source']}: {err}")
    return []

def limpiar_enlaces(enlaces):
    """Elimina los parámetros UTM de los enlaces."""
    return [re.sub(r"(?:&sa=|&ved=|&usg=|&cvid=|&PC=).*", "", enlace) for enlace in enlaces]

def generar_json():
    """Genera un JSON con los enlaces obtenidos y limpios."""
    resultados = []
    
    for consulta in CONSULTAS:
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
    """Guarda los resultados en un archivo JSON."""
    nombre_archivo = f'noticias_{FECHA_ACTUAL}.json'
    
    with open(nombre_archivo, 'w') as archivo_json:
        json.dump(resultados, archivo_json, indent=2)
    
    print(f"Archivo JSON generado: {nombre_archivo}")

if __name__ == "__main__":
    resultados_json = generar_json()
    guardar_resultados(resultados_json)
