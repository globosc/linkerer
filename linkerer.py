import requests
from bs4 import BeautifulSoup
import time
import json
import re

# Obtener la fecha actual
fecha_actual = time.strftime("%Y-%m-%d")

# Definir las consultas de búsqueda y las fuentes de noticias
consultas = [
    {"category": "Nacional", "site": "https://www.latercera.com/nacional/noticia/", "source": "La Tercera", "diminutive": "LT"},
    {"category": "Nacional", "site": "https://www.biobiochile.cl/noticias/nacional/", "source": "Radio BioBio", "diminutive": "RBB"},
    {"category": "Nacional", "site": "https://www.emol.com/noticias/Nacional/", "source": "Emol", "diminutive": "EMOL"},
    {"category": "Nacional", "site": "https://ellibero.cl/actualidad/", "source": "El Libero", "diminutive": "EL"},
    {"category": "Nacional", "site": "https://www.cooperativa.cl/noticias/pais", "source": "Cooperativa", "diminutive": "Co"},
    {"category": "Nacional", "site": "https://www.ex-ante.cl/category/nacional/", "source": "EX-ANTE", "diminutive": "EX"},
    {"category": "Nacional", "site": "https://www.chilevision.cl/noticias/nacional", "source": "Chilevisión", "diminutive": "CHV"},
    {"category": "Nacional", "site": "https://www.concierto.cl/tag/actualidad/", "source": "Emol", "diminutive": "EM"},
    {"category": "Nacional", "site": "https://www.eldinamo.cl/pais/", "source": "El Dínamo", "diminutive": "ED"},
    {"category": "Nacional", "site": "https://www.cnnchile.com/pais/", "source": "CNN Chile", "diminutive": "CNN"},
    {"category": "Nacional", "site": "https://www.elmostrador.cl/noticias/pais/", "source": "El Mostrador", "diminutive": "ELMO"},
    {"category": "Nacional", "site": "https://www.adnradio.cl/noticias/", "source": "ADN", "diminutive": "ADN"},
    {"category": "Nacional", "site": "https://www.t13.cl/noticia/nacional/", "source": "T13", "diminutive": "T13"},
    {"category": "Nacional", "site": "https://www.terra.cl/nacionales/", "source": "TERRA", "diminutive": "TERRA"},
    {"category": "Nacional", "site": "https://www.24horas.cl/actualidad/nacional", "source": "24 Horas", "diminutive": "24H"},
    {"category": "Nacional", "site": "https://radio.uchile.cl/temas/nacional/", "source": "Radio UDECHILE", "diminutive": "RU"},
    {"category": "Nacional", "site": "https://www.theclinic.cl/noticias/actualidad/nacional/", "source": "The Clinic", "diminutive": "TCLI"},
    # Agrega más consultas aquí según sea necesario
]

# Función para realizar la solicitud a Google y obtener los enlaces
def obtener_enlaces(consulta):
    url = f"https://www.google.com/search?q=site:{consulta['site']} after:{fecha_actual}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            resultados = soup.find_all('a', href=lambda href: href and href.startswith('/url?q='))
            enlaces = [resultado['href'].replace('/url?q=', '') for resultado in resultados]
            enlaces = [enlace for enlace in enlaces if not (
                enlace.startswith('/search%3Fq%3Dsite:') or 
                enlace.startswith('https://support.google.com/websearc') or 
                enlace.startswith('https://accounts.google.com/ServiceLogin') or 
                enlace.startswith('https://maps.google.com')
            )]
            return enlaces
        else:
            print(f"Error al realizar la solicitud a {consulta['source']}: código de estado {response.status_code}")
            return []
    except requests.exceptions.RequestException as e:
        print(f"Error al realizar la solicitud a {consulta['source']}: {e}")
        return []

# Función para eliminar los parámetros UTM de los enlaces
def limpiar_enlaces(enlaces):
    enlaces_limpios = []
    for enlace in enlaces:
        enlace_limpiado = re.sub(r"(?:&sa=|&ved=|&usg=).*", "", enlace)
        enlaces_limpios.append(enlace_limpiado)
    return enlaces_limpios

# Función para generar el formato JSON con los enlaces filtrados
def generar_json():
    resultados = []
    for consulta in consultas:
        enlaces = obtener_enlaces(consulta)
        enlaces_limpios = limpiar_enlaces(enlaces)
        for enlace in enlaces_limpios:
            resultados.append({
                "url": enlace,
                "category": consulta["category"],
                "source": consulta["source"],
                "diminutive": consulta["diminutive"]
            })
    return resultados

# Guardar los resultados en formato JSON
resultados_json = generar_json()
with open(f'resultados_finales_{fecha_actual}.json', 'w') as archivo_json:
    json.dump(resultados_json, archivo_json, indent=2)

# Mostrar los enlaces finales en pantalla
for resultado in resultados_json:
    print(resultado)
