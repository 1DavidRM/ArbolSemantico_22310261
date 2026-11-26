from __future__ import annotations

import sys

try:
    import tkinter as tk
    from tkinter import font as tkfont
    from tkinter import messagebox, ttk
except ImportError:
    print("Esta instalación de Python no incluye tkinter.")
    sys.exit(1)

import proposiciones as logica

FUENTE = "Segoe UI"
MONO = "Consolas"

BG = "#F6F8FB"
BARRA = "#FFFFFF"
TARJETA = "#FFFFFF"
BORDE = "#E3E8F0"
TEXTO = "#2B3445"
SUAVE = "#7A869A"
ARISTA = "#CBD5E1"

SAT_FONDO, SAT_BORDE, SAT_TEXTO = "#D1FAE5", "#10B981", "#065F46"
INSAT_FONDO, INSAT_BORDE, INSAT_TEXTO = "#FEE2E2", "#EF4444", "#991B1B"
VAR_FONDO, VAR_BORDE, VAR_TEXTO = "#E0E7FF", "#6366F1", "#312E81"
RESALTADO_ARISTA = "#059669"

ESTILOS = {
    "primario": ("#CFDDF7", "#BFD1F3", "#27427A"),
    "peligro": ("#FBE0E0", "#F6CCCC", "#9A3B3B"),
    "pestana": (BARRA, "#EEF2F9", SUAVE),
    "pestana_activa": ("#E3ECFB", "#E3ECFB", "#27427A"),
    "sat": (SAT_FONDO, SAT_FONDO, SAT_TEXTO),
    "insat": (INSAT_FONDO, INSAT_FONDO, INSAT_TEXTO),
}


def rect_redondeado(canvas, x1, y1, x2, y2, r, **opciones):
    puntos = [
        x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r,
        x2, y2 - r, x2, y2, x2 - r, y2, x1 + r, y2,
        x1, y2, x1, y2 - r, x1, y1 + r, x1, y1,
    ]
    return canvas.create_polygon(puntos, smooth=True, **opciones)


class BotonRedondeado(tk.Canvas):
    def __init__(self, master, texto, comando=None, estilo="primario",
                 ancho=None, alto=32, fuente=None):
        self._fuente = fuente or (FUENTE, 9, "bold")
        ancho = ancho or tkfont.Font(font=self._fuente).measure(texto) + 24
        super().__init__(
            master, width=ancho, height=alto, bg=master.cget("bg"),
            highlightthickness=0, bd=0, cursor="hand2" if comando else "arrow",
        )
        self._ancho, self._alto = ancho, alto
        self._texto = texto
        self._comando = comando
        self._estilo = estilo
        self._sobre = False
        self.bind("<Enter>", self._entrar)
        self.bind("<Leave>", self._salir)
        self.bind("<ButtonRelease-1>", self._soltar)
        self._dibujar()

    def set_estilo(self, estilo):
        self._estilo = estilo
        self._dibujar()

    def _dibujar(self):
        fondo, hover, texto = ESTILOS.get(self._estilo, ESTILOS["primario"])
        color = hover if (self._sobre and self._comando) else fondo
        self.delete("all")
        rect_redondeado(self, 1, 1, self._ancho - 1, self._alto - 1, self._alto // 2,
                        fill=color, outline=color)
        self.create_text(self._ancho / 2, self._alto / 2, text=self._texto,
                         fill=texto, font=self._fuente)

    def _entrar(self, _):
        self._sobre = True
        self._dibujar()

    def _salir(self, _):
        self._sobre = False
        self._dibujar()

    def _soltar(self, e):
        if self._comando and 0 <= e.x <= self._ancho and 0 <= e.y <= self._alto:
            self._comando()


def tarjeta(master, **pack):
    marco = tk.Frame(master, bg=TARJETA, highlightthickness=1, highlightbackground=BORDE)
    marco.pack(**pack)
    return marco


class VistaAgregar(tk.Frame):
    def __init__(self, master, app):
        super().__init__(master, bg=BG)
        self.app = app
        entrada = tarjeta(self, fill="x", padx=28, pady=(24, 12))
        tk.Label(entrada, text="Agregar Proposiciones y Reglas", font=(FUENTE, 14, "bold"),
                 bg=TARJETA, fg=TEXTO).pack(anchor="w", padx=22, pady=(18, 2))
        tk.Label(entrada, text="Escribe una regla por línea. Conectores: y, o, o...o, si...entonces, si y solo si, no",
                 font=(FUENTE, 10), bg=TARJETA, fg=SUAVE).pack(anchor="w", padx=22, pady=(0, 10))

        self.entrada = tk.Text(
            entrada, height=5, wrap="word", font=(FUENTE, 11), bg="#FBFCFE",
            fg=TEXTO, insertbackground=TEXTO, relief="flat", padx=12, pady=10,
            highlightthickness=1, highlightbackground=BORDE,
        )
        self.entrada.pack(fill="x", padx=22, pady=(0, 12))
        self.entrada.bind("<Control-Return>", self.guardar)

        fila = tk.Frame(entrada, bg=TARJETA)
        fila.pack(fill="x", padx=22, pady=(0, 18))
        BotonRedondeado(fila, "Guardar Reglas", self.guardar).pack(side="left")

        detalle = tarjeta(self, fill="both", expand=True, padx=28, pady=(0, 24))
        tk.Label(detalle, text="Resultado del Procesamiento", font=(FUENTE, 11, "bold"),
                 bg=TARJETA, fg=TEXTO).pack(anchor="w", padx=22, pady=(14, 6))
        self.salida = tk.Text(detalle, wrap="word", font=(MONO, 10), bg=TARJETA,
                              fg=TEXTO, relief="flat", state="disabled")
        self.salida.pack(fill="both", expand=True, padx=22, pady=(0, 14))

    def al_mostrar(self):
        self.entrada.focus_set()

    def guardar(self, _=None):
        lineas = [l.strip() for l in self.entrada.get("1.0", "end").splitlines() if l.strip()]
        if not lineas:
            return "break"
        guardadas = 0
        for linea in lineas:
            res = logica.registrar_texto(linea)
            if res:
                guardadas += 1
        self.entrada.delete("1.0", "end")
        self.salida.config(state="normal")
        self.salida.delete("1.0", "end")
        self.salida.insert("1.0", f"Se procesaron {len(lineas)} línea(s). Reglas registradas: {guardadas}.\n\nPuedes ir a la pestaña 'Árbol Semántico Conjunto' para visualizar el diagrama completo.")
        self.salida.config(state="disabled")
        return "break"


class VistaProposiciones(tk.Frame):
    def __init__(self, master, app):
        super().__init__(master, bg=BG)
        self.app = app

        cabecera = tk.Frame(self, bg=BG)
        cabecera.pack(fill="x", padx=28, pady=(24, 10))
        tk.Label(cabecera, text="Reglas Almacenadas", font=(FUENTE, 14, "bold"), bg=BG, fg=TEXTO).pack(side="left")

        marco = tarjeta(self, fill="both", expand=True, padx=28, pady=(0, 24))
        self.canvas = tk.Canvas(marco, bg=TARJETA, highlightthickness=0)
        barra = ttk.Scrollbar(marco, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=barra.set)
        barra.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        self.tabla = tk.Frame(self.canvas, bg=TARJETA)
        ventana = self.canvas.create_window((0, 0), window=self.tabla, anchor="nw")
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfigure(ventana, width=e.width))
        self.tabla.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))

    def al_mostrar(self):
        for w in self.tabla.winfo_children():
            w.destroy()

        if not logica.reglas:
            tk.Label(self.tabla, text="No hay reglas almacenadas.", font=(FUENTE, 11), bg=TARJETA, fg=SUAVE, pady=30).pack()
            return

        prop_a_letra, _ = logica.obtener_mapeo_global_proposiciones()

        for id_r, r in logica.reglas.items():
            fila = tk.Frame(self.tabla, bg=TARJETA, highlightthickness=1, highlightbackground=BORDE)
            fila.pack(fill="x", padx=16, pady=8)

            items_globales = [("~" if n else "") + prop_a_letra.get(p, p) for p, n in zip(r["proposiciones"], r["negadas"])]
            esquema_global = logica.construir_esquema(items_globales, r["conectores"])

            info = f"Regla [{id_r}]  ·  Esquema Global: {esquema_global}\nOriginal: {r['original']}"
            tk.Label(fila, text=info, font=(FUENTE, 10, "bold"), bg=TARJETA, fg=TEXTO, justify="left", anchor="w").pack(side="left", padx=12, pady=10)

            btn_elim = BotonRedondeado(fila, "Eliminar", lambda i=id_r: self.eliminar(i), estilo="peligro", alto=28)
            btn_elim.pack(side="right", padx=12, pady=10)

    def eliminar(self, id_r):
        if messagebox.askyesno("Eliminar Regla", f"¿Deseas eliminar la regla {id_r}?"):
            logica.eliminar_regla(id_r)
            self.al_mostrar()


class VistaArbol(tk.Frame):
    BASE_H = 120
    BASE_V = 90
    BASE_R = 20
    BASE_HOJA_W = 100
    BASE_HOJA_H = 42

    def __init__(self, master, app):
        super().__init__(master, bg=BG)
        self.app = app
        self.podar = tk.BooleanVar(value=True)
        self.zoom_level = 1.0
        self.reglas_seleccionadas = {}

        # CONTROLES SUPERIORES
        controles = tk.Frame(self, bg=BG)
        controles.pack(fill="x", padx=28, pady=(16, 6))

        tk.Label(controles, text="Árbol Semántico Unificado", font=(FUENTE, 13, "bold"), bg=BG, fg=TEXTO).pack(side="left")

        btn_zoom_in = BotonRedondeado(controles, "Zoom +", lambda: self.cambiar_zoom(1.2), alto=28)
        btn_zoom_in.pack(side="right", padx=4)
        btn_zoom_out = BotonRedondeado(controles, "Zoom -", lambda: self.cambiar_zoom(0.8), alto=28)
        btn_zoom_out.pack(side="right", padx=4)
        btn_fit = BotonRedondeado(controles, "Ajustar a Pantalla", self.ajustar_a_pantalla, alto=28)
        btn_fit.pack(side="right", padx=4)

        ttk.Checkbutton(controles, text="Podar ramas decididas", variable=self.podar, command=self.dibujar).pack(side="right", padx=12)

        # PANEL CHECKBOXES DE REGLAS
        self.panel_reglas = tarjeta(self, fill="x", padx=28, pady=(2, 6))
        self.f_checks = tk.Frame(self.panel_reglas, bg=TARJETA)
        self.f_checks.pack(fill="x", padx=12, pady=6)

        # PANEL DE DETALLES Y ESQUEMA
        info_frame = tarjeta(self, fill="x", padx=28, pady=(2, 6))

        self.lbl_esquema = tk.Label(info_frame, text="", bg=TARJETA, fg=TEXTO,
                                   font=(FUENTE, 10, "bold"), anchor="w", justify="left")
        self.lbl_esquema.pack(fill="x", padx=14, pady=(6, 2))

        self.lbl_leyenda = tk.Label(info_frame, text="", bg=TARJETA, fg=SUAVE,
                                    font=(FUENTE, 9), anchor="w", justify="left")
        self.lbl_leyenda.pack(fill="x", padx=14, pady=(0, 4))

        self.lbl_ramas = tk.Label(info_frame, text="", bg=TARJETA, fg=SAT_TEXTO,
                                  font=(FUENTE, 9, "bold"), anchor="w", justify="left", wraplength=950)
        self.lbl_ramas.pack(fill="x", padx=14, pady=(0, 6))

        # CANVAS DE DIBUJO
        marco = tarjeta(self, fill="both", expand=True, padx=28, pady=(0, 16))
        marco.rowconfigure(0, weight=1)
        marco.columnconfigure(0, weight=1)

        self.canvas = tk.Canvas(marco, bg=TARJETA, highlightthickness=0)
        sy = ttk.Scrollbar(marco, orient="vertical", command=self.canvas.yview)
        sx = ttk.Scrollbar(marco, orient="horizontal", command=self.canvas.xview)
        self.canvas.configure(xscrollcommand=sx.set, yscrollcommand=sy.set)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        sy.grid(row=0, column=1, sticky="ns")
        sx.grid(row=1, column=0, sticky="ew")

        # NAVEGACIÓN Y ARRASTRE DE LIENZO
        self.canvas.bind("<ButtonPress-1>", lambda e: self.canvas.scan_mark(e.x, e.y))
        self.canvas.bind("<B1-Motion>", lambda e: self.canvas.scan_dragto(e.x, e.y, gain=1))
        self.canvas.bind("<Control-MouseWheel>", self._on_mousewheel_zoom)

    def _on_mousewheel_zoom(self, event):
        if event.delta > 0:
            self.cambiar_zoom(1.15)
        else:
            self.cambiar_zoom(0.85)

    def cambiar_zoom(self, factor):
        self.zoom_level = max(0.2, min(3.0, self.zoom_level * factor))
        self.dibujar()

    def al_mostrar(self):
        for w in self.f_checks.winfo_children():
            w.destroy()

        tk.Label(self.f_checks, text="Reglas a incluir en el árbol:", font=(FUENTE, 9, "bold"),
                 bg=TARJETA, fg=TEXTO).pack(side="left", padx=(0, 10))

        self.reglas_seleccionadas.clear()

        if not logica.reglas:
            tk.Label(self.f_checks, text="(No hay reglas guardadas)", font=(FUENTE, 9),
                     bg=TARJETA, fg=SUAVE).pack(side="left")
            self.dibujar()
            return

        btn_todas = tk.Button(self.f_checks, text="Todas", font=(FUENTE, 8),
                              command=self._marcar_todas, bg=BARRA, relief="solid", bd=1)
        btn_todas.pack(side="left", padx=4)

        for id_r, r in logica.reglas.items():
            var = tk.BooleanVar(value=True)
            self.reglas_seleccionadas[id_r] = var
            cb = ttk.Checkbutton(self.f_checks, text=f"R{id_r} ({r['esquema']})",
                                 variable=var, command=self.dibujar)
            cb.pack(side="left", padx=6)

        self.dibujar()

    def _marcar_todas(self):
        nuevo_valor = not all(v.get() for v in self.reglas_seleccionadas.values())
        for v in self.reglas_seleccionadas.values():
            v.set(nuevo_valor)
        self.dibujar()

    def _obtener_ids_activas(self):
        return [id_r for id_r, var in self.reglas_seleccionadas.items() if var.get()]

    def ajustar_a_pantalla(self):
        ids_activas = self._obtener_ids_activas()
        arbol = logica.construir_arbol_conjunto(ids_activas, podar=self.podar.get())
        if not arbol:
            return

        hojas, niveles = [0], [0]
        self._contar_hojas_y_niveles(arbol, 0, hojas, niveles)

        anchura_total = max(1, hojas[0]) * self.BASE_H
        altura_total = max(1, niveles[0]) * self.BASE_V

        cw = max(self.canvas.winfo_width(), 400)
        ch = max(self.canvas.winfo_height(), 300)

        scale_x = (cw - 120) / anchura_total
        scale_y = (ch - 100) / altura_total

        self.zoom_level = max(0.25, min(1.5, min(scale_x, scale_y)))
        self.dibujar()

    def _contar_hojas_y_niveles(self, nodo, nivel, hojas, niveles):
        niveles[0] = max(niveles[0], nivel)
        if nodo["hoja"]:
            hojas[0] += 1
        else:
            self._contar_hojas_y_niveles(nodo["verdadero"], nivel + 1, hojas, niveles)
            self._contar_hojas_y_niveles(nodo["falso"], nivel + 1, hojas, niveles)

    def dibujar(self, *_):
        c = self.canvas
        c.delete("all")

        ids_activas = self._obtener_ids_activas()

        if not ids_activas:
            self.lbl_esquema.config(text="Selecciona al menos una regla para visualizar su árbol semántico.")
            self.lbl_leyenda.config(text="")
            self.lbl_ramas.config(text="")
            return

        prop_a_letra, _ = logica.obtener_mapeo_global_proposiciones(ids_activas)

        if len(prop_a_letra) > logica.MAX_VARIABLES:
            self.lbl_esquema.config(text="Límite de variables superado.")
            self.lbl_leyenda.config(text=f"Las reglas seleccionadas contienen {len(prop_a_letra)} variables atómicas. El límite soportado es {logica.MAX_VARIABLES}.")
            self.lbl_ramas.config(text="")
            return

        esquema_conjunto = logica.esquema_conjunto_reglas(ids_activas)
        self.lbl_esquema.config(text=f"Esquema Evaluado: {esquema_conjunto}")

        leyenda_vars = "   ·   ".join(f"{letra} = {prop}" for prop, letra in prop_a_letra.items())
        self.lbl_leyenda.config(text=f"Variables globales ({len(prop_a_letra)}): {leyenda_vars}")

        arbol = logica.construir_arbol_conjunto(ids_activas, podar=self.podar.get())
        if not arbol:
            return

        satisfechas = logica.obtener_ramificaciones_satisfechas(arbol)
        if satisfechas:
            esquemas_sat = []
            for item in satisfechas:
                minitermino = " ∧ ".join(f"{'' if val else '~'}{v}" for v, val in item["camino"])
                esquemas_sat.append(f"({minitermino})" if minitermino else "(True)")
            texto_sat = f"✓ Ramas que satisfacen las reglas seleccionadas ({len(satisfechas)}): " + "  ∨  ".join(esquemas_sat)
            self.lbl_ramas.config(text=texto_sat, fg=SAT_TEXTO)
        else:
            self.lbl_ramas.config(text="✗ Ninguna asignación satisface las reglas seleccionadas conjuntamente (Contradicción / Inconsistencia).", fg=INSAT_TEXTO)

        hojas, niveles = [0], [0]
        self._colocar(arbol, 0, hojas, niveles)

        H = self.BASE_H * self.zoom_level
        V = self.BASE_V * self.zoom_level

        ancho_arbol = (hojas[0] - 1) * H
        ancho_canvas = max(c.winfo_width(), 1)
        ox = max(60 * self.zoom_level, (ancho_canvas - ancho_arbol) / 2)
        oy = 40 * self.zoom_level

        self._aristas(arbol, ox, oy)
        self._nodos(arbol, ox, oy)

        c.configure(scrollregion=(
            0, 0,
            max(ox + ancho_arbol + 100 * self.zoom_level, ancho_canvas + 50),
            oy + niveles[0] * V + 120 * self.zoom_level,
        ))

    def _colocar(self, nodo, nivel, hojas, niveles):
        H = self.BASE_H * self.zoom_level
        V = self.BASE_V * self.zoom_level
        niveles[0] = max(niveles[0], nivel)

        if nodo["hoja"]:
            nodo["x"] = hojas[0] * H
            hojas[0] += 1
        else:
            self._colocar(nodo["verdadero"], nivel + 1, hojas, niveles)
            self._colocar(nodo["falso"], nivel + 1, hojas, niveles)
            nodo["x"] = (nodo["verdadero"]["x"] + nodo["falso"]["x"]) / 2
        nodo["y"] = nivel * V

    def _tope(self, nodo):
        return (self.BASE_HOJA_H * self.zoom_level) / 2 if nodo["hoja"] else (self.BASE_R * self.zoom_level)

    def _aristas(self, nodo, ox, oy):
        if nodo["hoja"]:
            return

        R = self.BASE_R * self.zoom_level
        x1, y1 = ox + nodo["x"], oy + nodo["y"] + R

        for clave, etiqueta in (("verdadero", "V"), ("falso", "F")):
            hijo = nodo[clave]
            x2, y2 = ox + hijo["x"], oy + hijo["y"] - self._tope(hijo)

            es_camino_sat = hijo["estado"] in ("sat", "mixto")
            color = RESALTADO_ARISTA if es_camino_sat else (INSAT_BORDE if hijo["estado"] == "insat" else ARISTA)
            grosor = max(1, int(4 * self.zoom_level)) if es_camino_sat else max(1, int(2 * self.zoom_level))

            self.canvas.create_line(x1, y1, x2, y2, fill=color, width=grosor)
            mx, my = (x1 + x2) / 2, (y1 + y2) / 2

            bw = 12 * self.zoom_level
            bh = 9 * self.zoom_level
            rect_redondeado(self.canvas, mx - bw, my - bh, mx + bw, my + bh, max(2, int(8 * self.zoom_level)),
                            fill=TARJETA, outline=color)

            f_size = max(7, int(9 * self.zoom_level))
            self.canvas.create_text(mx, my, text=etiqueta, font=(FUENTE, f_size, "bold"),
                                    fill=SAT_TEXTO if es_camino_sat else INSAT_TEXTO)
            self._aristas(hijo, ox, oy)

    def _nodos(self, nodo, ox, oy):
        x, y = ox + nodo["x"], oy + nodo["y"]
        R = self.BASE_R * self.zoom_level
        HOJA_W = self.BASE_HOJA_W * self.zoom_level
        HOJA_H = self.BASE_HOJA_H * self.zoom_level

        if nodo["hoja"]:
            sat = nodo["estado"] == "sat"
            fondo, borde, texto = ((SAT_FONDO, SAT_BORDE, SAT_TEXTO) if sat
                                   else (INSAT_FONDO, INSAT_BORDE, INSAT_TEXTO))
            w, h = HOJA_W / 2, HOJA_H / 2
            grosor = max(1, int(3 * self.zoom_level)) if sat else 1
            rect_redondeado(self.canvas, x - w, y - h, x + w, y + h, max(3, int(12 * self.zoom_level)),
                            fill=fondo, outline=borde, width=grosor)

            etiqueta = "✓ Satisface" if sat else "✗ No satisface"
            f_size = max(7, int(9 * self.zoom_level))
            self.canvas.create_text(x, y, text=etiqueta, fill=texto, font=(FUENTE, f_size, "bold"))
            return

        es_camino_sat = nodo["estado"] in ("sat", "mixto")
        borde_node = SAT_BORDE if es_camino_sat else VAR_BORDE
        grosor_node = max(1, int(3 * self.zoom_level)) if es_camino_sat else max(1, int(1.5 * self.zoom_level))

        self.canvas.create_oval(x - R, y - R, x + R, y + R,
                                fill=VAR_FONDO, outline=borde_node, width=grosor_node)

        f_size = max(8, int(11 * self.zoom_level))
        self.canvas.create_text(x, y, text=nodo["var"], fill=VAR_TEXTO,
                                font=(FUENTE, f_size, "bold"))

        self._nodos(nodo["verdadero"], ox, oy)
        self._nodos(nodo["falso"], ox, oy)


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Diccionario de Proposiciones - Árbol Semántico Conjunto")
        self.geometry("1120x760")
        self.minsize(860, 560)
        self.configure(bg=BG)

        logica.cargar_json()

        barra = tk.Frame(self, bg=BARRA)
        barra.pack(fill="x")
        tk.Label(barra, text="Diccionario de Proposiciones Lógicas", font=(FUENTE, 12, "bold"),
                 bg=BARRA, fg=TEXTO).pack(side="left", padx=(28, 24), pady=14)
        tk.Frame(self, bg=BORDE, height=1).pack(fill="x")

        self.contenedor = tk.Frame(self, bg=BG)
        self.contenedor.pack(fill="both", expand=True)

        self.vistas = {
            "agregar": VistaAgregar(self.contenedor, self),
            "proposiciones": VistaProposiciones(self.contenedor, self),
            "arbol": VistaArbol(self.contenedor, self),
        }
        self.vista_actual = None
        self.pestanas = {}
        for clave, titulo in (("agregar", "Agregar"),
                              ("proposiciones", "Proposiciones"),
                              ("arbol", "Árbol Semántico Conjunto")):
            boton = BotonRedondeado(barra, titulo, lambda k=clave: self.mostrar(k),
                                    estilo="pestana", alto=34)
            boton.pack(side="left", padx=4, pady=11)
            self.pestanas[clave] = boton

        self.mostrar("arbol")

    def mostrar(self, nombre):
        if self.vista_actual is not None:
            self.vista_actual.pack_forget()
        self.vista_actual = self.vistas[nombre]
        self.vista_actual.pack(fill="both", expand=True)
        for clave, boton in self.pestanas.items():
            boton.set_estilo("pestana_activa" if clave == nombre else "pestana")
        self.vista_actual.al_mostrar()


if __name__ == "__main__":
    App().mainloop()