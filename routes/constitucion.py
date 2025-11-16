from fastapi import APIRouter, Request, HTTPException, Query
from fastapi.responses import JSONResponse
 
from pydantic import BaseModel
from typing import Optional, Dict, Any, List, Tuple
from pathlib import Path
from functools import lru_cache
import os
import json
import re

router = APIRouter()

 

BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_JSON_PATH = BASE_DIR / "constitucion_panama.json"
CONSTITUCION_PATH = Path(os.getenv("CONSTITUCION_FILE", str(DEFAULT_JSON_PATH)))

 

class Articulo(BaseModel):
    numero: int
    titulo_num: int
    titulo_nombre: str
    capitulo_num: Optional[int] = None
    capitulo_nombre: Optional[str] = None
    texto: str

class Capitulo(BaseModel):
    titulo_num: int
    titulo_nombre: str
    numero: int
    nombre: str
    articulos: List[Articulo]

class Titulo(BaseModel):
    numero: int
    nombre: str
    capitulos: Optional[List[Capitulo]] = None
    articulos: Optional[List[Articulo]] = None

class Paginacion(BaseModel):
    total: int
    pagina: int
    tamano_pagina: int
    items: List[Any]

 

def extraer_romano(s: str) -> Optional[int]:
    m = re.search(r"T[ÍI]TULO\s+([IVXLCDM]+)", s, re.IGNORECASE)
    if not m:
        return None
    r = m.group(1).upper()
    valores = {"I":1,"V":5,"X":10,"L":50,"C":100,"D":500,"M":1000}
    total = 0
    prev = 0
    for ch in r[::-1]:
        val = valores.get(ch,0)
        if val < prev:
            total -= val
        else:
            total += val
        prev = val
    return total if total > 0 else None

def extraer_capitulo_num(nombre: str) -> Optional[int]:
    m = re.search(r"Cap[íi]tulo\s+(\d+)", nombre)
    return int(m.group(1)) if m else None

def extraer_articulo_num(k: str) -> Optional[int]:
    m = re.search(r"articulo-(\d+)", k)
    return int(m.group(1)) if m else None

 

@lru_cache(maxsize=8)
def cargar_json(mtime: float) -> Dict[str, Any]:
    with open(CONSTITUCION_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

 

@lru_cache(maxsize=8)
def construir_indices(mtime: float) -> Dict[str, Any]:
    data = cargar_json(mtime)
    titulos = {}
    titulos_por_num = {}
    capitulos = {}
    articulos = {}
    for nombre_titulo, contenido_titulo in data.items():
        tnum = extraer_romano(nombre_titulo) or 0
        tinfo = {"numero": tnum, "nombre": nombre_titulo, "capitulos": [], "articulos": []}
        if isinstance(contenido_titulo, dict) and "Capitulos" in contenido_titulo:
            for nombre_capitulo, contenido_capitulo in contenido_titulo["Capitulos"].items():
                cnum = extraer_capitulo_num(nombre_capitulo) or 0
                lista_art = []
                for k, v in contenido_capitulo.items():
                    anum = extraer_articulo_num(k)
                    if anum is None:
                        continue
                    art = Articulo(numero=anum, titulo_num=tnum, titulo_nombre=nombre_titulo, capitulo_num=cnum, capitulo_nombre=nombre_capitulo, texto=v)
                    articulos[anum] = art
                    lista_art.append(art)
                    tinfo["articulos"].append(art)
                cap = Capitulo(titulo_num=tnum, titulo_nombre=nombre_titulo, numero=cnum, nombre=nombre_capitulo, articulos=sorted(lista_art, key=lambda a: a.numero))
                capitulos[(tnum, cnum)] = cap
                tinfo["capitulos"].append(cap)
        else:
            for k, v in contenido_titulo.items():
                anum = extraer_articulo_num(k)
                if anum is None:
                    continue
                art = Articulo(numero=anum, titulo_num=tnum, titulo_nombre=nombre_titulo, texto=v)
                articulos[anum] = art
                tinfo["articulos"].append(art)
        titulos[nombre_titulo] = tinfo
        titulos_por_num[tnum] = tinfo
    for t in titulos.values():
        if t["capitulos"]:
            t["capitulos"] = sorted(t["capitulos"], key=lambda c: c.numero)
        if t["articulos"]:
            t["articulos"] = sorted(t["articulos"], key=lambda a: a.numero)
    return {"titulos": titulos, "titulos_por_num": titulos_por_num, "capitulos": capitulos, "articulos": articulos, "data": data}

def get_mtime() -> float:
    return CONSTITUCION_PATH.stat().st_mtime

def paginar(lista: List[Any], pagina: int, tamano: int) -> Tuple[List[Any], int]:
    total = len(lista)
    if tamano <= 0:
        tamano = 1
    if pagina <= 0:
        pagina = 1
    inicio = (pagina - 1) * tamano
    fin = inicio + tamano
    return lista[inicio:fin], total

def filtrar_buscar(items: List[Any], q: Optional[str], tipo: str) -> List[Any]:
    res = items
    if q:
        ql = q.lower()
        if tipo == "articulo":
            res = [i for i in res if ql in i.texto.lower() or ql in i.titulo_nombre.lower() or (i.capitulo_nombre and ql in i.capitulo_nombre.lower())]
        elif tipo == "capitulo":
            res = [i for i in res if ql in i.nombre.lower() or ql in i.titulo_nombre.lower()]
        elif tipo == "titulo":
            res = [i for i in res if ql in i["nombre"].lower()]
    return res

def ordenar(items: List[Any], ordenar_por: Optional[str], orden: str, tipo: str) -> List[Any]:
    desc = orden.lower() == "desc"
    if tipo == "articulo":
        keymap = {
            "numero": lambda a: a.numero,
            "longitud": lambda a: len(a.texto),
            "titulo": lambda a: a.titulo_num,
            "capitulo": lambda a: a.capitulo_num or 0,
        }
    elif tipo == "capitulo":
        keymap = {
            "numero": lambda c: c.numero,
            "titulo": lambda c: c.titulo_num,
            "articulos": lambda c: len(c.articulos),
        }
    else:
        keymap = {
            "numero": lambda t: t["numero"],
            "nombre": lambda t: t["nombre"],
            "capitulos": lambda t: len(t["capitulos"]) if t["capitulos"] else 0,
            "articulos": lambda t: len(t["articulos"]) if t["articulos"] else 0,
        }
    k = keymap.get((ordenar_por or "numero").lower(), keymap["numero"])
    return sorted(items, key=k, reverse=desc)

@router.get(
    "/constitucion",
    summary="Contenido completo del JSON",
    tags=["Constitución"],
    description="Devuelve el JSON completo de la Constitución de Panamá.",
    responses={
        200: {"description": "Contenido completo del documento"},
        401: {"description": "Autenticación requerida si se configura como obligatoria"},
    },
)
async def obtener_constitucion(request: Request):
    m = get_mtime()
    data = cargar_json(m)
    return JSONResponse(content=data)

@router.get(
    "/titulos",
    response_model=Paginacion,
    summary="Listar títulos",
    tags=["Títulos"],
    description="Lista los Títulos con soporte de búsqueda, orden y paginación.",
)
async def listar_titulos(q: Optional[str] = Query(None), ordenar_por: Optional[str] = Query("numero"), orden: str = Query("asc"), pagina: int = Query(1, ge=1), tamano_pagina: int = Query(20, ge=1, le=200)):
    m = get_mtime()
    idx = construir_indices(m)
    lista = list(idx["titulos"].values())
    lista = filtrar_buscar(lista, q, "titulo")
    lista = ordenar(lista, ordenar_por, orden, "titulo")
    page_items, total = paginar(lista, pagina, tamano_pagina)
    return Paginacion(total=total, pagina=pagina, tamano_pagina=tamano_pagina, items=page_items)

@router.get(
    "/titulos/{titulo_id}",
    response_model=Titulo,
    summary="Obtener título por identificador",
    tags=["Títulos"],
    description="Obtiene un Título por su número (arábigo o romano).",
    responses={404: {"description": "Título no encontrado"}},
)
async def obtener_titulo(titulo_id: str):
    m = get_mtime()
    idx = construir_indices(m)
    try:
        tnum = int(titulo_id)
    except ValueError:
        r = extraer_romano(f"TÍTULO {titulo_id}")
        tnum = r or 0
    t = idx["titulos_por_num"].get(tnum)
    if not t:
        raise HTTPException(status_code=404, detail="Título no encontrado")
    return Titulo(numero=t["numero"], nombre=t["nombre"], capitulos=t["capitulos"], articulos=t["articulos"])

@router.get(
    "/titulos/{titulo_id}/capitulos",
    response_model=Paginacion,
    summary="Listar capítulos de un título",
    tags=["Capítulos"],
    description="Lista los capítulos del Título indicado con búsqueda, orden y paginación.",
)
async def listar_capitulos_por_titulo(titulo_id: str, q: Optional[str] = Query(None), ordenar_por: Optional[str] = Query("numero"), orden: str = Query("asc"), pagina: int = Query(1, ge=1), tamano_pagina: int = Query(20, ge=1, le=200)):
    m = get_mtime()
    idx = construir_indices(m)
    try:
        tnum = int(titulo_id)
    except ValueError:
        r = extraer_romano(f"TÍTULO {titulo_id}")
        tnum = r or 0
    t = idx["titulos_por_num"].get(tnum)
    if not t:
        raise HTTPException(status_code=404, detail="Título no encontrado")
    lista = t["capitulos"] or []
    lista = filtrar_buscar(lista, q, "capitulo")
    lista = ordenar(lista, ordenar_por, orden, "capitulo")
    page_items, total = paginar(lista, pagina, tamano_pagina)
    return Paginacion(total=total, pagina=pagina, tamano_pagina=tamano_pagina, items=page_items)

@router.get(
    "/titulos/{titulo_id}/capitulos/{capitulo_num}",
    response_model=Capitulo,
    summary="Obtener capítulo de un título",
    tags=["Capítulos"],
    description="Obtiene un Capítulo específico dentro de un Título.",
    responses={404: {"description": "Capítulo no encontrado"}},
)
async def obtener_capitulo_por_titulo(titulo_id: str, capitulo_num: int):
    m = get_mtime()
    idx = construir_indices(m)
    try:
        tnum = int(titulo_id)
    except ValueError:
        r = extraer_romano(f"TÍTULO {titulo_id}")
        tnum = r or 0
    cap = idx["capitulos"].get((tnum, capitulo_num))
    if not cap:
        raise HTTPException(status_code=404, detail="Capítulo no encontrado")
    return cap

@router.get(
    "/capitulos",
    response_model=Paginacion,
    summary="Listar capítulos",
    tags=["Capítulos"],
    description="Lista todos los capítulos con filtros opcionales por Título.",
)
async def listar_capitulos(q: Optional[str] = Query(None), titulo: Optional[str] = Query(None), ordenar_por: Optional[str] = Query("numero"), orden: str = Query("asc"), pagina: int = Query(1, ge=1), tamano_pagina: int = Query(20, ge=1, le=200)):
    m = get_mtime()
    idx = construir_indices(m)
    lista = list(idx["capitulos"].values())
    if titulo:
        try:
            tnum = int(titulo)
        except ValueError:
            r = extraer_romano(f"TÍTULO {titulo}")
            tnum = r or 0
        lista = [c for c in lista if c.titulo_num == tnum]
    lista = filtrar_buscar(lista, q, "capitulo")
    lista = ordenar(lista, ordenar_por, orden, "capitulo")
    page_items, total = paginar(lista, pagina, tamano_pagina)
    return Paginacion(total=total, pagina=pagina, tamano_pagina=tamano_pagina, items=page_items)

@router.get(
    "/articulos",
    response_model=Paginacion,
    summary="Listar artículos",
    tags=["Artículos"],
    description="Lista artículos con búsqueda textual, orden y paginación.",
)
async def listar_articulos(q: Optional[str] = Query(None), ordenar_por: Optional[str] = Query("numero"), orden: str = Query("asc"), pagina: int = Query(1, ge=1), tamano_pagina: int = Query(20, ge=1, le=200)):
    m = get_mtime()
    idx = construir_indices(m)
    lista = list(idx["articulos"].values())
    lista = filtrar_buscar(lista, q, "articulo")
    lista = ordenar(lista, ordenar_por, orden, "articulo")
    page_items, total = paginar(lista, pagina, tamano_pagina)
    return Paginacion(total=total, pagina=pagina, tamano_pagina=tamano_pagina, items=page_items)

@router.get(
    "/articulos/{numero}",
    response_model=Articulo,
    summary="Obtener artículo por número",
    tags=["Artículos"],
    description="Obtiene el contenido y metadatos de un artículo por su número.",
    responses={404: {"description": "Artículo no encontrado"}},
)
async def obtener_articulo(numero: int):
    m = get_mtime()
    idx = construir_indices(m)
    art = idx["articulos"].get(numero)
    if not art:
        raise HTTPException(status_code=404, detail="Artículo no encontrado")
    return art