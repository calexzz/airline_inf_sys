import tkinter as tk
from tkinter import ttk, messagebox

from models.crew_model import (
    get_all_crew, search_crew,
    add_crew_member, update_crew_member, delete_crew_member,
    get_crew_by_flight, assign_crew_to_flight, remove_crew_from_flight,
    get_flights_by_crew,
)
from models.flight_model import get_all_flights

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
}
FF = "Helvetica"

ROLE_RU = {
    "captain": "Командир",
    "first_officer": "Второй пилот",
    "flight_attendant": "Бортпроводник",
}

POSITION_RU = {
    "captain": "Командир",
    "first_officer": "Второй пилот",
    "senior_attendant": "Старший бортпроводник",
    "attendant": "Бортпроводник",
}


class CrewView(tk.Frame):
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
        tk.Label(row, text="Экипаж",
                 font=(FF, 18, "bold"),
                 bg=COLORS["bg"], fg=COLORS["text_main"]).grid(row=0, column=0, sticky="w")
        btn_frame = tk.Frame(row, bg=COLORS["bg"])
        btn_frame.grid(row=0, column=1, sticky="e")
        tk.Button(btn_frame, text="Назначить на рейс",
                  font=(FF, 10), bg=COLORS["bg"], fg=COLORS["accent"],
                  relief="flat", padx=14, pady=6, cursor="hand2",
                  highlightbackground=COLORS["accent"], highlightthickness=1,
                  command=self._on_assign).pack(side="left", padx=(0, 8))
        tk.Button(btn_frame, text="Добавить сотрудника",
                  font=(FF, 10), bg=COLORS["accent"], fg="white",
                  relief="flat", padx=14, pady=6, cursor="hand2",
                  command=self._on_add).pack(side="left")

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
        tk.Label(row, text="по фамилии, имени или номеру лицензии",
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

        columns = ("last_name", "first_name", "role", "license_num", "license_exp", "months_left", "flights_count")
        self._tree = ttk.Treeview(card, columns=columns,
                                  show="headings", selectmode="browse")

        col_cfg = [
            ("last_name", "Фамилия", 120, "w"),
            ("first_name", "Имя", 110, "w"),
            ("role", "Должность", 150, "w"),
            ("license_num", "Лицензия", 110, "center"),
            ("license_exp", "Действует до", 110, "center"),
            ("months_left", "Осталось, мес.", 110, "center"),
            ("flights_count", "Рейсов", 70, "center"),
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
        self._tree.tag_configure("expiring", foreground=COLORS["warning"])
        self._tree.tag_configure("critical", foreground=COLORS["danger"])

        vsb = ttk.Scrollbar(card, orient="vertical", command=self._tree.yview)
        self._tree.configure(yscrollcommand=vsb.set)
        self._tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")

        self._tree.bind("<Double-1>", self._on_double_click)

        self._ctx = tk.Menu(self, tearoff=0)
        self._ctx.add_command(label="Редактировать", command=self._on_edit)
        self._ctx.add_command(label="Рейсы сотрудника", command=self._on_flights)
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
        data = rows if rows is not None else get_all_crew()
        for i, c in enumerate(data):
            months = c["months_left"]
            tags = []
            if i % 2:
                tags.append("odd")
            if months is not None and months <= 3:
                tags.append("critical")
            elif months is not None and months <= 9:
                tags.append("expiring")
            self._tree.insert(
                "", "end",
                iid=str(c["crew_id"]),
                tags=tuple(tags),
                values=(
                    c["last_name"],
                    c["first_name"],
                    ROLE_RU.get(c["role"], c["role"]),
                    c["license_num"],
                    c["license_exp"],
                    months if months is not None else "—",
                    c["flights_count"],
                )
            )
        self._status.set(f"Сотрудников: {len(data)}")

    def _on_search(self):
        q = self._q.get().strip()
        if q:
            rows = search_crew(q)
            self._load(_add_months(rows))
        else:
            self._load()

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
        dlg = _CrewDialog(self)
        self.wait_window(dlg)
        if dlg.result:
            try:
                add_crew_member(**dlg.result)
                self._load()
                messagebox.showinfo("Готово", "Сотрудник добавлен.", parent=self)
            except ValueError as e:
                messagebox.showerror("Ошибка", str(e), parent=self)

    def _on_edit(self):
        cid = self._selected_id()
        if not cid:
            return
        vals = self._tree.item(str(cid))["values"]
        role_key = next((k for k, v in ROLE_RU.items() if v == vals[2]), vals[2])
        current = {
            "last_name": vals[0],
            "first_name": vals[1],
            "role": role_key,
            "license_num": vals[3],
            "license_exp": vals[4],
        }
        dlg = _CrewDialog(self, current)
        self.wait_window(dlg)
        if dlg.result:
            try:
                update_crew_member(
                    cid,
                    dlg.result["last_name"],
                    dlg.result["first_name"],
                    dlg.result["role"],
                    dlg.result["license_exp"],
                )
                self._load()
            except ValueError as e:
                messagebox.showerror("Ошибка", str(e), parent=self)

    def _on_flights(self):
        cid = self._selected_id()
        if not cid:
            return
        vals = self._tree.item(str(cid))["values"]
        name = f"{vals[0]} {vals[1]}"
        flights = get_flights_by_crew(cid)
        _CrewFlightsDialog(self, name, flights)

    def _on_assign(self):
        cid = self._selected_id()
        dlg = _AssignDialog(self, cid)
        self.wait_window(dlg)
        if dlg.result:
            try:
                assign_crew_to_flight(**dlg.result)
                self._load()
                messagebox.showinfo("Готово", "Сотрудник назначен на рейс.", parent=self)
            except ValueError as e:
                messagebox.showerror("Ошибка", str(e), parent=self)

    def _on_delete(self):
        cid = self._selected_id()
        if not cid:
            return
        vals = self._tree.item(str(cid))["values"]
        name = f"{vals[0]} {vals[1]}"
        if not messagebox.askyesno("Удаление", f"Удалить сотрудника {name}?", parent=self):
            return
        try:
            delete_crew_member(cid)
            self._load()
        except ValueError as e:
            messagebox.showerror("Ошибка", str(e), parent=self)


def _add_months(rows):
    from datetime import date
    result = []
    for r in rows:
        try:
            exp = date.fromisoformat(r["license_exp"])
            today = date.today()
            months = (exp.year - today.year) * 12 + (exp.month - today.month)
        except Exception:
            months = None
        result.append({
            "crew_id": r["crew_id"],
            "last_name": r["last_name"],
            "first_name": r["first_name"],
            "role": r["role"],
            "license_num": r["license_num"],
            "license_exp": r["license_exp"],
            "months_left": months,
            "flights_count": 0,
        })
    return result


class _CrewDialog(tk.Toplevel):
    def __init__(self, parent, current=None):
        super().__init__(parent)
        self.title("Редактировать сотрудника" if current else "Новый сотрудник")
        self.resizable(False, False)
        self.grab_set()
        self.result = None
        self._current = current
        self._build()

    def _build(self):
        title = "Редактировать сотрудника" if self._current else "Новый сотрудник"
        tk.Label(self, text=title,
                 font=(FF, 13, "bold"),
                 fg=COLORS["text_main"]).grid(row=0, column=0, columnspan=2,
                                              sticky="w", padx=20, pady=(16, 12))
        tk.Frame(self, bg=COLORS["border"], height=1).grid(
            row=1, column=0, columnspan=2, sticky="ew", padx=20)

        self._vars = {}
        fields = [
            ("last_name", "Фамилия", "entry", None, True),
            ("first_name", "Имя", "entry", None, True),
            ("role", "Должность", "combo", list(ROLE_RU.keys()), True),
            ("license_num", "Номер лицензии", "entry", None, not bool(self._current)),
            ("license_exp", "Действует до", "entry", "ГГГГ-ММ-ДД", True),
        ]

        for i, (key, label, kind, opts, editable) in enumerate(fields):
            tk.Label(self, text=label,
                     font=(FF, 10), fg=COLORS["text_sub"],
                     anchor="w").grid(row=i + 2, column=0, sticky="w",
                                      padx=(20, 10), pady=6)
            default = self._current.get(key, "") if self._current else ""
            var = tk.StringVar(value=default)
            self._vars[key] = var

            if kind == "combo":
                display_values = [ROLE_RU[k] for k in opts]
                display_var = tk.StringVar(value=ROLE_RU.get(default, default))
                self._vars["_role_display"] = display_var
                ttk.Combobox(self, textvariable=display_var,
                             values=display_values,
                             width=26, font=(FF, 10),
                             state="readonly" if editable else "disabled").grid(
                    row=i + 2, column=1, padx=(0, 20), pady=6, sticky="ew")
            else:
                e = tk.Entry(self, textvariable=var,
                             font=(FF, 10), width=28, relief="flat",
                             highlightbackground=COLORS["border"],
                             highlightthickness=1)
                e.configure(state="normal" if editable else "readonly")
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
        import re
        vals = {k: v.get().strip() for k, v in self._vars.items() if not k.startswith("_")}
        role_display = self._vars.get("_role_display", tk.StringVar()).get()
        vals["role"] = next((k for k, v in ROLE_RU.items() if v == role_display), vals.get("role", ""))

        if not all(v for k, v in vals.items()):
            messagebox.showwarning("Заполните все поля", "", parent=self)
            return

        if not re.match(r"^\d{4}-\d{2}-\d{2}$", vals["license_exp"]):
            messagebox.showerror("Ошибка", "Дата лицензии: формат ГГГГ-ММ-ДД", parent=self)
            return

        from datetime import date
        try:
            date.fromisoformat(vals["license_exp"])
        except ValueError:
            messagebox.showerror("Ошибка", "Введена несуществующая дата.", parent=self)
            return

        self.result = vals
        self.destroy()


class _AssignDialog(tk.Toplevel):
    def __init__(self, parent, preselected_crew_id=None):
        super().__init__(parent)
        self.title("Назначить на рейс")
        self.resizable(False, False)
        self.grab_set()
        self.result = None

        crew = get_all_crew()
        flights = [f for f in get_all_flights() if f["status"] == "scheduled"]

        self._crew_map = {
            f"{c['last_name']} {c['first_name']} ({ROLE_RU.get(c['role'], c['role'])})": c["crew_id"]
            for c in crew
        }
        self._flight_map = {
            f"{f['flight_number']}  {f['origin_city']} — {f['dest_city']}  ({f['departure_time'][:10]})": f["flight_id"]
            for f in flights
        }
        self._preselected = preselected_crew_id
        self._build()

    def _build(self):
        tk.Label(self, text="Назначить на рейс",
                 font=(FF, 13, "bold"),
                 fg=COLORS["text_main"]).grid(row=0, column=0, columnspan=2,
                                              sticky="w", padx=20, pady=(16, 12))
        tk.Frame(self, bg=COLORS["border"], height=1).grid(
            row=1, column=0, columnspan=2, sticky="ew", padx=20)

        tk.Label(self, text="Сотрудник",
                 font=(FF, 10), fg=COLORS["text_sub"],
                 anchor="w").grid(row=2, column=0, sticky="w", padx=(20, 10), pady=6)
        self._crew_var = tk.StringVar()
        if self._preselected:
            for label, cid in self._crew_map.items():
                if cid == self._preselected:
                    self._crew_var.set(label)
                    break
        ttk.Combobox(self, textvariable=self._crew_var,
                     values=list(self._crew_map),
                     width=36, font=(FF, 10), state="readonly").grid(
            row=2, column=1, padx=(0, 20), pady=6, sticky="ew")

        tk.Label(self, text="Рейс",
                 font=(FF, 10), fg=COLORS["text_sub"],
                 anchor="w").grid(row=3, column=0, sticky="w", padx=(20, 10), pady=6)
        self._flight_var = tk.StringVar()
        ttk.Combobox(self, textvariable=self._flight_var,
                     values=list(self._flight_map),
                     width=36, font=(FF, 10), state="readonly").grid(
            row=3, column=1, padx=(0, 20), pady=6, sticky="ew")

        tk.Label(self, text="Позиция",
                 font=(FF, 10), fg=COLORS["text_sub"],
                 anchor="w").grid(row=4, column=0, sticky="w", padx=(20, 10), pady=6)
        self._pos_var = tk.StringVar(value="captain")
        pos_frame = tk.Frame(self)
        pos_frame.grid(row=4, column=1, sticky="w", padx=(0, 20), pady=6)
        for val, label in POSITION_RU.items():
            tk.Radiobutton(pos_frame, text=label, variable=self._pos_var,
                           value=val, font=(FF, 10)).pack(side="left", padx=(0, 10))

        self.columnconfigure(1, weight=1)
        tk.Frame(self, bg=COLORS["border"], height=1).grid(
            row=5, column=0, columnspan=2, sticky="ew", padx=20, pady=(8, 0))
        bf = tk.Frame(self)
        bf.grid(row=6, column=0, columnspan=2, pady=14)
        tk.Button(bf, text="Назначить",
                  font=(FF, 10), bg=COLORS["accent"], fg="white",
                  relief="flat", padx=14,
                  command=self._ok).pack(side="left", padx=6)
        tk.Button(bf, text="Отмена",
                  font=(FF, 10), relief="flat", padx=14,
                  command=self.destroy).pack(side="left")

    def _ok(self):
        if not self._crew_var.get():
            messagebox.showwarning("Выберите сотрудника", "", parent=self)
            return
        if not self._flight_var.get():
            messagebox.showwarning("Выберите рейс", "", parent=self)
            return
        self.result = {
            "flight_id": self._flight_map[self._flight_var.get()],
            "crew_id": self._crew_map[self._crew_var.get()],
            "position": self._pos_var.get(),
        }
        self.destroy()


class _CrewFlightsDialog(tk.Toplevel):
    def __init__(self, parent, name, flights):
        super().__init__(parent)
        self.title(f"Рейсы сотрудника — {name}")
        self.geometry("660x360")
        self.grab_set()
        self._build(name, flights)

    def _build(self, name, flights):
        tk.Label(self, text=f"Рейсы: {name}",
                 font=(FF, 12, "bold"),
                 fg=COLORS["text_main"]).pack(anchor="w", padx=20, pady=(16, 8))

        card = tk.Frame(self, bg=COLORS["card"],
                        highlightbackground=COLORS["border"],
                        highlightthickness=1)
        card.pack(fill="both", expand=True, padx=20, pady=(0, 16))
        card.columnconfigure(0, weight=1)
        card.rowconfigure(0, weight=1)

        columns = ("flight", "route", "dep", "arr", "position", "status")
        tree = ttk.Treeview(card, columns=columns,
                            show="headings", selectmode="none")

        col_cfg = [
            ("flight", "Рейс", 80, "center"),
            ("route", "Маршрут", 190, "w"),
            ("dep", "Вылет", 130, "center"),
            ("arr", "Прилёт", 130, "center"),
            ("position", "Позиция", 150, "w"),
            ("status", "Статус", 100, "center"),
        ]
        for cid, heading, width, anchor in col_cfg:
            tree.heading(cid, text=heading)
            tree.column(cid, width=width, minwidth=40, anchor=anchor)

        tree.tag_configure("odd", background=COLORS["row_odd"])

        STATUS_RU = {
            "scheduled": "По расписанию",
            "departed": "Вылетел",
            "arrived": "Прибыл",
            "cancelled": "Отменён",
        }

        for i, f in enumerate(flights):
            tree.insert("", "end",
                        tags=("odd",) if i % 2 else (),
                        values=(
                            f["flight_number"],
                            f"{f['origin_city']} — {f['dest_city']}",
                            f["departure_time"][:16],
                            f["arrival_time"][:16],
                            POSITION_RU.get(f["position"], f["position"]),
                            STATUS_RU.get(f["status"], f["status"]),
                        ))

        if not flights:
            tree.insert("", "end", values=("—", "Рейсов нет", "", "", "", ""))

        vsb = ttk.Scrollbar(card, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=vsb.set)
        tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")

        tk.Button(self, text="Закрыть",
                  font=(FF, 10), relief="flat", padx=14,
                  command=self.destroy).pack(pady=(0, 12))