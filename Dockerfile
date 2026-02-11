## ------------------------------- Builder Stage ------------------------------ ##
FROM python:3.13-bookworm AS builder

# Instalar uv
ADD https://astral.sh/uv/install.sh /install.sh
RUN chmod +x /install.sh && /install.sh && rm /install.sh
ENV PATH="/root/.local/bin:${PATH}"

WORKDIR /app

# Copiar archivos necesarios para la instalación
COPY pyproject.toml uv.lock README.md ./
COPY src ./src

# Instalar dependencias y el proyecto
RUN uv sync --frozen --no-dev

## ------------------------------- Production Stage ------------------------------ ##
FROM python:3.13-slim-bookworm AS production

# Evitar que Python genere archivos .pyc y habilitar logs en tiempo real
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PATH="/app/.venv/bin:/root/.local/bin:${PATH}"

WORKDIR /app

# Instalar dependencias del sistema necesarias para Playwright
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Instalar uv en producción
ADD https://astral.sh/uv/install.sh /install.sh
RUN chmod +x /install.sh && /install.sh && rm /install.sh

# Copiar el entorno virtual desde el builder
COPY --from=builder /app/.venv /app/.venv

# Instalar Chromium y sus dependencias del sistema
RUN uv run playwright install chromium --with-deps

# Copiar el código fuente
COPY src ./src
COPY pyproject.toml README.md ./

# Crear directorios para datos y logs
RUN mkdir -p /app/data /app/logs

# Comando por defecto para iniciar el script
CMD ["uv", "run", "python", "src/main.py"]
