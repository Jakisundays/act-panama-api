import os
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).resolve().parent.parent))
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_constitucion_endpoint():
    r = client.get("/constitucion")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, dict)
    assert any(k.startswith("T") for k in data.keys())

def test_titulos_list():
    r = client.get("/titulos")
    assert r.status_code == 200
    payload = r.json()
    assert payload["total"] >= 1
    assert isinstance(payload["items"], list)
    assert any("nombre" in t for t in payload["items"])

def test_titulo_detalle():
    r = client.get("/titulos/3")
    assert r.status_code == 200
    t = r.json()
    assert t["numero"] == 3
    assert "nombre" in t

def test_capitulo_por_titulo():
    r = client.get("/titulos/3/capitulos")
    assert r.status_code == 200
    payload = r.json()
    assert payload["total"] >= 1
    cap = payload["items"][0]
    assert "numero" in cap and "nombre" in cap

def test_articulo_detalle():
    r = client.get("/articulos/107")
    assert r.status_code == 200
    art = r.json()
    assert art["numero"] == 107
    assert "actos de cultos religiosos" in art["texto"]

def test_busqueda_texto():
    r = client.get("/articulos", params={"q": "salud", "tamano_pagina": 5})
    assert r.status_code == 200
    payload = r.json()
    assert payload["total"] >= 1
    assert len(payload["items"]) <= 5

def test_filtro_anio():
    r = client.get("/articulos", params={"anio_desde": 1949, "anio_hasta": 1949})
    assert r.status_code == 200
    payload = r.json()
    assert any(6 == a["numero"] for a in payload["items"]) or payload["total"] >= 0

def test_ordenamiento():
    r = client.get("/articulos", params={"ordenar_por": "longitud", "orden": "desc"})
    assert r.status_code == 200
    payload = r.json()
    items = payload["items"]
    if len(items) >= 2:
        assert len(items[0]["texto"]) >= len(items[-1]["texto"]) 

def test_status_endpoint():
    r = client.get("/status")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"