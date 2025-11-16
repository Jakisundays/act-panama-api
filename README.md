# Constitución de Panamá API

API REST para consultar y gestionar datos de la Constitución de Panamá. Provee endpoints para listar Títulos, Capítulos y Artículos, buscar por texto, filtrar por años, ordenar y paginar resultados. Operaciones de escritura (crear, actualizar y eliminar artículos) requieren autenticación básica.

## Descripción

Este proyecto expone un servicio HTTP basado en FastAPI que sirve el contenido del archivo `constitucion_panama.json` y construye índices en memoria para consultas rápidas. Las rutas principales incluyen:

- `GET /status` — verificación de salud del servicio.
- `GET /constitucion` — devuelve el documento completo en JSON.
- `GET /titulos` — lista de Títulos, con búsqueda, orden y paginación.
- `GET /capitulos` — lista de Capítulos, con filtros por Título, orden y paginación.
- `GET /articulos` — lista de Artículos, con búsqueda textual y filtros por años.
- `GET /articulos/{numero}` — detalle de un Artículo por número.
- `POST /articulos` — crea un Artículo (requiere autenticación básica).
- `PUT /articulos/{numero}` — actualiza el texto de un Artículo (requiere autenticación básica).
- `DELETE /articulos/{numero}` — elimina un Artículo (requiere autenticación básica).

El servidor expone documentación interactiva en `http://localhost:8000/docs` (Swagger UI).

## Requisitos

- Python `3.11+` (la imagen Docker usa `3.11`; se ha probado también en `3.13`).
- `pip` y opcionalmente `virtualenv` para entorno local.
- Docker y Docker Compose (opcional para despliegue/ejecución en contenedor).
- Dependencias Python (archivo `requirements.txt`):
  - `fastapi`
  - `uvicorn`
  - `pydantic`
  - `httpx` (para pruebas)
  - `pytest`

## Instalación

### Entorno local

1. Crear y activar el entorno virtual:

   ```bash
   python -m venv venv
   source venv/bin/activate
   ```

2. Instalar dependencias:

   ```bash
   pip install -r requirements.txt
   ```

3. Configurar variables de entorno (opcional):

   Crea un archivo `.env` en la raíz del proyecto si vas a usar Docker Compose, o exporta variables en tu shell local.

   ```env
   PORT=8000
   CONSTITUCION_FILE=./constitucion_panama.json
   ```

### Docker / Docker Compose

1. Asegúrate de tener `docker` y `docker compose` instalados.
2. Construye y levanta el servicio:

   ```bash
   docker compose up --build -d
   ```

   - La imagen se construye desde el `Dockerfile` con base `python:3.11-slim`.
   - Se expone `http://localhost:8000`.

3. Alternativa sin Compose:

   ```bash
   docker build -t act_panama_api:latest .
   docker run --rm -p 8000:8000 act_panama_api:latest
   ```

## Uso

### Ejecutar el servidor localmente

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Documentación interactiva

- Accede a Swagger UI: `http://localhost:8000/docs`

### Ejemplos con `curl`

- Salud del servicio:

  ```bash
  curl -s http://localhost:8000/status
  ```

- Constitución completa:

  ```bash
  curl -s http://localhost:8000/constitucion
  ```

- Listado de Títulos (búsqueda y paginación):

  ```bash
  curl -s "http://localhost:8000/titulos?q=trabajo&ordenar_por=numero&orden=asc&pagina=1&tamano_pagina=10"
  ```

- Listado de Capítulos filtrando por Título:

  ```bash
  curl -s "http://localhost:8000/capitulos?titulo=III&ordenar_por=numero&orden=asc"
  ```

- Artículos: búsqueda, filtros por año y orden:

  ```bash
  curl -s "http://localhost:8000/articulos?q=salud&anio_desde=1949&anio_hasta=2004&ordenar_por=longitud&orden=desc&pagina=1&tamano_pagina=5"
  ```

- Detalle de un Artículo:

  ```bash
  curl -s http://localhost:8000/articulos/107
  ```

- Crear un Artículo (autenticación básica requerida):

  ```bash
  curl -s -X POST \
       -u usuario:clave \
       -H 'Content-Type: application/json' \
       -d '{"numero": 9999, "titulo_id": "I", "texto": "Contenido de prueba"}' \
       http://localhost:8000/articulos
  ```

- Actualizar un Artículo:

  ```bash
  curl -s -X PUT \
       -u usuario:clave \
       -H 'Content-Type: application/json' \
       -d '{"texto": "Nuevo contenido"}' \
       http://localhost:8000/articulos/9999
  ```

- Eliminar un Artículo:

  ```bash
  curl -s -X DELETE -u usuario:clave http://localhost:8000/articulos/9999 -i
  ```

Notas:
- La autenticación básica actualmente valida la presencia de credenciales; puedes usar cualquier `usuario:clave`. Se puede extender para verificar usuarios reales.
- Puedes sobreescribir la ruta del JSON con `CONSTITUCION_FILE`.

### Pruebas

Ejecuta el conjunto de tests:

```bash
pytest -q
```

Marcadores disponibles:

```bash
pytest -q -m funcionalidad
pytest -q -m rendimiento
```

## Contribución

1. Haz un fork del repositorio y crea una rama descriptiva (`feature/mi-cambio`).
2. Sigue PEP8 y añade docstrings donde corresponda. Mantén los modelos en Pydantic y las rutas documentadas.
3. Añade/ajusta pruebas cuando modifiques endpoints o lógica.
4. Verifica que los tests pasan (`pytest -q`).
5. Abre un Pull Request explicando el cambio, contexto y cómo probarlo.

## Licencia

Este proyecto está bajo la licencia MIT. Consulta más detalles en: https://opensource.org/licenses/MIT

## Recursos

- FastAPI: https://fastapi.tiangolo.com/
- Uvicorn: https://www.uvicorn.org/
- Pydantic: https://docs.pydantic.dev/latest/
- Docker Compose: https://docs.docker.com/compose/