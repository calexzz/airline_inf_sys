import tkinter as tk
from tkinter import ttk, messagebox

from models.flight_model import (
    get_all_flights, search_flights,
    add_flight, update_flight_status, delete_flight,
    get_all_airports, get_all_aircrafts,
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
    "row_even": "#FFFFFF",
    "row_odd": "#F9F8F5",
    "header_bg": "#EFF4FA",
}
FF = "Montserrat"

STATUS_RU = {
    "scheduled": "По расписанию",
    "departed": "Вылетел",
    "arrived": "Прибыл",
    "cancelled": "Отменён",
}


class FlightsView(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=COLORS["bg"])
        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)
        self._build()
        self._load()

    def _build(self):
        self._build_header()
        self._build_toolbar()
        self._build_table()
        self._build_statusbar()

    def _build_header(self):
        row = tk.Frame(self, bg=COLORS["bg"])
        row.grid(row=0, column=0, sticky="ew", padx=24, pady=(20, 0))
        row.columnconfigure(0, weight=1)
        tk.Label(row, text="Расписание рейсов",
                 font=(FF, 18, "bold"),
                 bg=COLORS["bg"], fg=COLORS["text_main"]).grid(row=0, column=0, sticky="w")
        tk.Button(row, text="Добавить рейс",
                  font=(FF, 10), bg=COLORS["accent"], fg="white",
                  relief="flat", padx=14, pady=6, cursor="hand2",
                  command=self._on_add).grid(row=0, column=1, sticky="e")

    def _build_toolbar(self):
        row = tk.Frame(self, bg=COLORS["bg"])
        row.grid(row=1, column=0, sticky="ew", padx=24, pady=10)
        tk.Label(row, text="Поиск:",
                 font=(FF, 10), bg=COLORS["bg"],
                 fg=COLORS["text_sub"]).pack(side="left")
        self._q = tk.StringVar()
        entry = tk.Entry(row, textvariable=self._q,
                         font=(FF, 11), width=30, relief="flat",
                         bg=COLORS["card"], fg=COLORS["text_main"],
                         highlightbackground=COLORS["border"],
                         highlightthickness=1)
        entry.pack(side="left", padx=(8, 0), ipady=5, ipadx=6)
        entry.bind("<KeyRelease>", lambda _: self._on_search())
        tk.Label(row, text="по номеру рейса или городу",
                 font=(FF, 9), bg=COLORS["bg"],
                 fg=COLORS["text_light"]).pack(side="left", padx=10)
        tk.Button(row, text="Обновить",
                  font=(FF, 9), relief="flat",
                  bg=COLORS["border"], fg=COLORS["text_sub"],
                  padx=10, pady=4, cursor="hand2",
                  command=self._load).pack(side="right")

    def _build_table(self):
        card = tk.Frame(self, bg=COLORS["card"],
                        highlightbackground=COLORS["border"],
                        highlightthickness=1)
        card.grid(row=2, column=0, sticky="nsew", padx=24)
        card.columnconfigure(0, weight=1)
        card.rowconfigure(0, weight=1)

        columns = ("num", "route", "dep", "arr", "price", "aircraft", "status")
        self._tree = ttk.Treeview(card, columns=columns,
                                  show="headings", selectmode="browse")

        col_cfg = [
            ("num", "Рейс", 80, "center"),
            ("route", "Маршрут", 220, "w"),
            ("dep", "Вылет", 130, "center"),
            ("arr", "Прилёт", 130, "center"),
            ("price", "Цена, ₽", 100, "e"),
            ("aircraft", "Воздушное судно", 190, "w"),
            ("status", "Статус", 120, "center"),
        ]
        for cid, heading, width, anchor in col_cfg:
            self._tree.heading(cid, text=heading,
                               command=lambda c=cid: self._sort_by(c))
            self._tree.column(cid, width=width, minwidth=50, anchor=anchor)

        s = ttk.Style()
        s.configure("Treeview",
                    font=(FF, 10), rowheight=34,
                    background=COLORS["row_even"],
                    fieldbackground=COLORS["row_even"],
                    foreground=COLORS["text_main"])
        s.configure("Treeview.Heading",
                    font=(FF, 9, "bold"),
                    background=COLORS["header_bg"],
                    foreground=COLORS["text_sub"],
                    relief="flat")
        s.map("Treeview", background=[("selected", "#D0E4F5")])
        self._tree.tag_configure("odd", background=COLORS["row_odd"])

        vsb = ttk.Scrollbar(card, orient="vertical", command=self._tree.yview)
        self._tree.configure(yscrollcommand=vsb.set)
        self._tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")

        self._ctx = tk.Menu(self, tearoff=0)
        self._ctx.add_command(label="Сменить статус", command=self._on_change_status)
        self._ctx.add_separator()
        self._ctx.add_command(label="Удалить рейс", command=self._on_delete)
        self._tree.bind("<Button-3>", self._show_ctx)
        self._tree.bind("<Button-2>", self._show_ctx)

    def _build_statusbar(self):
        self._status = tk.StringVar()
        tk.Label(self, textvariable=self._status,
                 font=(FF, 9), bg=COLORS["bg"],
                 fg=COLORS["text_sub"]).grid(row=3, column=0, sticky="w", padx=26, pady=(4, 10))

    def _load(self, rows=None):
        self._tree.delete(*self._tree.get_children())
        data = rows if rows is not None else get_all_flights()
        for i, f in enumerate(data):
            self._tree.insert(
                "", "end",
                iid=str(f["flight_id"]),
                tags=("odd",) if i % 2 else (),
                values=(
                    f["flight_number"],
                    f"{f['origin_city']} — {f['dest_city']}",
                    f["departure_time"][:16],
                    f["arrival_time"][:16],
                    f"{f['base_price']:,.0f}",
                    f"{f['aircraft_model']}  {f['aircraft_reg']}",
                    STATUS_RU.get(f["status"], f["status"]),
                )
            )
        self._status.set(f"Рейсов: {len(data)}")

    def _on_search(self):
        q = self._q.get().strip()
        self._load(search_flights(q) if q else None)

    def _sort_by(self, col):
        rows = [(self._tree.set(k, col), k) for k in self._tree.get_children("")]
        for idx, (_, k) in enumerate(sorted(rows)):
            self._tree.move(k, "", idx)

    def _show_ctx(self, event):
        iid = self._tree.identify_row(event.y)
        if not iid:
            return
        self._tree.selection_set(iid)
        self._tree.focus_set()
        try:
            self._ctx.tk_popup(event.x_root, event.y_root)
        finally:
            self._ctx.grab_release()

    def _selected_id(self):
        sel = self._tree.selection()
        return int(sel[0]) if sel else None

    def _on_change_status(self):
        fid = self._selected_id()
        if not fid:
            return
        dlg = _StatusDialog(self)
        self.wait_window(dlg)
        if dlg.result:
            try:
                update_flight_status(fid, dlg.result)
                self._load()
            except ValueError as e:
                messagebox.showerror("Ошибка", str(e), parent=self)

    def _on_delete(self):
        fid = self._selected_id()
        if not fid:
            return
        if not messagebox.askyesno("Удаление", "Удалить выбранный рейс?", parent=self):
            return
        try:
            delete_flight(fid)
            self._load()
        except ValueError as e:
            messagebox.showerror("Ошибка", str(e), parent=self)

    def _on_add(self):
        dlg = _AddFlightDialog(self)
        self.wait_window(dlg)
        if dlg.result:
            try:
                add_flight(**dlg.result)
                self._load()
                messagebox.showinfo("Готово", "Рейс добавлен.", parent=self)
            except ValueError as e:
                messagebox.showerror("Ошибка", str(e), parent=self)


class _StatusDialog(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Сменить статус рейса")
        self.resizable(False, False)
        self.grab_set()
        self.result = None
        self._build()

    def _build(self):
        tk.Label(self, text="Выберите новый статус:",
                 font=(FF, 11)).pack(padx=24, pady=(18, 10))
        self._var = tk.StringVar(value="scheduled")
        for key, label in STATUS_RU.items():
            tk.Radiobutton(self, text=label, variable=self._var,
                           value=key, font=(FF, 10)).pack(anchor="w", padx=36, pady=2)
        bf = tk.Frame(self)
        bf.pack(pady=16)
        tk.Button(bf, text="Применить",
                  font=(FF, 10), bg=COLORS["accent"], fg="white",
                  relief="flat", padx=14,
                  command=self._ok).pack(side="left", padx=6)
        tk.Button(bf, text="Отмена",
                  font=(FF, 10), relief="flat", padx=14,
                  command=self.destroy).pack(side="left")

    def _ok(self):
        self.result = self._var.get()
        self.destroy()


class _AddFlightDialog(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Новый рейс")
        self.resizable(False, False)
        self.grab_set()
        self.result = None
        airports = get_all_airports()
        aircrafts = get_all_aircrafts()
        self._ap = {f"{a['city']} ({a['iata_code']})": a["iata_code"] for a in airports}
        self._ac = {f"{a['model']} — {a['reg_number']}": a["reg_number"] for a in aircrafts}
        self._build()

    def _build(self):
        tk.Label(self, text="Новый рейс",
                 font=(FF, 13, "bold"),
                 fg=COLORS["text_main"]).grid(row=0, column=0, columnspan=2,
                                              sticky="w", padx=20, pady=(16, 12))
        tk.Frame(self, bg=COLORS["border"], height=1).grid(
            row=1, column=0, columnspan=2, sticky="ew", padx=20)

        self._vars = {}
        fields = [
            ("flight_number", "Номер рейса", "entry", None),
            ("origin_iata", "Откуда", "combo", list(self._ap)),
            ("dest_iata", "Куда", "combo", list(self._ap)),
            ("aircraft_reg", "Воздушное судно", "combo", list(self._ac)),
            ("departure_time", "Вылет", "entry", "2025-06-01 06:00:00"),
            ("arrival_time", "Прилёт", "entry", "2025-06-01 08:00:00"),
            ("base_price", "Базовая цена, ₽", "entry", ""),
        ]

        for i, (key, label, kind, default) in enumerate(fields):
            tk.Label(self, text=label,
                     font=(FF, 10), anchor="w",
                     fg=COLORS["text_sub"]).grid(row=i + 2, column=0, sticky="w",
                                                 padx=(20, 10), pady=6)
            var = tk.StringVar(value=default or "")
            self._vars[key] = var
            if kind == "entry":
                tk.Entry(self, textvariable=var,
                         font=(FF, 10), width=30, relief="flat",
                         highlightbackground=COLORS["border"],
                         highlightthickness=1).grid(row=i + 2, column=1,
                                                    padx=(0, 20), pady=6, sticky="ew")
            else:
                values = list(self._ap) if key in ("origin_iata", "dest_iata") else list(self._ac)
                ttk.Combobox(self, textvariable=var,
                             values=values, width=28,
                             font=(FF, 10), state="readonly").grid(row=i + 2, column=1,
                                                                   padx=(0, 20), pady=6, sticky="ew")

        self.columnconfigure(1, weight=1)
        tk.Frame(self, bg=COLORS["border"], height=1).grid(
            row=len(fields) + 2, column=0, columnspan=2, sticky="ew", padx=20, pady=(8, 0))
        bf = tk.Frame(self)
        bf.grid(row=len(fields) + 3, column=0, columnspan=2, pady=14)
        tk.Button(bf, text="Добавить",
                  font=(FF, 10), bg=COLORS["accent"], fg="white",
                  relief="flat", padx=14,
                  command=self._ok).pack(side="left", padx=6)
        tk.Button(bf, text="Отмена",
                  font=(FF, 10), relief="flat", padx=14,
                  command=self.destroy).pack(side="left")

    def _ok(self):
        import re
        from datetime import datetime

        vals = {k: v.get().strip() for k, v in self._vars.items()}
        if not all(vals.values()):
            messagebox.showwarning("Заполните все поля", "Все поля обязательны.", parent=self)
            return

        try:
            price = float(vals["base_price"])
        except ValueError:
            messagebox.showerror("Ошибка", "Цена должна быть числом.", parent=self)
            return

        dt_pattern = re.compile(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$")
        if not dt_pattern.match(vals["departure_time"]):
            messagebox.showerror("Ошибка", "Вылет: неверный формат.\nОжидается: ГГГГ-ММ-ДД ЧЧ:ММ:СС", parent=self)
            return
        if not dt_pattern.match(vals["arrival_time"]):
            messagebox.showerror("Ошибка", "Прилёт: неверный формат.\nОжидается: ГГГГ-ММ-ДД ЧЧ:ММ:СС", parent=self)
            return

        if vals["origin_iata"] == vals["dest_iata"]:
            messagebox.showerror("Ошибка", "Город вылета и прилёта не могут совпадать.", parent=self)
            return

        try:
            dep = datetime.strptime(vals["departure_time"], "%Y-%m-%d %H:%M:%S")
            arr = datetime.strptime(vals["arrival_time"], "%Y-%m-%d %H:%M:%S")
        except ValueError:
            messagebox.showerror("Ошибка", "Введена несуществующая дата.", parent=self)
            return

        if arr <= dep:
            messagebox.showerror("Ошибка", "Время прилёта должно быть позже времени вылета.", parent=self)
            return

        if vals["origin_iata"] not in self._ap.values():
            vals["origin_iata"] = self._ap.get(vals["origin_iata"], "")
        if vals["dest_iata"] not in self._ap.values():
            vals["dest_iata"] = self._ap.get(vals["dest_iata"], "")
        if vals["aircraft_reg"] not in self._ac.values():
            vals["aircraft_reg"] = self._ac.get(vals["aircraft_reg"], "")

        self.result = {
            "flight_number": vals["flight_number"],
            "origin_iata": vals["origin_iata"],
            "dest_iata": vals["dest_iata"],
            "aircraft_reg": vals["aircraft_reg"],
            "departure_time": vals["departure_time"],
            "arrival_time": vals["arrival_time"],
            "base_price": price,
        }
        self.destroy()