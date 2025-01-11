# Etapa de construcción
FROM python:3.9-slim-bullseye AS builder

# Configuración de variables de entorno para la construcción
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Instala las dependencias del sistema necesarias para compilar paquetes
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Crea y activa un entorno virtual
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copia y instala los requerimientos
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Etapa final
FROM python:3.9-slim-bullseye

ENV TZ=America/Santiago \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH" \
    APP_USER=linkerer \
    APP_HOME=/home/linkerer

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    # Crea un usuario con el nombre del servicio
    && useradd --create-home ${APP_USER} \
    && mkdir -p /app ${APP_HOME}/output ${APP_HOME}/logs \
    && chown -R ${APP_USER}:${APP_USER} /app ${APP_HOME}

# Copia el entorno virtual desde la etapa de construcción
COPY --from=builder /opt/venv /opt/venv

# Establece el directorio de trabajo
WORKDIR /app

# Copia los archivos de la aplicación
COPY --chown=${APP_USER}:${APP_USER} . .

# Cambia al usuario no root
USER ${APP_USER}

# Expone el puerto (cambiado a 8000 para el linkerer)
EXPOSE 8000

# Configuración de healthcheck
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl --fail http://localhost:8000/health || exit 1

# Límites de memoria y CPU (ajustados para el scraping)
ENV UVICORN_MEMORY_LIMIT="1024m" \
    UVICORN_WORKERS="1" \
    UVICORN_TIMEOUT="600"

# Comando para ejecutar la aplicación
CMD ["uvicorn", "app.api.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--timeout-keep-alive", "120", \
     "--workers", "1", \
     "--log-level", "info"]