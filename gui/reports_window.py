import tkinter as tk
from tkinter import ttk

from models.report_model import (
    get_revenue_summary,
    get_revenue_by_flight,
    get_revenue_by_route,
    get_flight_load_all,
    get_load_by_class,
    get_passenger_ranking,
    get_crew_workload,
    get_aircraft_util,
)

COLORS = {
    "bg": "#F5F5F0",
    "card": "#FFFFFF",
    "border": "#E0DED8",
    "accent": "#2E6099",
    "text_main": "#1A1A18",
    "text_sub": "#6B6A65",
    "text_light": "#9B9A95",
    "danger": "#B91C1C",
    "warning": "#B45309",
    "success": "#3A7D44",
    "row_even": "#FFFFFF",
    "row_odd": "#F9F8F5",
    "header_bg": "#EFF4FA",
    "kpi_blue": "#EBF3FB",
    "kpi_green": "#EAF3DE",
    "kpi_amber": "#FEF3C7",
    "kpi_red": "#FEE2E2",
    "bar": "#2E6099",
    "bar_light": "#90B8D8",
}
FF = "Helvetica"


class ReportsView(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=COLORS["bg"])
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        self._build()

    def _build(self):
        self._build_header()
        self._build_tabs()

    def _build_header(self):
        hdr = tk.Frame(self, bg=COLORS["bg"])
        hdr.grid(row=0, column=0, sticky="ew", padx=24, pady=(20, 0))
        hdr.columnconfigure(0, weight=1)
        tk.Label(hdr, text="Аналитика",
                 font=(FF, 18, "bold"),
                 bg=COLORS["bg"], fg=COLORS["text_main"]).grid(row=0, column=0, sticky="w")
        tk.Button(hdr, text="Обновить данные",
                  font=(FF, 10), relief="flat",
                  bg=COLORS["border"], fg=COLORS["text_sub"],
                  padx=12, pady=5, cursor="hand2",
                  command=self._refresh).grid(row=0, column=1, sticky="e")

    def _build_tabs(self):
        nb = ttk.Notebook(self)
        nb.grid(row=1, column=0, sticky="nsew", padx=24, pady=12)

        s = ttk.Style()
        s.configure("TNotebook", background=COLORS["bg"], borderwidth=0)
        s.configure("TNotebook.Tab", font=(FF, 10), padding=(14, 6))
        s.map("TNotebook.Tab", background=[("selected", COLORS["card"])])

        self._tab_summary = tk.Frame(nb, bg=COLORS["bg"])
        self._tab_revenue = tk.Frame(nb, bg=COLORS["bg"])
        self._tab_load = tk.Frame(nb, bg=COLORS["bg"])
        self._tab_passengers = tk.Frame(nb, bg=COLORS["bg"])
        self._tab_crew = tk.Frame(nb, bg=COLORS["bg"])
        self._tab_aircraft = tk.Frame(nb, bg=COLORS["bg"])

        nb.add(self._tab_summary, text="Сводка")
        nb.add(self._tab_revenue, text="Выручка")
        nb.add(self._tab_load, text="Загрузка рейсов")
        nb.add(self._tab_passengers, text="Пассажиры")
        nb.add(self._tab_crew, text="Экипаж")
        nb.add(self._tab_aircraft, text="Флот")

        self._nb = nb
        nb.bind("<<NotebookTabChanged>>", self._on_tab_change)
        self._loaded = set()
        self._load_tab("summary")

    def _on_tab_change(self, _):
        names = ["summary", "revenue", "load", "passengers", "crew", "aircraft"]
        idx = self._nb.index(self._nb.select())
        name = names[idx]
        if name not in self._loaded:
            self._load_tab(name)

    def _load_tab(self, name):
        self._loaded.add(name)
        tab = getattr(self, f"_tab_{name}")
        for w in tab.winfo_children():
            w.destroy()
        getattr(self, f"_build_{name}")(tab)

    def _refresh(self):
        self._loaded.clear()
        idx = self._nb.index(self._nb.select())
        names = ["summary", "revenue", "load", "passengers", "crew", "aircraft"]
        self._load_tab(names[idx])

    def _make_card(self, parent, title=None) -> tk.Frame:
        outer = tk.Frame(parent, bg=COLORS["card"],
                         highlightbackground=COLORS["border"],
                         highlightthickness=1)
        if title:
            tk.Label(outer, text=title,
                     font=(FF, 11, "bold"),
                     bg=COLORS["card"], fg=COLORS["text_main"]).pack(
                anchor="w", padx=16, pady=(12, 4))
            tk.Frame(outer, bg=COLORS["border"], height=1).pack(fill="x")
        return outer

    def _make_table(self, parent, columns) -> ttk.Treeview:
        frame = tk.Frame(parent, bg=COLORS["card"])
        frame.pack(fill="both", expand=True)
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)

        tree = ttk.Treeview(frame, columns=[c[0] for c in columns],
                            show="headings", selectmode="none")
        s = ttk.Style()
        s.configure("Treeview",
                    font=(FF, 10), rowheight=30,
                    background=COLORS["row_even"],
                    fieldbackground=COLORS["row_even"],
                    foreground=COLORS["text_main"])
        s.configure("Treeview.Heading",
                    font=(FF, 9, "bold"),
                    background=COLORS["header_bg"],
                    foreground=COLORS["text_sub"],
                    relief="flat")

        tree.tag_configure("odd", background=COLORS["row_odd"])

        for cid, heading, width, anchor in columns:
            tree.heading(cid, text=heading)
            tree.column(cid, width=width, minwidth=40, anchor=anchor)

        vsb = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=vsb.set)
        tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")

        return tree

    def _make_bar_chart(self, parent, data, value_key, label_key, title) -> tk.Frame:
        card = self._make_card(parent, title)
        if not data:
            tk.Label(card, text="Нет данных",
                     font=(FF, 10), bg=COLORS["card"],
                     fg=COLORS["text_light"]).pack(pady=20)
            return card

        max_val = max(r[value_key] for r in data) or 1
        bar_area = tk.Frame(card, bg=COLORS["card"])
        bar_area.pack(fill="both", expand=True, padx=16, pady=10)

        for r in data:
            row = tk.Frame(bar_area, bg=COLORS["card"])
            row.pack(fill="x", pady=3)

            tk.Label(row, text=r[label_key],
                     font=(FF, 9), bg=COLORS["card"],
                     fg=COLORS["text_sub"], anchor="w",
                     width=28).pack(side="left")

            bar_frame = tk.Frame(row, bg=COLORS["border"], height=18)
            bar_frame.pack(side="left", fill="x", expand=True)
            bar_frame.pack_propagate(False)

            pct = r[value_key] / max_val
            bar_inner = tk.Frame(bar_frame, bg=COLORS["bar"], height=18)
            bar_inner.place(x=0, y=0, relwidth=pct, relheight=1)

            val_text = f"{r[value_key]:,.0f} ₽" if "revenue" in value_key or "total" in value_key else f"{r[value_key]}"
            tk.Label(row, text=val_text,
                     font=(FF, 9, "bold"), bg=COLORS["card"],
                     fg=COLORS["text_main"], width=14, anchor="e").pack(side="left", padx=(6, 0))

        return card

    def _build_summary(self, tab):
        tab.columnconfigure((0, 1, 2, 3), weight=1)

        try:
            s = get_revenue_summary()
            kpi = [
                ("Выручка", f"{s['total_revenue']:,.0f} ₽", COLORS["kpi_blue"], COLORS["accent"]),
                ("Бронирований", str(s["total_bookings"]), COLORS["kpi_green"], COLORS["success"]),
                ("Средний чек", f"{s['avg_price']:,.0f} ₽", COLORS["kpi_amber"], COLORS["warning"]),
                ("Отменено", str(s["cancelled_count"]), COLORS["kpi_red"], COLORS["danger"]),
            ]
        except Exception:
            kpi = [
                ("Выручка", "—", COLORS["kpi_blue"], COLORS["accent"]),
                ("Бронирований", "—", COLORS["kpi_green"], COLORS["success"]),
                ("Средний чек", "—", COLORS["kpi_amber"], COLORS["warning"]),
                ("Отменено", "—", COLORS["kpi_red"], COLORS["danger"]),
            ]

        for col, (title, value, bg, fg) in enumerate(kpi):
            card = tk.Frame(tab, bg=bg,
                            highlightbackground=COLORS["border"],
                            highlightthickness=1)
            card.grid(row=0, column=col, sticky="ew",
                      padx=(0, 12) if col < 3 else 0,
                      pady=(16, 12), ipadx=4)
            tk.Label(card, text=title,
                     font=(FF, 9), bg=bg,
                     fg=COLORS["text_sub"]).pack(anchor="w", padx=16, pady=(12, 2))
            tk.Label(card, text=value,
                     font=(FF, 20, "bold"), bg=bg, fg=fg).pack(anchor="w", padx=16, pady=(0, 14))

        bottom = tk.Frame(tab, bg=COLORS["bg"])
        bottom.grid(row=1, column=0, columnspan=4, sticky="nsew", pady=(0, 16))
        bottom.columnconfigure(0, weight=1)
        bottom.columnconfigure(1, weight=1)
        tab.rowconfigure(1, weight=1)

        rev_card = self._make_bar_chart(
            bottom,
            list(get_revenue_by_route()),
            "revenue", "route",
            "Выручка по маршрутам, ₽"
        )
        rev_card.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        load_card = self._make_bar_chart(
            bottom,
            list(get_flight_load_all()),
            "sold", "flight_number",
            "Продано мест по рейсам"
        )
        load_card.grid(row=0, column=1, sticky="nsew")

    def _build_revenue(self, tab):
        tab.columnconfigure(0, weight=1)
        tab.rowconfigure(0, weight=1)

        card = self._make_card(tab, "Выручка по рейсам")
        card.grid(row=0, column=0, sticky="nsew", padx=0, pady=12)
        card.columnconfigure(0, weight=1)
        card.rowconfigure(1, weight=1)

        columns = [
            ("flight", "Рейс", 80, "center"),
            ("route", "Маршрут", 190, "w"),
            ("count", "Бронирований", 110, "center"),
            ("revenue", "Выручка, ₽", 120, "e"),
            ("avg", "Средний чек, ₽", 120, "e"),
            ("max_p", "Макс. цена, ₽", 110, "e"),
            ("min_p", "Мин. цена, ₽", 110, "e"),
        ]
        tree = self._make_table(card, columns)

        for i, r in enumerate(get_revenue_by_flight()):
            tree.insert("", "end",
                        tags=("odd",) if i % 2 else (),
                        values=(
                            r["flight_number"],
                            r["route"],
                            r["bookings_count"],
                            f"{r['revenue']:,.0f}",
                            f"{r['avg_price']:,.0f}",
                            f"{r['max_price']:,.0f}",
                            f"{r['min_price']:,.0f}",
                        ))

    def _build_load(self, tab):
        tab.columnconfigure(0, weight=1)
        tab.rowconfigure(0, weight=1)

        card = self._make_card(tab, "Загрузка рейсов")
        card.grid(row=0, column=0, sticky="nsew", padx=0, pady=12)
        card.columnconfigure(0, weight=1)
        card.rowconfigure(1, weight=1)

        columns = [
            ("flight", "Рейс", 80, "center"),
            ("route", "Маршрут", 200, "w"),
            ("dep", "Вылет", 130, "center"),
            ("capacity", "Мест всего", 90, "center"),
            ("sold", "Продано", 80, "center"),
            ("free", "Свободно", 80, "center"),
            ("load_pct", "Загрузка, %", 90, "center"),
            ("status", "Статус", 110, "center"),
        ]
        tree = self._make_table(card, columns)
        tree.tag_configure("high", foreground=COLORS["success"])
        tree.tag_configure("low", foreground=COLORS["danger"])

        STATUS_RU = {
            "scheduled": "По расписанию",
            "departed": "Вылетел",
            "arrived": "Прибыл",
            "cancelled": "Отменён",
        }

        for i, r in enumerate(get_flight_load_all()):
            pct = r["load_pct"] or 0
            tags = ["odd"] if i % 2 else []
            if pct >= 70:
                tags.append("high")
            elif pct < 30:
                tags.append("low")
            tree.insert("", "end",
                        tags=tuple(tags),
                        values=(
                            r["flight_number"],
                            r["route"],
                            r["departure_time"][:16],
                            r["capacity"],
                            r["sold"],
                            r["free"],
                            f"{pct:.1f}",
                            STATUS_RU.get(r["status"], r["status"]),
                        ))

    def _build_passengers(self, tab):
        tab.columnconfigure(0, weight=1)
        tab.rowconfigure(0, weight=1)

        card = self._make_card(tab, "Рейтинг пассажиров по расходам")
        card.grid(row=0, column=0, sticky="nsew", padx=0, pady=12)
        card.columnconfigure(0, weight=1)
        card.rowconfigure(1, weight=1)

        columns = [
            ("rank", "Место", 60, "center"),
            ("name", "Пассажир", 180, "w"),
            ("email", "Email", 180, "w"),
            ("flights", "Рейсов", 70, "center"),
            ("total", "Итого потрачено, ₽", 160, "e"),
        ]
        tree = self._make_table(card, columns)
        tree.tag_configure("top3", foreground=COLORS["accent"])

        for i, r in enumerate(get_passenger_ranking()):
            tags = ["odd"] if i % 2 else []
            if r["rank"] <= 3:
                tags.append("top3")
            tree.insert("", "end",
                        tags=tuple(tags),
                        values=(
                            f"#{r['rank']}",
                            r["passenger_name"],
                            r["email"],
                            r["flights_count"],
                            f"{r['total_spent']:,.0f}",
                        ))

    def _build_crew(self, tab):
        tab.columnconfigure(0, weight=1)
        tab.rowconfigure(0, weight=1)

        card = self._make_card(tab, "Нагрузка экипажа")
        card.grid(row=0, column=0, sticky="nsew", padx=0, pady=12)
        card.columnconfigure(0, weight=1)
        card.rowconfigure(1, weight=1)

        columns = [
            ("name", "Сотрудник", 180, "w"),
            ("role", "Должность", 150, "w"),
            ("flights", "Рейсов назначено", 130, "center"),
            ("license_exp", "Лицензия до", 110, "center"),
            ("months", "Осталось, мес.", 120, "center"),
        ]
        tree = self._make_table(card, columns)
        tree.tag_configure("warn", foreground=COLORS["warning"])
        tree.tag_configure("crit", foreground=COLORS["danger"])

        ROLE_RU = {
            "captain": "Командир",
            "first_officer": "Второй пилот",
            "flight_attendant": "Бортпроводник",
        }

        for i, r in enumerate(get_crew_workload()):
            months = r["months_left"]
            tags = ["odd"] if i % 2 else []
            if months is not None and months <= 3:
                tags.append("crit")
            elif months is not None and months <= 9:
                tags.append("warn")
            tree.insert("", "end",
                        tags=tuple(tags),
                        values=(
                            r["crew_name"],
                            ROLE_RU.get(r["role"], r["role"]),
                            r["flights_assigned"],
                            r["license_exp"],
                            months if months is not None else "—",
                        ))

    def _build_load(self, tab):
        tab.columnconfigure(0, weight=1)
        tab.rowconfigure(0, weight=3)
        tab.rowconfigure(1, weight=1)

        card = self._make_card(tab, "Загрузка рейсов")
        card.grid(row=0, column=0, sticky="nsew", padx=0, pady=(12, 6))
        card.columnconfigure(0, weight=1)
        card.rowconfigure(1, weight=1)

        columns = [
            ("flight", "Рейс", 80, "center"),
            ("route", "Маршрут", 200, "w"),
            ("dep", "Вылет", 130, "center"),
            ("capacity", "Мест всего", 90, "center"),
            ("sold", "Продано", 80, "center"),
            ("free", "Свободно", 80, "center"),
            ("load_pct", "Загрузка, %", 90, "center"),
            ("status", "Статус", 110, "center"),
        ]
        tree = self._make_table(card, columns)
        tree.tag_configure("high", foreground=COLORS["success"])
        tree.tag_configure("low", foreground=COLORS["danger"])

        STATUS_RU = {
            "scheduled": "По расписанию",
            "departed": "Вылетел",
            "arrived": "Прибыл",
            "cancelled": "Отменён",
        }

        for i, r in enumerate(get_flight_load_all()):
            pct = r["load_pct"] or 0
            tags = ["odd"] if i % 2 else []
            if pct >= 70:
                tags.append("high")
            elif pct < 30:
                tags.append("low")
            tree.insert("", "end",
                        tags=tuple(tags),
                        values=(
                            r["flight_number"],
                            r["route"],
                            r["departure_time"][:16],
                            r["capacity"],
                            r["sold"],
                            r["free"],
                            f"{pct:.1f}",
                            STATUS_RU.get(r["status"], r["status"]),
                        ))

        try:
            CLASS_RU = {"economy": "Эконом", "business": "Бизнес"}
            class_data = []
            for r in get_load_by_class():
                d = dict(r)
                if d.get("class"):
                    d["class"] = CLASS_RU.get(d["class"].lower(), d["class"])
                class_data.append(d)
        except Exception:
            class_data = []

        class_card = self._make_bar_chart(
            tab,
            class_data,
            value_key="count",
            label_key="class",
            title="Продано мест по классам обслуживания"
        )
        class_card.grid(row=1, column=0, sticky="nsew", padx=0, pady=(6, 12))

    def _build_aircraft(self, tab):
        tab.columnconfigure(0, weight=1)
        tab.rowconfigure(0, weight=1)

        card = self._make_card(tab, "Использование воздушного флота")
        card.grid(row=0, column=0, sticky="nsew", padx=0, pady=12)
        card.columnconfigure(0, weight=1)
        card.rowconfigure(1, weight=1)

        columns = [
            ("reg", "Рег. номер", 110, "center"),
            ("model", "Модель", 190, "w"),
            ("capacity", "Вместимость", 100, "center"),
            ("status", "Статус", 110, "center"),
            ("flights", "Рейсов", 80, "center"),
            ("revenue", "Выручка на борт, ₽", 160, "e"),
        ]
        tree = self._make_table(card, columns)
        tree.tag_configure("maintenance", foreground=COLORS["warning"])

        STATUS_RU = {
            "active": "В эксплуатации",
            "maintenance": "ТО",
            "retired": "Списан",
        }

        for i, r in enumerate(get_aircraft_util()):
            tags = ["odd"] if i % 2 else []
            if r["status"] == "maintenance":
                tags.append("maintenance")
            tree.insert("", "end",
                        tags=tuple(tags),
                        values=(
                            r["reg_number"],
                            r["model"],
                            r["capacity"],
                            STATUS_RU.get(r["status"], r["status"]),
                            r["flights_count"],
                            f"{r['total_revenue']:,.0f}",
                        ))