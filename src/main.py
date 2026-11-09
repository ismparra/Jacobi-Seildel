"""Interfaz gráfica para resolver sistemas A·x = b con Jacobi y Gauss-Seidel.

Solo interfaz: los botones aún no ejecutan la lógica numérica.
"""

import tkinter as tk
from tkinter import ttk

import customtkinter as ctk

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

COLOR_JACOBI = "#3B8ED0"
COLOR_SEIDEL = "#2FA572"
COLOR_ERROR = "#E5534B"
COLOR_WARN = "#E3B341"


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Jacobi y Gauss-Seidel · Sistemas de ecuaciones lineales")
        self.geometry("1280x780")
        self.minsize(1100, 700)
        # CustomTkinter reajusta la ventana al iniciar; maximizar tras el primer ciclo
        self.after(0, lambda: self.state("zoomed"))

        self.equation_rows = []  # lista de CTkEntry, una por ecuación

        self.grid_columnconfigure(0, weight=0, minsize=430)
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
        header = ctk.CTkFrame(self, corner_radius=0, fg_color=("gray85", "gray14"))
        header.grid(row=0, column=0, columnspan=2, sticky="ew")
        ctk.CTkLabel(
            header,
            text="Solución de sistemas de ecuaciones lineales",
            font=ctk.CTkFont(size=22, weight="bold"),
        ).pack(side="left", padx=20, pady=(12, 0))
        ctk.CTkLabel(
            header,
            text="Métodos de Jacobi y Gauss-Seidel",
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
        panel = ctk.CTkScrollableFrame(self, label_text="Datos del problema")
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
            params, text="Aproximación inicial (separada por comas)"
        ).grid(row=2, column=0, columnspan=2, sticky="w")
        self.x0_entry = ctk.CTkEntry(params, placeholder_text="0, 0, 0")
        self.x0_entry.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(2, 0))

        # --- Ecuaciones
        self._section_label(panel, "3. Ecuaciones")
        ctk.CTkLabel(
            panel,
            text="Ejemplo: 4x + y - z = 7   (solo ecuaciones lineales)",
            font=ctk.CTkFont(size=11),
            text_color="gray60",
            anchor="w",
        ).pack(fill="x", padx=8)

        self.equations_frame = ctk.CTkFrame(panel, fg_color="transparent")
        self.equations_frame.pack(fill="x", padx=8, pady=(6, 6))
        self.equations_frame.grid_columnconfigure(1, weight=1)

        tools = ctk.CTkFrame(panel, fg_color="transparent")
        tools.pack(fill="x", padx=8, pady=(0, 14))
        tools.grid_columnconfigure((0, 1), weight=1)
        ctk.CTkButton(
            tools, text="＋ Agregar ecuación", command=self.agregar_ecuacion
        ).grid(row=0, column=0, sticky="ew", padx=(0, 5), pady=(0, 8))
        ctk.CTkButton(
            tools,
            text="－ Quitar última",
            fg_color="gray40",
            hover_color="gray30",
            command=self.quitar_ecuacion,
        ).grid(row=0, column=1, sticky="ew", padx=(5, 0), pady=(0, 8))
        ctk.CTkButton(
            tools,
            text="Cargar ejemplo",
            fg_color="transparent",
            border_width=2,
            text_color=("gray10", "gray90"),
            command=self.cargar_ejemplo,
        ).grid(row=1, column=0, sticky="ew", padx=(0, 5))
        ctk.CTkButton(
            tools,
            text="Limpiar",
            fg_color="transparent",
            border_width=2,
            border_color=COLOR_ERROR,
            text_color=COLOR_ERROR,
            hover_color=("gray80", "gray25"),
            command=self.limpiar,
        ).grid(row=1, column=1, sticky="ew", padx=(5, 0))

        # --- Resolver
        self.resolver_btn = ctk.CTkButton(
            panel,
            text="▶  Resolver",
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

        # Banner de alertas (linealidad, convergencia, errores)
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

        self.tabs = ctk.CTkTabview(panel)
        self.tabs.grid(row=2, column=0, sticky="nsew", padx=12, pady=(0, 12))
        for name in ("Resumen", "Jacobi", "Gauss-Seidel", "Comparación"):
            self.tabs.add(name)

        self._build_summary_tab(self.tabs.tab("Resumen"))
        self.jacobi_tree = self._build_iteration_tab(self.tabs.tab("Jacobi"))
        self.seidel_tree = self._build_iteration_tab(self.tabs.tab("Gauss-Seidel"))
        self._build_comparison_tab(self.tabs.tab("Comparación"))

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

        ctk.CTkLabel(card, text="Solución", text_color="gray60").grid(
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
        tree.heading("x", text="Vector x")
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
        bar = ctk.CTkFrame(self, height=28, corner_radius=0, fg_color=("gray85", "gray14"))
        bar.grid(row=2, column=0, columnspan=2, sticky="ew")
        self.status_label = ctk.CTkLabel(
            bar, text="Listo", font=ctk.CTkFont(size=12), text_color="gray60"
        )
        self.status_label.pack(side="left", padx=16, pady=3)

    # ------------------------------------------------------------- helpers
    @staticmethod
    def _section_label(parent, text):
        ctk.CTkLabel(
            parent, text=text, font=ctk.CTkFont(size=14, weight="bold"), anchor="w"
        ).pack(fill="x", padx=8, pady=(10, 4))

    def _style_treeviews(self):
        dark = ctk.get_appearance_mode() == "Dark"
        bg, fg, head = ("#2b2b2b", "#e6e6e6", "#1f538d") if dark else ("#ffffff", "#1a1a1a", "#3b8ed0")
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
        style.map("Treeview", background=[("selected", "#1f538d")])
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

    # ---------------------------------------------------- filas de ecuación
    def agregar_ecuacion(self, texto=""):
        idx = len(self.equation_rows) + 1
        ctk.CTkLabel(self.equations_frame, text=f"Ec. {idx}", width=44, anchor="w").grid(
            row=idx - 1, column=0, pady=3
        )
        entry = ctk.CTkEntry(self.equations_frame, placeholder_text="a·x + b·y + c·z = d")
        entry.grid(row=idx - 1, column=1, sticky="ew", pady=3)
        if isinstance(texto, str) and texto:
            entry.insert(0, texto)
        self.equation_rows.append(entry)

    def quitar_ecuacion(self):
        if not self.equation_rows:
            return
        self.equation_rows.pop().destroy()
        # el último label de la columna 0 también debe eliminarse
        labels = [w for w in self.equations_frame.grid_slaves(column=0)]
        if labels:
            max(labels, key=lambda w: int(w.grid_info()["row"])).destroy()

    # --------------------------------------------- acciones (sin lógica aún)
    def cargar_ejemplo(self):
        self.limpiar()
        for eq in ("10x + y + z = 12", "2x + 10y + z = 13", "2x + 2y + 10z = 14"):
            self.agregar_ecuacion(eq)
        self.error_entry.insert(0, "0.001")
        self.max_iter_entry.insert(0, "100")
        self.x0_entry.insert(0, "0, 0, 0")
        self._set_status("Ejemplo cargado")

    def limpiar(self):
        for entry in self.equation_rows:
            entry.destroy()
        for w in self.equations_frame.winfo_children():
            w.destroy()
        self.equation_rows.clear()
        for e in (self.error_entry, self.max_iter_entry, self.x0_entry):
            e.delete(0, "end")
        for tree in (self.jacobi_tree, self.seidel_tree, self.compare_tree):
            tree.delete(*tree.get_children())
        for card in (self.jacobi_card, self.seidel_card):
            for key in ("estado", "iter", "tiempo", "error"):
                card[key].configure(text="—")
            card["solucion"].configure(state="normal")
            card["solucion"].delete("1.0", "end")
            card["solucion"].configure(state="disabled")
        self.veredicto.configure(text="Ejecute el modo «Ambos» para comparar los métodos.")
        self.ocultar_alerta()
        self._set_status("Campos limpiados")

    def resolver(self):
        # TODO: validar linealidad, parsear A y b, ejecutar métodos y llenar resultados.
        self._set_status("La lógica de resolución aún no está implementada")



if __name__ == "__main__":
    App().mainloop()
