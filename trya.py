import re

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
]

# Lista de URLs para probar
urls_a_probar = [
    "https://www.chilevision.cl/noticias/nacional",
    "https://www.chilevision.cl/noticias/nacional/",
    "https://www.chilevision.cl/noticias/nacional?page=1",
    "https://www.elmostrador.cl/noticias/pais/",
    "https://www.cnnchile.com/deportes/",
    "https://www.adnradio.cl/noticias/ciencia-y-tecnologia/",
    "https://www.publimetro.cl/deportes/"
]

# Probar cada URL
for url in urls_a_probar:
    excluida = any(re.match(patron, url) for patron in PATRONES_EXCLUIDOS)
    print(f"URL: {url} - Excluida: {excluida}")
