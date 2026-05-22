import tkinter as tk
from tkinter import ttk, messagebox

from models.passenger_model import (
    get_all_passengers, search_passengers,
    add_passenger, update_passenger, delete_passenger,
    get_passenger_history,
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
    "success": "#3A7D44",
    "row_even": "#FFFFFF",
    "row_odd": "#F9F8F5",
    "header_bg": "#EFF4FA",
}
FF = "Helvetica"


class PassengersView(tk.Frame):
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
        tk.Label(row, text="Пассажиры",
                 font=(FF, 18, "bold"),
                 bg=COLORS["bg"], fg=COLORS["text_main"]).grid(row=0, column=0, sticky="w")
        tk.Button(row, text="Добавить пассажира",
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
        tk.Label(row, text="по фамилии, имени, паспорту или email",
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

        columns = ("last_name", "first_name", "passport", "email", "phone", "flights")
        self._tree = ttk.Treeview(card, columns=columns,
                                  show="headings", selectmode="browse")

        col_cfg = [
            ("last_name", "Фамилия", 130, "w"),
            ("first_name", "Имя", 120, "w"),
            ("passport", "Паспорт", 110, "center"),
            ("email", "Email", 190, "w"),
            ("phone", "Телефон", 130, "center"),
            ("flights", "Рейсов", 70, "center"),
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

        self._tree.bind("<Double-1>", self._on_double_click)

        self._ctx = tk.Menu(self, tearoff=0)
        self._ctx.add_command(label="Редактировать", command=self._on_edit)
        self._ctx.add_command(label="История рейсов", command=self._on_history)
        self._ctx.add_separator()
        self._ctx.add_command(label="Удалить", command=self._on_delete)
        self._tree.bind("<Button-3>", self._show_ctx)
        self._tree.bind("<Button-2>", self._show_ctx)

    def _build_statusbar(self):
        self._status = tk.StringVar()
        tk.Label(self, textvariable=self._status,
                 font=(FF, 9), bg=COLORS["bg"],
                 fg=COLORS["text_sub"]).grid(row=3, column=0, sticky="w", padx=26, pady=(4, 10))

    def _load(self, rows=None):
        self._tree.delete(*self._tree.get_children())
        data = rows if rows is not None else get_all_passengers()
        for i, p in enumerate(data):
            self._tree.insert(
                "", "end",
                iid=str(p["passenger_id"]),
                tags=("odd",) if i % 2 else (),
                values=(
                    p["last_name"],
                    p["first_name"],
                    p["passport_num"],
                    p["email"],
                    p["phone"],
                    p["total_flights"],
                )
            )
        self._status.set(f"Пассажиров: {len(data)}")

    def _on_search(self):
        q = self._q.get().strip()
        self._load(search_passengers(q) if q else None)

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

    def _on_double_click(self, event):
        iid = self._tree.identify_row(event.y)
        if iid:
            self._tree.selection_set(iid)
            self._on_edit()

    def _selected_id(self):
        sel = self._tree.selection()
        return int(sel[0]) if sel else None

    def _on_add(self):
        dlg = _PassengerDialog(self)
        self.wait_window(dlg)
        if dlg.result:
            try:
                add_passenger(**dlg.result)
                self._load()
                messagebox.showinfo("Готово", "Пассажир добавлен.", parent=self)
            except ValueError as e:
                messagebox.showerror("Ошибка", str(e), parent=self)

    def _on_edit(self):
        pid = self._selected_id()
        if not pid:
            return
        vals = self._tree.item(str(pid))["values"]
        current = {
            "last_name": vals[0],
            "first_name": vals[1],
            "passport_num": vals[2],
            "email": vals[3],
            "phone": vals[4],
        }
        dlg = _PassengerDialog(self, current)
        self.wait_window(dlg)
        if dlg.result:
            try:
                update_passenger(
                    pid,
                    dlg.result["last_name"],
                    dlg.result["first_name"],
                    dlg.result["email"],
                    dlg.result["phone"],
                )
                self._load()
            except ValueError as e:
                messagebox.showerror("Ошибка", str(e), parent=self)

    def _on_history(self):
        pid = self._selected_id()
        if not pid:
            return
        vals = self._tree.item(str(pid))["values"]
        name = f"{vals[0]} {vals[1]}"
        history = get_passenger_history(pid)
        _HistoryDialog(self, name, history)

    def _on_delete(self):
        pid = self._selected_id()
        if not pid:
            return
        vals = self._tree.item(str(pid))["values"]
        name = f"{vals[0]} {vals[1]}"
        if not messagebox.askyesno("Удаление",
                                   f"Удалить пассажира {name}?", parent=self):
            return
        try:
            delete_passenger(pid)
            self._load()
        except ValueError as e:
            messagebox.showerror("Ошибка", str(e), parent=self)


class _PassengerDialog(tk.Toplevel):
    def __init__(self, parent, current=None):
        super().__init__(parent)
        self.title("Редактировать пассажира" if current else "Новый пассажир")
        self.resizable(False, False)
        self.grab_set()
        self.result = None
        self._current = current
        self._build()

    def _build(self):
        title = "Редактировать пассажира" if self._current else "Новый пассажир"
        tk.Label(self, text=title,
                 font=(FF, 13, "bold"),
                 fg=COLORS["text_main"]).grid(row=0, column=0, columnspan=2,
                                              sticky="w", padx=20, pady=(16, 12))
        tk.Frame(self, bg=COLORS["border"], height=1).grid(
            row=1, column=0, columnspan=2, sticky="ew", padx=20)

        self._vars = {}
        fields = [
            ("last_name", "Фамилия", True),
            ("first_name", "Имя", True),
            ("passport_num", "Паспорт", not bool(self._current)),
            ("email", "Email", True),
            ("phone", "Телефон", True),
        ]
        for i, (key, label, editable) in enumerate(fields):
            tk.Label(self, text=label,
                     font=(FF, 10), fg=COLORS["text_sub"],
                     anchor="w").grid(row=i + 2, column=0, sticky="w",
                                      padx=(20, 10), pady=6)
            var = tk.StringVar(value=self._current.get(key, "") if self._current else "")
            self._vars[key] = var
            state = "normal" if editable else "readonly"
            e = tk.Entry(self, textvariable=var,
                         font=(FF, 10), width=28, relief="flat",
                         highlightbackground=COLORS["border"],
                         highlightthickness=1)
            e.configure(state=state)
            if not editable:
                e.configure(bg=COLORS["bg"])
            e.grid(row=i + 2, column=1, padx=(0, 20), pady=6, sticky="ew")

        self.columnconfigure(1, weight=1)
        tk.Frame(self, bg=COLORS["border"], height=1).grid(
            row=len(fields) + 2, column=0, columnspan=2,
            sticky="ew", padx=20, pady=(8, 0))

        bf = tk.Frame(self)
        bf.grid(row=len(fields) + 3, column=0, columnspan=2, pady=14)
        tk.Button(bf, text="Сохранить",
                  font=(FF, 10), bg=COLORS["accent"], fg="white",
                  relief="flat", padx=14,
                  command=self._ok).pack(side="left", padx=6)
        tk.Button(bf, text="Отмена",
                  font=(FF, 10), relief="flat", padx=14,
                  command=self.destroy).pack(side="left")

    def _ok(self):
        vals = {k: v.get().strip() for k, v in self._vars.items()}
        if not all(vals.values()):
            messagebox.showwarning("Заполните все поля", "", parent=self)
            return
        self.result = vals
        self.destroy()


class _HistoryDialog(tk.Toplevel):
    def __init__(self, parent, name, history):
        super().__init__(parent)
        self.title(f"История рейсов — {name}")
        self.geometry("680x380")
        self.grab_set()
        self._build(name, history)

    def _build(self, name, history):
        tk.Label(self, text=f"История рейсов: {name}",
                 font=(FF, 12, "bold"),
                 fg=COLORS["text_main"]).pack(anchor="w", padx=20, pady=(16, 8))

        card = tk.Frame(self, bg=COLORS["card"],
                        highlightbackground=COLORS["border"],
                        highlightthickness=1)
        card.pack(fill="both", expand=True, padx=20, pady=(0, 16))
        card.columnconfigure(0, weight=1)
        card.rowconfigure(0, weight=1)

        columns = ("flight", "route", "dep", "seat", "cls", "price", "status")
        tree = ttk.Treeview(card, columns=columns,
                            show="headings", selectmode="none")

        col_cfg = [
            ("flight", "Рейс", 80, "center"),
            ("route", "Маршрут", 180, "w"),
            ("dep", "Дата вылета", 120, "center"),
            ("seat", "Место", 60, "center"),
            ("cls", "Класс", 80, "center"),
            ("price", "Цена, ₽", 90, "e"),
            ("status", "Статус", 100, "center"),
        ]
        for cid, heading, width, anchor in col_cfg:
            tree.heading(cid, text=heading)
            tree.column(cid, width=width, minwidth=40, anchor=anchor)

        tree.tag_configure("odd", background=COLORS["row_odd"])

        STATUS_RU = {"confirmed": "Подтверждено", "cancelled": "Отменено", "used": "Использовано"}
        CLASS_RU = {"economy": "Эконом", "business": "Бизнес", "first": "Первый"}

        for i, r in enumerate(history):
            tree.insert("", "end",
                        tags=("odd",) if i % 2 else (),
                        values=(
                            r["flight_number"],
                            f"{r['origin_city']} — {r['dest_city']}",
                            r["departure_time"][:10],
                            r["seat_number"],
                            CLASS_RU.get(r["class"], r["class"]),
                            f"{r['price']:,.0f}",
                            STATUS_RU.get(r["booking_status"], r["booking_status"]),
                        ))

        if not history:
            tree.insert("", "end", values=("—", "Нет данных", "", "", "", "", ""))

        vsb = ttk.Scrollbar(card, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=vsb.set)
        tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")

        tk.Button(self, text="Закрыть",
                  font=(FF, 10), relief="flat", padx=14,
                  command=self.destroy).pack(pady=(0, 12))