from __future__ import annotations

import re
import sys
import textwrap

VERSION = "v4 (menú + conectores lógicos)"
COMANDO_VOLVER = "volver"

# --------------------------------------------------------------- conectores
# Palabra del texto -> símbolo del conector lógico (según la tabla de conectores)
CONECTORES_PALABRA = {
    "y": "∧",                # Conjunción:           p y q
    "o": "∨",                # Disyunción:           p o q
    "entonces": "⇒",         # Condicional:          si p entonces q
    "si y solo si": "↔",     # Bicondicional:        p si y solo si q
}
# La disyunción exclusiva (Δ) se detecta con el patrón "o p o q":
# el texto inicia con 'o' y después aparece otra 'o'.
NEGACION = "no"              # Negación:             no p  ->  ~p

NOMBRES = {
    "∧": "Conjunción",
    "∨": "Disyunción",
    "Δ": "Disyunción exclusiva",
    "⇒": "Condicional",
    "↔": "Bicondicional",
    "~": "Negación",
}

# Precedencia de menor a mayor (para decidir dónde van los paréntesis)
ORDEN_PRECEDENCIA = ["↔", "⇒", "Δ", "∨", "∧"]
ASOCIATIVOS = {"Δ", "∨", "∧"}

# Se prueba 'si y solo si' primero para que no se confunda con 'si' ni 'y'
PATRON_CONECTORES = re.compile(r"\b(si\s+y\s+s[oó]lo\s+si|entonces|o|y)\b")

LETRAS = "pqrstuvwxyz"

# ----------------------------------------------------------- almacenamiento
# "001" -> {"original", "proposiciones", "negadas", "letras",
#           "conectores", "esquema", "tipos"}
reglas = {}

# Diccionario de proposiciones atómicas:
# "llueve" -> [{"regla": "001", "posicion": 1, "negada": False}, ...]
indice_proposiciones = {}


# ---------------------------------------------------------------- análisis
def normalizar(texto: str) -> str:
    """Minúsculas, sin espacios al inicio/final y espacios internos simples."""
    return re.sub(r"\s+", " ", texto.strip().lower())


def detectar_negacion(proposicion: str) -> tuple[str, bool]:
    """
    Devuelve (proposición sin 'no', negada).
    Un número impar de 'no' se considera negada (dos 'no' se cancelan).
    """
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
    """
    Arma el esquema respetando la precedencia:
    ∧ (mayor) > ∨ > Δ > ⇒ > ↔ (menor). Agrega paréntesis donde hace falta.
    conectores[i] une items[i] con items[i + 1].
    """
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

        # ⇒ y ↔ no son asociativos: se divide en la primera aparición
        i = posiciones[0]
        izq = _envolver(items[:i + 1], conectores[:i])
        der = _envolver(items[i + 1:], conectores[i + 1:])
        return f"{izq} {op} {der}"

    return items[0]


def interpretar(texto: str) -> dict:
    """
    Analiza el texto y devuelve:
      proposiciones, negadas, letras (arreglos paralelos),
      conectores (entre proposiciones consecutivas), esquema, tipos,
      advertencias.
    """
    texto = normalizar(texto)
    advertencias = []

    # 'si p entonces q'  y  'o p o q' llevan una palabra al inicio
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
                advertencias.append(
                    "Hay un conector sin proposición a un lado; "
                    "se ignoró ese fragmento."
                )
            if proposiciones and pendiente is None:
                pendiente = antes
            continue

        if proposiciones:
            conectores_palabra.append(pendiente or antes)
        pendiente = None

        proposiciones.append(limpia)
        negadas.append(negada)
        if re.search(r"\bsi\b", limpia):
            advertencias.append(
                f"La palabra 'si' dentro de '{limpia}' no se reconoce como "
                "conector (usa 'si ... entonces ...' o 'si y solo si')."
            )

    conectores = [CONECTORES_PALABRA[w] for w in conectores_palabra]
    if inicia_o:
        conectores = ["Δ" if c == "∨" else c for c in conectores]
        if "Δ" not in conectores:
            advertencias.append(
                "El texto inicia con 'o' pero falta el segundo 'o' "
                "(disyunción exclusiva: 'o p o q')."
            )
    if inicia_si and "⇒" not in conectores:
        advertencias.append(
            "El texto inicia con 'si' pero falta 'entonces' (si p entonces q)."
        )

    # Letra de cada proposición (la misma proposición conserva su letra)
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
        etiqueta = f"{NOMBRES[c]} ({c})"
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


# ------------------------------------------------------------ comparadores
def comparar_proposicion(proposicion: str, negada: bool) -> list[dict]:
    """Busca la proposición en las ya almacenadas (misma negación u opuesta)."""
    return [
        {**c, "misma_negacion": c["negada"] == negada}
        for c in indice_proposiciones.get(proposicion, [])
    ]


def comparar_regla(analisis: dict) -> list[str]:
    """ID de las reglas almacenadas idénticas (proposiciones, negaciones y conectores)."""
    return [
        id_regla
        for id_regla, r in reglas.items()
        if r["proposiciones"] == analisis["proposiciones"]
        and r["negadas"] == analisis["negadas"]
        and r["conectores"] == analisis["conectores"]
    ]


# ------------------------------------------------------------ almacenamiento
def generar_id() -> str:
    return f"{len(reglas) + 1:03d}"


def almacenar_regla(id_regla: str, original: str, analisis: dict) -> None:
    reglas[id_regla] = {
        "original": original,
        "proposiciones": analisis["proposiciones"],
        "negadas": analisis["negadas"],
        "letras": analisis["letras"],
        "conectores": analisis["conectores"],
        "esquema": analisis["esquema"],
        "tipos": analisis["tipos"],
    }
    for pos, (p, n) in enumerate(
        zip(analisis["proposiciones"], analisis["negadas"]), start=1
    ):
        indice_proposiciones.setdefault(p, []).append(
            {"regla": id_regla, "posicion": pos, "negada": n}
        )


# ----------------------------------------------------------------- salida
def procesar_texto(texto: str) -> None:
    analisis = interpretar(texto)
    proposiciones = analisis["proposiciones"]
    negadas = analisis["negadas"]

    if not proposiciones:
        print("  No se detectaron proposiciones en el texto.\n")
        return

    # Se compara ANTES de almacenar, para no compararla consigo misma
    reglas_iguales = comparar_regla(analisis)
    coincidencias = [comparar_proposicion(p, n) for p, n in zip(proposiciones, negadas)]

    id_regla = generar_id()
    almacenar_regla(id_regla, texto.strip(), analisis)

    print(f"\n=== Regla {id_regla} almacenada ===")
    print(f"Texto original: {texto.strip()}")
    print(f"Proposiciones:  {proposiciones}")
    print(f"Negadas:        {negadas}")
    print(f"Conectores:     {analisis['conectores']}")
    print(f"Esquema:        {analisis['esquema']}")
    print(f"Tipo(s):        {', '.join(analisis['tipos']) or '(ninguno)'}")

    print("\nDetalle:")
    for i, (p, n, letra, coincide) in enumerate(
        zip(proposiciones, negadas, analisis["letras"], coincidencias), start=1
    ):
        print(f"  P{i} ({letra}): '{p}' -> {'NEGADA' if n else 'afirmada'}")
        if not coincide:
            print("      (proposición nueva)")
        for c in coincide:
            if c["misma_negacion"]:
                print(
                    f"      = igual a la proposición P{c['posicion']} "
                    f"de la regla {c['regla']}"
                )
            else:
                print(
                    f"      ~ mismo enunciado que P{c['posicion']} de la "
                    f"regla {c['regla']}, pero con negación opuesta"
                )

    if reglas_iguales:
        print(f"\n>> La regla completa es IDÉNTICA a: {', '.join(reglas_iguales)}")
    for aviso in analisis["advertencias"]:
        print(f"\n[Advertencia] {aviso}")
    print()


def imprimir_tabla(encabezados: list[str], filas: list[list[list[str]]]) -> None:
    """Cada celda es una lista de líneas."""
    anchos = [len(h) for h in encabezados]
    for fila in filas:
        for j, celda in enumerate(fila):
            for linea in celda:
                anchos[j] = max(anchos[j], len(linea))

    sep = "+" + "+".join("-" * (a + 2) for a in anchos) + "+"

    def linea(celdas: list[str]) -> str:
        return "| " + " | ".join(c.ljust(a) for c, a in zip(celdas, anchos)) + " |"

    print(sep)
    print(linea(encabezados))
    print(sep)
    for fila in filas:
        alto = max(len(c) for c in fila)
        for k in range(alto):
            print(linea([c[k] if k < len(c) else "" for c in fila]))
        print(sep)


def ver_tabla() -> None:
    if not reglas:
        print("\nAún no hay reglas almacenadas.\n")
        return

    filas = []
    for id_regla, r in reglas.items():
        atomos, vistas = [], set()
        for letra, prop in zip(r["letras"], r["proposiciones"]):
            if letra in vistas:
                continue
            vistas.add(letra)
            atomos.extend(
                textwrap.wrap(f"{letra} = {prop}", width=45, subsequent_indent="    ")
            )
        filas.append([[id_regla], [r["esquema"]], r["tipos"] or ["(ninguno)"], atomos])

    print("\n=== Proposiciones atómicas y esquemas ===")
    imprimir_tabla(["Regla", "Esquema", "Conectores", "Proposiciones atómicas"], filas)
    print(f"Reglas almacenadas: {len(reglas)}")
    print(f"Proposiciones atómicas distintas: {len(indice_proposiciones)}\n")


# ------------------------------------------------------------------- menú
def leer(mensaje: str):
    """input() que devuelve None si la entrada se cierra o se interrumpe."""
    try:
        return input(mensaje)
    except (EOFError, KeyboardInterrupt):
        print()
        return None


def modo_agregar() -> None:
    print("\n--- Agregar nuevas proposiciones ---")
    print("Conectores reconocidos: y | o | o ... o | si ... entonces | si y solo si | no")
    print(f"Escribe '{COMANDO_VOLVER}' para regresar al menú.\n")
    while True:
        texto = leer("Texto: ")
        if texto is None or normalizar(texto) == COMANDO_VOLVER:
            return
        if not texto.strip():
            continue
        procesar_texto(texto)


def mostrar_menu() -> None:
    print("========== MENÚ ==========")
    print("1. Agregar nuevas proposiciones")
    print("2. Ver proposiciones atómicas y esquemas")
    print("3. Salir")


def main() -> None:
    # Evita errores de codificación en consolas de Windows
    try:
        sys.stdout.reconfigure(errors="replace")
    except Exception:
        pass

    print(f"proposiciones.py {VERSION}")
    if not sys.stdin.isatty():
        print(
            "AVISO: este entorno no es una terminal interactiva, por lo que "
            "no se pueden escribir textos.\nEjecútalo desde la terminal "
            "(python proposiciones.py)."
        )
    print()

    while True:
        mostrar_menu()
        opcion = leer("Opción: ")
        if opcion is None:
            break
        opcion = normalizar(opcion)
        if opcion == "1":
            modo_agregar()
        elif opcion == "2":
            ver_tabla()
        elif opcion in ("3", "salir"):
            break
        else:
            print("Opción no válida. Elige 1, 2 o 3.\n")
        print()

    print(f"\nReglas almacenadas: {len(reglas)}")
    print(f"Proposiciones atómicas distintas: {len(indice_proposiciones)}")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        import traceback

        traceback.print_exc()
    try:
        input("\nPresiona Enter para cerrar...")
    except (EOFError, KeyboardInterrupt):
        pass