import os

# Configuración de la carpeta de salida
RUTA_SALIDA = "/home/globoscx/unews/salidas/input"
os.makedirs(RUTA_SALIDA, exist_ok=True)

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
