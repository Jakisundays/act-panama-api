"""Pruebas de funcionalidad y rendimiento para la API de Constitución de Panamá.

Uso de categorías:
- Ejecutar solo funcionalidad: pytest -q -m funcionalidad
- Ejecutar solo rendimiento: pytest -q -m rendimiento
"""

import time
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).resolve().parent.parent))
from fastapi.testclient import TestClient
import pytest
from main import app


@pytest.fixture(scope="session")
def client():
    """Cliente de pruebas compartido para toda la sesión."""
    return TestClient(app)


@pytest.mark.funcionalidad
def test_endpoints_basicos_ok(client):
    """Valida que endpoints principales respondan con 200 y JSON válido."""
    for ep in ["/status", "/constitucion", "/titulos", "/capitulos", "/articulos"]:
        r = client.get(ep)
        assert r.status_code == 200
        assert isinstance(r.json(), dict)




@pytest.mark.rendimiento
def test_latencia_promedio_y_maxima(client):
    """Mide latencia promedio y máxima para rutas GET bajo carga normal."""
    endpoints = ["/status", "/constitucion", "/titulos", "/capitulos", "/articulos"]
    latencias = []
    for ep in endpoints:
        t0 = time.monotonic()
        r = client.get(ep)
        dt = time.monotonic() - t0
        assert r.status_code == 200
        latencias.append(dt)
    promedio = statistics.mean(latencias)
    maxima = max(latencias)
    print({"latencia_promedio": promedio, "latencia_maxima": maxima})
    assert promedio >= 0.0
    assert maxima >= 0.0


@pytest.mark.rendimiento
def test_estres_concurrente_lectura(client):
    """Prueba de estrés con múltiples requests concurrentes sobre endpoints GET."""
    def hit(ep: str):
        t0 = time.monotonic()
        r = client.get(ep)
        dt = time.monotonic() - t0
        return ep, r.status_code, dt

    endpoints = ["/constitucion", "/titulos", "/capitulos", "/articulos"]
    tasks = []
    with ThreadPoolExecutor(max_workers=16) as ex:
        for _ in range(50):
            for ep in endpoints:
                tasks.append(ex.submit(hit, ep))
        resultados = [f.result() for f in as_completed(tasks)]
    codigos = [code for _, code, _ in resultados]
    latencias = [dt for _, _, dt in resultados]
    assert all(code == 200 for code in codigos)
    promedio = statistics.mean(latencias)
    maxima = max(latencias)
    print({"concurrencia_promedio": promedio, "concurrencia_maxima": maxima})
    assert promedio >= 0.0
    assert maxima >= 0.0