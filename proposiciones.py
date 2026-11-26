from __future__ import annotations

import itertools
import json
import os
import re
import sys
import textwrap
from pathlib import Path

VERSION = "v7 (Árbol Conjunto con Zoom y Filtros)"
COMANDO_VOLVER = "volver"
ARCHIVO_JSON = Path(__file__).resolve().parent / "proposiciones.json"
MAX_VARIABLES = 10  # Permite evaluar hasta 10 variables atómicas simultáneas

CONECTORES_PALABRA = {
    "y": "∧",
    "o": "∨",
    "entonces": "⇒",
    "si y solo si": "↔",
}
NEGACION = "no"

NOMBRES = {
    "∧": "Conjunción",
    "∨": "Disyunción",
    "Δ": "Disyunción exclusiva",
    "⇒": "Condicional",
    "↔": "Bicondicional",
    "~": "Negación",
}

ORDEN_PRECEDENCIA = ["↔", "⇒", "Δ", "∨", "∧"]
ASOCIATIVOS = {"Δ", "∨", "∧"}

PATRON_CONECTORES = re.compile(r"\b(si\s+y\s+s[oó]lo\s+si|entonces|o|y)\b")
LETRAS = "pqrstuvwxyz"

reglas = {}
indice_proposiciones = {}


def normalizar(texto: str) -> str:
    return re.sub(r"\s+", " ", texto.strip().lower())


def detectar_negacion(proposicion: str) -> tuple[str, bool]:
    patron = rf"\b{NEGACION}\b"
    cantidad = len(re.findall(patron, proposicion))
    limpia = re.sub(patron, "", proposicion)
    limpia = re.sub(r"\s+", " ", limpia).strip()
    return limpia, cantidad % 2 == 1


def nombre_letra(n: int) -> str:
    return LETRAS[n] if n < len(LETRAS) else f"p{n - len(LETRAS) + 1}"


def _envolver(items: list[str], conectores: list[str]) -> str:
    texto = construir_esquema(items, conectores)
    return f"({texto})" if len(items) > 1 else texto


def construir_esquema(items: list[str], conectores: list[str]) -> str:
    if not conectores:
        return items[0]

    for op in ORDEN_PRECEDENCIA:
        if op not in conectores:
            continue
        posiciones = [i for i, c in enumerate(conectores) if c == op]

        if op in ASOCIATIVOS:
            partes, inicio = [], 0
            for i in posiciones:
                partes.append(_envolver(items[inicio:i + 1], conectores[inicio:i]))
                inicio = i + 1
            partes.append(_envolver(items[inicio:], conectores[inicio:]))
            return f" {op} ".join(partes)

        i = posiciones[0]
        izq = _envolver(items[:i + 1], conectores[:i])
        der = _envolver(items[i + 1:], conectores[i + 1:])
        return f"{izq} {op} {der}"

    return items[0]


def interpretar(texto: str) -> dict:
    texto = normalizar(texto)
    advertencias = []

    inicia_si = inicia_o = False
    if re.match(r"si\b(?!\s+y\s+s[oó]lo\s+si)", texto):
        inicia_si = True
        texto = texto[2:].strip()
    elif re.match(r"o\b", texto):
        inicia_o = True
        texto = texto[1:].strip()

    partes = PATRON_CONECTORES.split(texto)
    fragmentos = partes[0::2]
    palabras = [re.sub(r"\s+", " ", w).replace("ó", "o") for w in partes[1::2]]

    proposiciones, negadas, conectores_palabra = [], [], []
    pendiente = None
    for i, fragmento in enumerate(fragmentos):
        limpia, negada = detectar_negacion(fragmento.strip())
        antes = palabras[i - 1] if i > 0 else None

        if not limpia:
            if len(fragmentos) > 1:
                advertencias.append("Hay un conector sin proposición a un lado; se ignoró.")
            if proposiciones and pendiente is None:
                pendiente = antes
            continue

        if proposiciones:
            conectores_palabra.append(pendiente or antes)
        pendiente = None

        proposiciones.append(limpia)
        negadas.append(negada)

    conectores = [CONECTORES_PALABRA[w] for w in conectores_palabra if w in CONECTORES_PALABRA]
    if inicia_o:
        conectores = ["Δ" if c == "∨" else c for c in conectores]

    letras_por_prop, letras = {}, []
    for p in proposiciones:
        if p not in letras_por_prop:
            letras_por_prop[p] = nombre_letra(len(letras_por_prop))
        letras.append(letras_por_prop[p])

    esquema = ""
    if proposiciones:
        items = [("~" if n else "") + letra for letra, n in zip(letras, negadas)]
        esquema = construir_esquema(items, conectores)

    tipos = []
    for c in conectores:
        etiqueta = f"{NOMBRES.get(c, c)} ({c})"
        if etiqueta not in tipos:
            tipos.append(etiqueta)
    if any(negadas):
        tipos.append(f"{NOMBRES['~']} (~)")

    return {
        "proposiciones": proposiciones,
        "negadas": negadas,
        "letras": letras,
        "conectores": conectores,
        "esquema": esquema,
        "tipos": tipos,
        "advertencias": advertencias,
    }


def reconstruir_indice() -> None:
    indice_proposiciones.clear()
    for id_regla in sorted(reglas, key=int):
        r = reglas[id_regla]
        for pos, (p, n) in enumerate(zip(r["proposiciones"], r["negadas"]), start=1):
            indice_proposiciones.setdefault(p, []).append(
                {"regla": id_regla, "posicion": pos, "negada": n}
            )


def guardar_json() -> tuple[bool, str]:
    datos = {
        "version": 1,
        "proposiciones_atomicas": sorted(indice_proposiciones),
        "reglas": reglas,
    }
    temporal = ARCHIVO_JSON.with_name(ARCHIVO_JSON.name + ".tmp")
    try:
        with open(temporal, "w", encoding="utf-8") as f:
            json.dump(datos, f, ensure_ascii=False, indent=2)
        os.replace(temporal, ARCHIVO_JSON)
        return True, ""
    except OSError as error:
        return False, str(error)


def cargar_json() -> tuple[bool, str]:
    reglas.clear()
    indice_proposiciones.clear()
    if not ARCHIVO_JSON.exists():
        return True, ""
    try:
        with open(ARCHIVO_JSON, encoding="utf-8") as f:
            datos = json.load(f)
        for id_regla in sorted(datos["reglas"], key=int):
            r = datos["reglas"][id_regla]
            reglas[str(id_regla)] = {
                "original": str(r["original"]),
                "proposiciones": [str(p) for p in r["proposiciones"]],
                "negadas": [bool(n) for n in r["negadas"]],
                "letras": [str(x) for x in r["letras"]],
                "conectores": [str(c) for c in r["conectores"]],
                "esquema": str(r["esquema"]),
                "tipos": [str(t) for t in r["tipos"]],
            }
    except Exception as error:
        return False, f"Error al cargar JSON: {error}"
    reconstruir_indice()
    return True, ""


def obtener_mapeo_global_proposiciones(ids_reglas: list[str] = None) -> tuple[dict[str, str], dict[str, str]]:
    if ids_reglas is None:
        ids_reglas = list(reglas.keys())

    props_unicas = []
    for id_r in ids_reglas:
        if id_r in reglas:
            for p in reglas[id_r]["proposiciones"]:
                if p not in props_unicas:
                    props_unicas.append(p)

    prop_a_letra = {}
    letra_a_prop = {}
    for i, p in enumerate(props_unicas):
        letra = nombre_letra(i)
        prop_a_letra[p] = letra
        letra_a_prop[letra] = p
    return prop_a_letra, letra_a_prop


def evaluar(valores: list[bool], conectores: list[str]) -> bool:
    if not conectores:
        return valores[0]

    for op in ORDEN_PRECEDENCIA:
        if op not in conectores:
            continue
        posiciones = [i for i, c in enumerate(conectores) if c == op]

        if op in ASOCIATIVOS:
            partes, inicio = [], 0
            for i in posiciones:
                partes.append(evaluar(valores[inicio:i + 1], conectores[inicio:i]))
                inicio = i + 1
            partes.append(evaluar(valores[inicio:], conectores[inicio:]))
            if op == "∧":
                return all(partes)
            if op == "∨":
                return any(partes)
            return sum(partes) == 1

        i = posiciones[0]
        izq = evaluar(valores[:i + 1], conectores[:i])
        der = evaluar(valores[i + 1:], conectores[i + 1:])
        return (not izq) or der if op == "⇒" else izq == der

    return valores[0]


def evaluar_regla_global(regla: dict, asignacion_global: dict, prop_a_letra: dict) -> bool:
    valores = []
    for p, n in zip(regla["proposiciones"], regla["negadas"]):
        letra = prop_a_letra[p]
        val = asignacion_global[letra]
        valores.append((not val) if n else val)
    return evaluar(valores, regla["conectores"])


def evaluar_conjunto_reglas(asignacion_global: dict, prop_a_letra: dict, ids_reglas: list[str] = None) -> bool:
    if ids_reglas is None:
        ids_reglas = list(reglas.keys())
    return all(evaluar_regla_global(reglas[id_r], asignacion_global, prop_a_letra) for id_r in ids_reglas if id_r in reglas)


def esquema_conjunto_reglas(ids_reglas: list[str] = None) -> str:
    if ids_reglas is None:
        ids_reglas = list(reglas.keys())
    if not ids_reglas:
        return ""
    prop_a_letra, _ = obtener_mapeo_global_proposiciones(ids_reglas)
    esquemas = []
    for id_r in ids_reglas:
        if id_r in reglas:
            r = reglas[id_r]
            items = [("~" if n else "") + prop_a_letra[p] for p, n in zip(r["proposiciones"], r["negadas"])]
            esquemas.append(f"({construir_esquema(items, r['conectores'])})")
    return " ∧ ".join(esquemas)


def construir_arbol_conjunto(ids_reglas: list[str] = None, podar: bool = True) -> dict | None:
    if ids_reglas is None:
        ids_reglas = list(reglas.keys())
    if not ids_reglas:
        return None

    prop_a_letra, letra_a_prop = obtener_mapeo_global_proposiciones(ids_reglas)
    variables = list(letra_a_prop.keys())

    def resultados(asignacion: dict, restantes: list[str]) -> set:
        vistos = set()
        for combo in itertools.product([True, False], repeat=len(restantes)):
            full_asig = {**asignacion, **dict(zip(restantes, combo))}
            vistos.add(evaluar_conjunto_reglas(full_asig, prop_a_letra, ids_reglas))
            if len(vistos) == 2:
                break
        return vistos

    def nodo(asignacion: dict) -> dict:
        restantes = [v for v in variables if v not in asignacion]
        vistos = resultados(asignacion, restantes)

        if not restantes or (podar and len(vistos) == 1):
            valor = next(iter(vistos)) if vistos else False
            return {
                "hoja": True,
                "valor": valor,
                "estado": "sat" if valor else "insat",
                "filas": 2 ** len(restantes),
                "asignacion": asignacion.copy(),
            }

        variable = restantes[0]
        verdadero = nodo({**asignacion, variable: True})
        falso = nodo({**asignacion, variable: False})

        if verdadero["estado"] in ("sat", "mixto") or falso["estado"] in ("sat", "mixto"):
            estado = "sat" if (verdadero["estado"] == "sat" and falso["estado"] == "sat") else "mixto"
        else:
            estado = "insat"

        return {
            "hoja": False,
            "var": variable,
            "verdadero": verdadero,
            "falso": falso,
            "estado": estado,
            "asignacion": asignacion.copy(),
        }

    return nodo({})


def obtener_ramificaciones_satisfechas(nodo: dict, camino_actual: list[tuple[str, bool]] = None) -> list[dict]:
    if camino_actual is None:
        camino_actual = []

    if nodo["hoja"]:
        if nodo["valor"]:
            return [{"camino": camino_actual, "filas": nodo["filas"], "asignacion": nodo["asignacion"]}]
        return []

    res = []
    res.extend(obtener_ramificaciones_satisfechas(nodo["verdadero"], camino_actual + [(nodo["var"], True)]))
    res.extend(obtener_ramificaciones_satisfechas(nodo["falso"], camino_actual + [(nodo["var"], False)]))
    return res


def registrar_texto(texto: str) -> dict | None:
    analisis = interpretar(texto)
    if not analisis["proposiciones"]:
        return None

    id_regla = f"{max((int(k) for k in reglas), default=0) + 1:03d}"
    reglas[id_regla] = {
        "original": texto.strip(),
        "proposiciones": analisis["proposiciones"],
        "negadas": analisis["negadas"],
        "letras": analisis["letras"],
        "conectores": analisis["conectores"],
        "esquema": analisis["esquema"],
        "tipos": analisis["tipos"],
    }
    reconstruir_indice()
    guardar_json()

    return {"id": id_regla, "original": texto.strip(), "analisis": analisis}


def eliminar_regla(id_regla: str) -> tuple[bool, str]:
    if id_regla not in reglas:
        return False, "La regla no existe."
    del reglas[id_regla]
    reconstruir_indice()
    return guardar_json()