import tkinter as tk
from tkinter import ttk, messagebox

from models.report_model import get_revenue_summary, get_top_passengers, get_expiring_licenses

COLORS = {
    "bg":           "#F5F5F0",
    "sidebar":      "#1A3A5C",
    "sidebar_hover":"#244D78",
    "sidebar_active":"#2E6099",
    "accent":       "#2E6099",
    "white":        "#FFFFFF",
    "card":         "#FFFFFF",
    "border":       "#E0DED8",
    "text_main":    "#1A1A18",
    "text_sub":     "#6B6A65",
    "text_light":   "#9B9A95",
    "success":      "#3A7D44",
    "warning":      "#B45309",
    "danger":       "#B91C1C",
    "kpi_blue":     "#EBF3FB",
    "kpi_green":    "#EAF3DE",
    "kpi_amber":    "#FEF3C7",
    "kpi_red":      "#FEE2E2",
}

FONT_FAMILY = "Montserrat"

class MainWindow:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("АвиаСистема")
        self.root.geometry("1100x680")
        self.root.minsize(900, 600)
        self.root.configure(bg=COLORS["bg"])

        self._gui: dict[str, tk.Frame] = {}
        self._active_btn = None

        self._build_ui()
        self._show_dashboard()


    def _build_ui(self):
        self.root.columnconfigure(1, weight=1)
        self.root.rowconfigure(0, weight=1)

        self._build_sidebar()
        self._build_content_area()

    def _build_sidebar(self):
        sidebar = tk.Frame(self.root, bg=COLORS["sidebar"], width=210)
        sidebar.grid(row=0, column=0, sticky="ns")
        sidebar.grid_propagate(False)
        sidebar.columnconfigure(0, weight=1)

        logo_frame = tk.Frame(sidebar, bg=COLORS["sidebar"])
        logo_frame.grid(row=0, column=0, sticky="ew", pady=(20, 8))

        tk.Label(
            logo_frame, text="✈", font=(FONT_FAMILY, 28),
            bg=COLORS["sidebar"], fg="#FFFFFF"
        ).pack()
        tk.Label(
            logo_frame, text="АвиаСистема",
            font=(FONT_FAMILY, 13, "bold"),
            bg=COLORS["sidebar"], fg="#FFFFFF"
        ).pack()
        tk.Label(
            logo_frame, text="Управление авиакомпанией",
            font=(FONT_FAMILY, 8),
            bg=COLORS["sidebar"], fg="#8AABCC"
        ).pack(pady=(0, 10))

        tk.Frame(sidebar, bg="#2A5A8A", height=1).grid(
            row=1, column=0, sticky="ew", padx=16, pady=(0, 8)
        )

        # Пункты навигации
        nav_items = [
            ("", "Главная",       self._show_dashboard),
            ("",  "Рейсы",         self._show_flights),
            ("", "Бронирования",  self._show_bookings),
            ("", "Пассажиры",     self._show_passengers),
            ("‍️", "Экипаж",      self._show_crew),
            ("", "Аналитика",     self._show_reports),
        ]

        self._nav_buttons = []
        for i, (icon, label, command) in enumerate(nav_items):
            btn = self._make_nav_btn(sidebar, icon, label, command)
            btn.grid(row=i + 2, column=0, sticky="ew", padx=10, pady=2)
            self._nav_buttons.append(btn)

    def _make_nav_btn(self, parent, icon: str, label: str, command) -> tk.Frame:
        """Создаёт кнопку навигации с эффектом ховера"""
        frame = tk.Frame(parent, bg=COLORS["sidebar"], cursor="hand2")
        frame.columnconfigure(1, weight=1)

        tk.Label(
            frame, text=icon, width=2,
            font=(FONT_FAMILY, 13),
            bg=COLORS["sidebar"], fg="#FFFFFF"
        ).grid(row=0, column=0, padx=(12, 4), pady=10)

        tk.Label(
            frame, text=label, anchor="w",
            font=(FONT_FAMILY, 11),
            bg=COLORS["sidebar"], fg="#FFFFFF"
        ).grid(row=0, column=1, sticky="ew", pady=10)

        def on_enter(_):
            if frame != self._active_btn:
                frame.configure(bg=COLORS["sidebar_hover"])
                for w in frame.winfo_children():
                    w.configure(bg=COLORS["sidebar_hover"])

        def on_leave(_):
            if frame != self._active_btn:
                frame.configure(bg=COLORS["sidebar"])
                for w in frame.winfo_children():
                    w.configure(bg=COLORS["sidebar"])

        def on_click(_):
            self._set_active_btn(frame)
            command()

        for widget in [frame] + list(frame.winfo_children()):
            widget.bind("<Enter>", on_enter)
            widget.bind("<Leave>", on_leave)
            widget.bind("<Button-1>", on_click)

        return frame

    def _set_active_btn(self, btn_frame: tk.Frame):
        """Подсвечивает активный пункт меню."""
        if self._active_btn:
            self._active_btn.configure(bg=COLORS["sidebar"])
            for w in self._active_btn.winfo_children():
                w.configure(bg=COLORS["sidebar"])

        btn_frame.configure(bg=COLORS["sidebar_active"])
        for w in btn_frame.winfo_children():
            w.configure(bg=COLORS["sidebar_active"])

        self._active_btn = btn_frame

    def _build_content_area(self):
        self.content = tk.Frame(self.root, bg=COLORS["bg"])
        self.content.grid(row=0, column=1, sticky="nsew")
        self.content.columnconfigure(0, weight=1)
        self.content.rowconfigure(0, weight=1)

    def _clear_content(self):
        for w in self.content.winfo_children():
            w.destroy()

    def _show_dashboard(self):
        self._set_active_btn(self._nav_buttons[0])
        self._clear_content()
        DashboardView(self.content).grid(row=0, column=0, sticky="nsew")

    def _show_flights(self):
        self._set_active_btn(self._nav_buttons[1])
        self._clear_content()
        from gui.flights_view import FlightsView
        FlightsView(self.content).grid(row=0, column=0, sticky="nsew")

    def _show_bookings(self):
        self._set_active_btn(self._nav_buttons[2])
        self._clear_content()
        from gui.bookings_view import BookingsView
        BookingsView(self.content).grid(row=0, column=0, sticky="nsew")

    def _show_passengers(self):
        self._set_active_btn(self._nav_buttons[3])
        self._clear_content()
        from gui.passengers_view import PassengersView
        PassengersView(self.content).grid(row=0, column=0, sticky="nsew")

    def _show_crew(self):
        self._set_active_btn(self._nav_buttons[4])
        self._clear_content()
        from gui.crew_view import CrewView
        CrewView(self.content).grid(row=0, column=0, sticky="nsew")

    def _show_reports(self):
        self._set_active_btn(self._nav_buttons[5])
        self._clear_content()
        from gui.reports_view import ReportsView
        ReportsView(self.content).grid(row=0, column=0, sticky="nsew")

class DashboardView(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=COLORS["bg"])
        self.columnconfigure(0, weight=1)
        self._build()

    def _build(self):
        header = tk.Frame(self, bg=COLORS["bg"])
        header.grid(row=0, column=0, sticky="ew", padx=24, pady=(20, 4))

        tk.Label(
            header, text="Главная панель",
            font=(FONT_FAMILY, 18, "bold"),
            bg=COLORS["bg"], fg=COLORS["text_main"]
        ).pack(side="left")

        tk.Label(
            header, text="Авиакомпания · Июнь 2025",
            font=(FONT_FAMILY, 10),
            bg=COLORS["bg"], fg=COLORS["text_sub"]
        ).pack(side="right", anchor="s", pady=4)

        try:
            summary = get_revenue_summary()
            kpi_data = [
                ("💰 Выручка", f"{summary['total_revenue']:,.0f} Р", COLORS["kpi_blue"],  COLORS["accent"]),
                ("🎫 Бронирований", str(summary["total_bookings"]), COLORS["kpi_green"], COLORS["success"]),
                ("📊 Средний чек", f"{summary['avg_price']:,.0f} ₽", COLORS["kpi_amber"], COLORS["warning"]),
                ("❌ Отменено", str(summary["cancelled_count"]), COLORS["kpi_red"],   COLORS["danger"]),
            ]
        except Exception:
            kpi_data = [
                ("💰 Выручка",      "-", COLORS["kpi_blue"],  COLORS["accent"]),
                ("🎫 Бронирований", "-", COLORS["kpi_green"], COLORS["success"]),
                ("📊 Средний чек",  "-", COLORS["kpi_amber"], COLORS["warning"]),
                ("❌ Отменено",     "-", COLORS["kpi_red"],   COLORS["danger"]),
            ]

        kpi_row = tk.Frame(self, bg=COLORS["bg"])
        kpi_row.grid(row=1, column=0, sticky="ew", padx=24, pady=(8, 0))
        kpi_row.columnconfigure((0, 1, 2, 3), weight=1)

        for col, (title, value, bg, fg) in enumerate(kpi_data):
            self._kpi_card(kpi_row, title, value, bg, fg).grid(
                row=0, column=col, sticky="ew", padx=(0, 12) if col < 3 else 0
            )

        bottom = tk.Frame(self, bg=COLORS["bg"])
        bottom.grid(row=2, column=0, sticky="nsew", padx=24, pady=16)
        bottom.columnconfigure(0, weight=3)
        bottom.columnconfigure(1, weight=2)
        self.rowconfigure(2, weight=1)

        self._top_passengers_card(bottom).grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        self._warnings_card(bottom).grid(row=0, column=1, sticky="nsew")

    def _kpi_card(self, parent, title: str, value: str, bg: str, fg: str) -> tk.Frame:
        card = tk.Frame(parent, bg=bg, relief="flat", bd=0)
        card.configure(highlightbackground=COLORS["border"], highlightthickness=1)

        tk.Label(
            card, text=title,
            font=(FONT_FAMILY, 9),
            bg=bg, fg=COLORS["text_sub"]
        ).pack(anchor="w", padx=14, pady=(12, 2))

        tk.Label(
            card, text=value,
            font=(FONT_FAMILY, 22, "bold"),
            bg=bg, fg=fg
        ).pack(anchor="w", padx=14, pady=(0, 14))

        return card

    def _top_passengers_card(self, parent) -> tk.Frame:
        card = tk.Frame(parent, bg=COLORS["card"])
        card.configure(highlightbackground=COLORS["border"], highlightthickness=1)
        card.columnconfigure(0, weight=1)

        tk.Label(
            card, text="🏆  Топ пассажиры по расходам",
            font=(FONT_FAMILY, 11, "bold"),
            bg=COLORS["card"], fg=COLORS["text_main"]
        ).grid(row=0, column=0, sticky="w", padx=16, pady=(14, 8))

        tk.Frame(card, bg=COLORS["border"], height=1).grid(
            row=1, column=0, sticky="ew"
        )

        # Заголовки
        hdr = tk.Frame(card, bg=COLORS["bg"])
        hdr.grid(row=2, column=0, sticky="ew")
        hdr.columnconfigure(1, weight=1)
        for col, (text, w) in enumerate([("#", 3), ("Пассажир", 0), ("Рейсов", 6), ("Сумма", 12)]):
            tk.Label(
                hdr, text=text, width=w, anchor="w",
                font=(FONT_FAMILY, 9), bg=COLORS["bg"], fg=COLORS["text_light"]
            ).grid(row=0, column=col, padx=(14 if col == 0 else 4, 4), pady=6, sticky="w")

        # Данные
        try:
            passengers = get_top_passengers(6)
        except Exception:
            passengers = []

        for i, p in enumerate(passengers):
            row_bg = COLORS["card"] if i % 2 == 0 else COLORS["bg"]
            row_frame = tk.Frame(card, bg=row_bg)
            row_frame.grid(row=i + 3, column=0, sticky="ew")
            row_frame.columnconfigure(1, weight=1)

            cells = [
                (f"#{i+1}", 3, "w"),
                (p["passenger_name"], 0, "w"),
                (str(p["flights_count"]), 6, "center"),
                (f"{p['total_spent']:,.0f} ₽", 12, "e"),
            ]
            for col, (text, w, anchor) in enumerate(cells):
                tk.Label(
                    row_frame, text=text, width=w, anchor=anchor,
                    font=(FONT_FAMILY, 10), bg=row_bg, fg=COLORS["text_main"]
                ).grid(row=0, column=col, padx=(14 if col == 0 else 4, 4), pady=7, sticky="ew")

        return card


    def _warnings_card(self, parent) -> tk.Frame:
        card = tk.Frame(parent, bg=COLORS["card"])
        card.configure(highlightbackground=COLORS["border"], highlightthickness=1)
        card.columnconfigure(0, weight=1)

        tk.Label(
            card, text="⚠️  Истекающие лицензии",
            font=(FONT_FAMILY, 11, "bold"),
            bg=COLORS["card"], fg=COLORS["text_main"]
        ).grid(row=0, column=0, sticky="w", padx=16, pady=(14, 8))

        tk.Frame(card, bg=COLORS["border"], height=1).grid(
            row=1, column=0, sticky="ew"
        )

        try:
            expiring = get_expiring_licenses(18)
        except Exception:
            expiring = []

        if not expiring:
            tk.Label(
                card, text="✅  Все лицензии в порядке",
                font=(FONT_FAMILY, 10),
                bg=COLORS["card"], fg=COLORS["success"]
            ).grid(row=2, column=0, padx=16, pady=16)
            return card

        for i, member in enumerate(expiring):
            months = member["months_left"]
            # Цвет по срочности
            if months <= 3:
                color = COLORS["danger"]
                icon = "🔴"
            elif months <= 9:
                color = COLORS["warning"]
                icon = "🟡"
            else:
                color = COLORS["text_sub"]
                icon = "🟢"

            row_bg = COLORS["card"] if i % 2 == 0 else COLORS["bg"]
            row_frame = tk.Frame(card, bg=row_bg)
            row_frame.grid(row=i + 2, column=0, sticky="ew")
            row_frame.columnconfigure(1, weight=1)

            tk.Label(
                row_frame, text=icon,
                font=(FONT_FAMILY, 10),
                bg=row_bg
            ).grid(row=0, column=0, padx=(12, 4), pady=8)

            info_frame = tk.Frame(row_frame, bg=row_bg)
            info_frame.grid(row=0, column=1, sticky="ew", pady=6)

            tk.Label(
                info_frame, text=member["crew_name"],
                font=(FONT_FAMILY, 10, "bold"),
                bg=row_bg, fg=COLORS["text_main"], anchor="w"
            ).pack(anchor="w")

            tk.Label(
                info_frame,
                text=f"{member['license_num']}  ·  до {member['license_exp']}",
                font=(FONT_FAMILY, 8),
                bg=row_bg, fg=COLORS["text_sub"], anchor="w"
            ).pack(anchor="w")

            tk.Label(
                row_frame, text=f"{months} мес.",
                font=(FONT_FAMILY, 10, "bold"),
                bg=row_bg, fg=color
            ).grid(row=0, column=2, padx=12)

        return card
