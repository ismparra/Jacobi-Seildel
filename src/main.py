"""Interfaz para resolver circuitos por el método de mallas de Kirchhoff.

El usuario captura fuentes y resistencias; se genera el sistema A·I = V
(ley de voltajes de Kirchhoff) y se resuelve con Jacobi y/o Gauss-Seidel.
"""

from tkinter import ttk

import customtkinter as ctk

import solve

# Paleta Kirchhoff: azul de plano eléctrico, ámbar (corriente) y cian (voltaje)
COLOR_JACOBI = "#F2A900"
COLOR_SEIDEL = "#22C7D6"
COLOR_ERROR = "#E5534B"
COLOR_WARN = "#F2A900"
BG = ("#EAF1F8", "#0A1724")
PANEL = ("#DCE7F2", "#112437")
ACCENT = ("#C98A00", "#F2A900")
ACCENT_HOVER = ("#A87100", "#FFC233")

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")
for _w, _k in [("CTk", {"fg_color": BG}), ("CTkFrame", {"fg_color": PANEL, "top_fg_color": PANEL}),
               ("CTkScrollableFrame", {"label_fg_color": PANEL}),
               ("CTkButton", {"fg_color": ACCENT, "hover_color": ACCENT_HOVER, "text_color": ("white", "#0A1724")}),
               ("CTkSegmentedButton", {"selected_color": ACCENT, "selected_hover_color": ACCENT_HOVER,
                                       "text_color": ("white", "#0A1724")}),
               ("CTkSwitch", {"progress_color": ACCENT}),
               ("CTkEntry", {"border_color": ("#7FA1C2", "#2A4A6B"), "fg_color": ("#FFFFFF", "#0A1724")})]:
    ctk.ThemeManager.theme[_w].update({a: list(b) if isinstance(b, tuple) else b for a, b in _k.items()})

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Leyes de Kirchhoff · Método de mallas con Jacobi y Gauss-Seidel")
        self.geometry("1280x780")
        self.minsize(1100, 700)
        # CustomTkinter reajusta la ventana al iniciar; maximizar tras el primer ciclo
        self.after(0, lambda: self.state("zoomed"))

        self.mesh_rows = []  # (frame, entrada V, entrada R propia)
        self.shared_rows = []  # (frame, malla a, malla b, entrada R)

        self.grid_columnconfigure(0, weight=0, minsize=470)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self._build_header()
        self._build_input_panel()
        self._build_results_panel()
        self._build_status_bar()
        self._style_treeviews()

        self.cargar_ejemplo()

    # ------------------------------------------------------------------ UI
    def _build_header(self):
        header = ctk.CTkFrame(self, corner_radius=0, fg_color=("#C9DAEA", "#0D1E31"))
        header.grid(row=0, column=0, columnspan=2, sticky="ew")
        ctk.CTkLabel(
            header,
            text="⚡ Análisis de circuitos · Leyes de Kirchhoff",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=ACCENT,
        ).pack(side="left", padx=20, pady=(12, 0))
        ctk.CTkLabel(
            header,
            text="Método de mallas resuelto con Jacobi y Gauss-Seidel",
            font=ctk.CTkFont(size=13),
            text_color="gray60",
        ).pack(side="left", padx=10, pady=(16, 0))

        self.theme_switch = ctk.CTkSwitch(
            header, text="Modo oscuro", command=self._toggle_theme
        )
        self.theme_switch.select()
        self.theme_switch.pack(side="right", padx=20)

        # Se incluye un espaciador inferior para que el header respire
        ctk.CTkFrame(header, height=10, fg_color="transparent").pack(side="bottom")

    def _build_input_panel(self):
        panel = ctk.CTkScrollableFrame(self, label_text="Datos del circuito")
        panel.grid(row=1, column=0, sticky="nsew", padx=(16, 8), pady=12)
        panel.grid_columnconfigure(0, weight=1)
        self.input_panel = panel

        # --- Método
        self._section_label(panel, "1. Método")
        self.metodo_var = ctk.StringVar(value="Ambos")
        self.metodo_selector = ctk.CTkSegmentedButton(
            panel,
            values=["Jacobi", "Gauss-Seidel", "Ambos"],
            variable=self.metodo_var,
        )
        self.metodo_selector.pack(fill="x", padx=8, pady=(0, 14))

        # --- Parámetros
        self._section_label(panel, "2. Parámetros")
        params = ctk.CTkFrame(panel, fg_color="transparent")
        params.pack(fill="x", padx=8, pady=(0, 14))
        params.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkLabel(params, text="Error permitido (%)").grid(
            row=0, column=0, sticky="w"
        )
        ctk.CTkLabel(params, text="Máx. iteraciones").grid(
            row=0, column=1, sticky="w", padx=(10, 0)
        )
        self.error_entry = ctk.CTkEntry(params, placeholder_text="0.001")
        self.error_entry.grid(row=1, column=0, sticky="ew", pady=(2, 8))
        self.max_iter_entry = ctk.CTkEntry(params, placeholder_text="100")
        self.max_iter_entry.grid(row=1, column=1, sticky="ew", padx=(10, 0), pady=(2, 8))

        ctk.CTkLabel(
            params, text="Corrientes de malla iniciales, A (separadas por comas)"
        ).grid(row=2, column=0, columnspan=2, sticky="w")
        self.x0_entry = ctk.CTkEntry(params, placeholder_text="0, 0, 0")
        self.x0_entry.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(2, 0))

        # --- Mallas
        self._section_label(panel, "3. Mallas (corriente en sentido horario)")
        ctk.CTkLabel(
            panel,
            text="Voltaje: + si la fuente impulsa la corriente en sentido horario.\n"
            "R propias: resistencias que solo pertenecen a esa malla (ej. 4 + 3).",
            font=ctk.CTkFont(size=11),
            text_color="gray60",
            anchor="w",
            justify="left",
        ).pack(fill="x", padx=8)

        self.meshes_frame = ctk.CTkFrame(panel, fg_color="transparent")
        self.meshes_frame.pack(fill="x", padx=8, pady=(6, 6))
        self.meshes_frame.grid_columnconfigure((1, 2), weight=1)
        ctk.CTkLabel(self.meshes_frame, text="Voltaje (V)", text_color="gray60").grid(row=0, column=1, sticky="w")
        ctk.CTkLabel(self.meshes_frame, text="R propias (Ω)", text_color="gray60").grid(
            row=0, column=2, sticky="w", padx=(6, 0))
        self.meshes_head = self.meshes_frame.winfo_children()

        # --- Resistencias compartidas
        self._section_label(panel, "4. Resistencias compartidas entre mallas")
        self.shared_frame = ctk.CTkFrame(panel, fg_color="transparent")
        self.shared_frame.pack(fill="x", padx=8, pady=(0, 6))
        self.shared_frame.grid_columnconfigure((0, 1, 2), weight=1)
        head = ctk.CTkFrame(self.shared_frame, fg_color="transparent")
        head.pack(fill="x")
        head.grid_columnconfigure((0, 1, 2), weight=1, uniform="c")
        for c, t in enumerate(("Malla a", "Malla b", "R (Ω)")):
            ctk.CTkLabel(head, text=t, text_color="gray60", anchor="w").grid(
                row=0, column=c, sticky="w", padx=(0 if c == 0 else 6, 0))

        tools = ctk.CTkFrame(panel, fg_color="transparent")
        tools.pack(fill="x", padx=8, pady=(0, 14))
        tools.grid_columnconfigure((0, 1), weight=1)
        ctk.CTkButton(tools, text="＋ Agregar malla", command=self.agregar_malla).grid(
            row=0, column=0, sticky="ew", padx=(0, 5), pady=(0, 8))
        ctk.CTkButton(
            tools, text="－ Quitar malla", fg_color="gray40", hover_color="gray30",
            text_color="white", command=self.quitar_malla,
        ).grid(row=0, column=1, sticky="ew", padx=(5, 0), pady=(0, 8))
        ctk.CTkButton(tools, text="＋ Agregar compartida", command=self.agregar_compartida).grid(
            row=1, column=0, sticky="ew", padx=(0, 5), pady=(0, 8))
        ctk.CTkButton(
            tools, text="－ Quitar compartida", fg_color="gray40", hover_color="gray30",
            text_color="white", command=self.quitar_compartida,
        ).grid(row=1, column=1, sticky="ew", padx=(5, 0), pady=(0, 8))
        ctk.CTkButton(
            tools,
            text="Cargar ejemplo",
            fg_color="transparent",
            border_width=2,
            text_color=("gray10", "gray90"),
            command=self.cargar_ejemplo,
        ).grid(row=2, column=0, sticky="ew", padx=(0, 5))
        ctk.CTkButton(
            tools,
            text="Limpiar",
            fg_color="transparent",
            border_width=2,
            border_color=COLOR_ERROR,
            text_color=COLOR_ERROR,
            hover_color=("gray80", "gray25"),
            command=self.limpiar,
        ).grid(row=2, column=1, sticky="ew", padx=(5, 0))

        # --- Resolver
        self.resolver_btn = ctk.CTkButton(
            panel,
            text="▶  Resolver circuito",
            height=44,
            font=ctk.CTkFont(size=16, weight="bold"),
            command=self.resolver,
        )
        self.resolver_btn.pack(fill="x", padx=8, pady=(4, 8))

    def _build_results_panel(self):
        panel = ctk.CTkFrame(self)
        panel.grid(row=1, column=1, sticky="nsew", padx=(8, 16), pady=12)
        panel.grid_columnconfigure(0, weight=1)
        panel.grid_rowconfigure(2, weight=1)

        ctk.CTkLabel(
            panel, text="Resultados", font=ctk.CTkFont(size=16, weight="bold")
        ).grid(row=0, column=0, sticky="w", padx=16, pady=(12, 4))

        # Banner de alertas (datos inválidos, convergencia)
        self.alert_banner = ctk.CTkLabel(
            panel,
            text="",
            anchor="w",
            justify="left",
            corner_radius=8,
            fg_color="transparent",
            wraplength=700,
        )
        self.alert_banner.grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 6))

        self.tabs = ctk.CTkTabview(
            panel, segmented_button_selected_color=ACCENT,
            segmented_button_selected_hover_color=ACCENT_HOVER,
            segmented_button_unselected_color=("#B8CCE0", "#1B3550"),
        )
        self.tabs.grid(row=2, column=0, sticky="nsew", padx=12, pady=(0, 12))
        for name in ("Sistema generado", "Resumen", "Jacobi", "Gauss-Seidel", "Comparación"):
            self.tabs.add(name)

        self._build_system_tab(self.tabs.tab("Sistema generado"))
        self._build_summary_tab(self.tabs.tab("Resumen"))
        self.jacobi_tree = self._build_iteration_tab(self.tabs.tab("Jacobi"))
        self.seidel_tree = self._build_iteration_tab(self.tabs.tab("Gauss-Seidel"))
        self._build_comparison_tab(self.tabs.tab("Comparación"))

    def _build_system_tab(self, tab):
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(0, weight=1)
        self.system_box = ctk.CTkTextbox(tab, font=ctk.CTkFont(family="Consolas", size=14), state="disabled")
        self.system_box.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)

    def _build_summary_tab(self, tab):
        tab.grid_columnconfigure((0, 1), weight=1)
        tab.grid_rowconfigure(0, weight=1)
        self.jacobi_card = self._method_card(tab, "Jacobi", COLOR_JACOBI, 0)
        self.seidel_card = self._method_card(tab, "Gauss-Seidel", COLOR_SEIDEL, 1)

    def _method_card(self, parent, title, color, col):
        card = ctk.CTkFrame(parent, border_width=2, border_color=color)
        card.grid(row=0, column=col, sticky="nsew", padx=8, pady=8)
        card.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            card, text=title, font=ctk.CTkFont(size=18, weight="bold"), text_color=color
        ).grid(row=0, column=0, sticky="w", padx=16, pady=(14, 8))

        labels = {}
        for i, (key, text) in enumerate(
            [("estado", "Estado"), ("iter", "Iteraciones"), ("tiempo", "Tiempo de ejecución"),
             ("error", "Error final (%)")],
            start=1,
        ):
            row = ctk.CTkFrame(card, fg_color="transparent")
            row.grid(row=i, column=0, sticky="ew", padx=16, pady=2)
            ctk.CTkLabel(row, text=text, text_color="gray60").pack(side="left")
            val = ctk.CTkLabel(row, text="—", font=ctk.CTkFont(weight="bold"))
            val.pack(side="right")
            labels[key] = val

        ctk.CTkLabel(card, text="Corrientes de malla", text_color="gray60").grid(
            row=5, column=0, sticky="w", padx=16, pady=(12, 2)
        )
        sol = ctk.CTkTextbox(card, height=150, state="disabled")
        sol.grid(row=6, column=0, sticky="nsew", padx=16, pady=(0, 16))
        card.grid_rowconfigure(6, weight=1)
        labels["solucion"] = sol
        return labels

    def _build_iteration_tab(self, tab):
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(0, weight=1)
        tree = ttk.Treeview(tab, columns=("it", "x", "err"), show="headings")
        tree.heading("it", text="Iteración")
        tree.heading("x", text="Corrientes I (A)")
        tree.heading("err", text="Error relativo aprox. (%)")
        tree.column("it", width=90, anchor="center", stretch=False)
        tree.column("x", width=420, anchor="w")
        tree.column("err", width=200, anchor="center", stretch=False)
        tree.grid(row=0, column=0, sticky="nsew", padx=(4, 0), pady=4)
        sb = ctk.CTkScrollbar(tab, command=tree.yview)
        sb.grid(row=0, column=1, sticky="ns", pady=4)
        tree.configure(yscrollcommand=sb.set)
        return tree

    def _build_comparison_tab(self, tab):
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(1, weight=1)

        self.veredicto = ctk.CTkLabel(
            tab,
            text="Ejecute el modo «Ambos» para comparar los métodos.",
            font=ctk.CTkFont(size=14, weight="bold"),
            anchor="w",
        )
        self.veredicto.grid(row=0, column=0, sticky="ew", padx=8, pady=(8, 4))

        cols = ("metodo", "iter", "tiempo", "error", "converge")
        self.compare_tree = ttk.Treeview(tab, columns=cols, show="headings", height=6)
        for col, text, w in [
            ("metodo", "Método", 160),
            ("iter", "Iteraciones", 110),
            ("tiempo", "Tiempo (ms)", 130),
            ("error", "Error final (%)", 140),
            ("converge", "¿Convergió?", 120),
        ]:
            self.compare_tree.heading(col, text=text)
            self.compare_tree.column(col, width=w, anchor="center")
        self.compare_tree.grid(row=1, column=0, sticky="nsew", padx=8, pady=4)

        ctk.CTkLabel(
            tab,
            text="Misma aproximación inicial y mismo error permitido para ambos métodos.",
            font=ctk.CTkFont(size=11),
            text_color="gray60",
            anchor="w",
        ).grid(row=2, column=0, sticky="ew", padx=8, pady=(0, 8))

    def _build_status_bar(self):
        bar = ctk.CTkFrame(self, height=28, corner_radius=0, fg_color=("#C9DAEA", "#0D1E31"))
        bar.grid(row=2, column=0, columnspan=2, sticky="ew")
        self.status_label = ctk.CTkLabel(
            bar, text="Listo", font=ctk.CTkFont(size=12), text_color="gray60"
        )
        self.status_label.pack(side="left", padx=16, pady=3)

    # ------------------------------------------------------------- helpers
    @staticmethod
    def _section_label(parent, text):
        ctk.CTkLabel(
            parent, text=text, font=ctk.CTkFont(size=14, weight="bold"), anchor="w",
            text_color=ACCENT,
        ).pack(fill="x", padx=8, pady=(10, 4))

    def _style_treeviews(self):
        dark = ctk.get_appearance_mode() == "Dark"
        bg, fg, head = ("#112437", "#e6eef7", "#1B4A78") if dark else ("#ffffff", "#0A1724", "#2A6FB0")
        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "Treeview", background=bg, fieldbackground=bg, foreground=fg,
            rowheight=28, borderwidth=0, font=("Segoe UI", 10),
        )
        style.configure(
            "Treeview.Heading", background=head, foreground="white",
            relief="flat", font=("Segoe UI", 10, "bold"),
        )
        style.map("Treeview", background=[("selected", "#C98A00")], foreground=[("selected", "#0A1724")])
        style.map("Treeview.Heading", background=[("active", head)])

    def _toggle_theme(self):
        ctk.set_appearance_mode("dark" if self.theme_switch.get() else "light")
        self.theme_switch.configure(
            text="Modo oscuro" if self.theme_switch.get() else "Modo claro"
        )
        self._style_treeviews()

    def _set_status(self, text):
        self.status_label.configure(text=text)

    def mostrar_alerta(self, texto, color=COLOR_WARN):
        self.alert_banner.configure(text=texto, fg_color=color, text_color="black")

    def ocultar_alerta(self):
        self.alert_banner.configure(text="", fg_color="transparent")

    # ------------------------------------------------------ filas de captura
    def agregar_malla(self, v="", r=""):
        idx = len(self.mesh_rows) + 1
        frame = ctk.CTkFrame(self.meshes_frame, fg_color="transparent")
        frame.grid(row=idx, column=0, columnspan=3, sticky="ew")
        frame.grid_columnconfigure((1, 2), weight=1)
        ctk.CTkLabel(frame, text=f"Malla {idx}", width=60, anchor="w").grid(row=0, column=0, pady=3)
        ev = ctk.CTkEntry(frame, placeholder_text="10")
        ev.grid(row=0, column=1, sticky="ew", pady=3)
        er = ctk.CTkEntry(frame, placeholder_text="4 + 3")
        er.grid(row=0, column=2, sticky="ew", padx=(6, 0), pady=3)
        ev.insert(0, str(v))
        er.insert(0, str(r))
        self.mesh_rows.append((frame, ev, er))

    def quitar_malla(self):
        if self.mesh_rows:
            self.mesh_rows.pop()[0].destroy()

    def agregar_compartida(self, a="", b="", r=""):
        frame = ctk.CTkFrame(self.shared_frame, fg_color="transparent")
        frame.pack(fill="x")
        frame.grid_columnconfigure((0, 1, 2), weight=1, uniform="c")
        ents = []
        for c, ph in enumerate(("Malla a", "Malla b", "R (Ω)")):
            e = ctk.CTkEntry(frame, placeholder_text=ph)
            e.grid(row=0, column=c, sticky="ew", padx=(0 if c == 0 else 6, 0), pady=3)
            ents.append(e)
        for e, val in zip(ents, (a, b, r)):
            e.insert(0, str(val))
        self.shared_rows.append((frame, *ents))

    def quitar_compartida(self):
        if self.shared_rows:
            self.shared_rows.pop()[0].destroy()

    def _escribir(self, box, texto):
        box.configure(state="normal")
        box.delete("1.0", "end")
        box.insert("1.0", texto)
        box.configure(state="disabled")

    # ----------------------------------------------------------- acciones
    def cargar_ejemplo(self):
        self.limpiar()
        for v, r in ((20, "4"), (0, "3"), (10, "2")):
            self.agregar_malla(v, r)
        for a, b, r in ((1, 2, 5), (2, 3, 4), (1, 3, 2)):
            self.agregar_compartida(a, b, r)
        self.error_entry.insert(0, "0.001")
        self.max_iter_entry.insert(0, "100")
        self.x0_entry.insert(0, "0, 0, 0")
        self._set_status("Ejemplo cargado")

    def limpiar(self):
        while self.mesh_rows:
            self.quitar_malla()
        while self.shared_rows:
            self.quitar_compartida()
        for e in (self.error_entry, self.max_iter_entry, self.x0_entry):
            e.delete(0, "end")
        for tree in (self.jacobi_tree, self.seidel_tree, self.compare_tree):
            tree.delete(*tree.get_children())
        for card in (self.jacobi_card, self.seidel_card):
            for key in ("estado", "iter", "tiempo", "error"):
                card[key].configure(text="—")
            self._escribir(card["solucion"], "")
        self._escribir(self.system_box, "")
        self.veredicto.configure(text="Ejecute el modo «Ambos» para comparar los métodos.")
        self.ocultar_alerta()
        self._set_status("Campos limpiados")

    def resolver(self):
        self.ocultar_alerta()
        try:
            fuentes, propias, comp, tol, max_iter, x0 = solve.leer_datos(
                [(ev.get(), er.get()) for _, ev, er in self.mesh_rows],
                [(ea.get(), eb.get(), er.get()) for _, ea, eb, er in self.shared_rows],
                self.error_entry.get(), self.max_iter_entry.get(), self.x0_entry.get(),
            )
        except ValueError as e:
            self.mostrar_alerta(f"⚠ {e}", COLOR_ERROR)
            self._set_status("Datos inválidos")
            return
        A, b = solve.generar_sistema(fuentes, propias, comp)
        if any(A[i][i] == 0 for i in range(len(b))):
            self.mostrar_alerta("⚠ Una malla tiene resistencia total 0 Ω: el sistema no se puede resolver.", COLOR_ERROR)
            return

        dom = solve.es_diagonal_dominante(A)
        lineas = ["Ley de voltajes de Kirchhoff (corrientes de malla, sentido horario):", ""]
        lineas += solve.ecuaciones_texto(A, b)
        lineas += ["", "Forma matricial  A·I = V:", ""]
        lineas += ["  [ " + "  ".join(f"{a:8.3g}" for a in fila) + f" ]   [ I{i + 1} ] = [ {b[i]:g} ]"
                   for i, fila in enumerate(A)]
        lineas += ["", "Matriz diagonalmente dominante: " + ("sí (convergencia garantizada)" if dom
                                                          else "no (puede o no converger)")]
        self._escribir(self.system_box, "\n".join(lineas))

        corridas = solve.ejecutar(self.metodo_var.get(), A, b, x0, tol, max_iter)
        for nombre, tree, card in (("Jacobi", self.jacobi_tree, self.jacobi_card),
                                   ("Gauss-Seidel", self.seidel_tree, self.seidel_card)):
            tree.delete(*tree.get_children())
            if nombre not in corridas:
                for k in ("estado", "iter", "tiempo", "error"):
                    card[k].configure(text="—")
                self._escribir(card["solucion"], "")
                continue
            hist, conv, ms, _ = corridas[nombre]
            for k, x, err in hist:
                tree.insert("", "end", values=(k, ",  ".join(f"I{i + 1}={v:.6f}" for i, v in enumerate(x)),
                                               f"{err:.6f}"))
            card["estado"].configure(text="✔ Convergió" if conv else "✖ No convergió")
            card["iter"].configure(text=str(len(hist)))
            card["tiempo"].configure(text=f"{ms:.3f} ms")
            card["error"].configure(text=f"{hist[-1][2]:.6g}")
            self._escribir(card["solucion"], "\n".join(f"I{i + 1} = {v:.6f} A" for i, v in enumerate(hist[-1][1])))

        self.compare_tree.delete(*self.compare_tree.get_children())
        for nombre, (hist, conv, ms, _) in corridas.items():
            self.compare_tree.insert("", "end", values=(nombre, len(hist), f"{ms:.3f}", f"{hist[-1][2]:.6g}",
                                                        "Sí" if conv else "No"))
        fallos = [n for n, r in corridas.items() if not r[1]]
        if fallos:
            self.mostrar_alerta(f"⚠ {', '.join(fallos)} no convergió: las iteraciones no se acercan a la solución "
                                f"con este error/máximo de iteraciones. Revise los datos del circuito.")
        self.veredicto.configure(text=solve.veredicto(corridas) if len(corridas) == 2
                                 else "Ejecute el modo «Ambos» para comparar los métodos.")
        self.tabs.set("Resumen")
        self._set_status("Circuito resuelto")


if __name__ == "__main__":
    App().mainloop()
