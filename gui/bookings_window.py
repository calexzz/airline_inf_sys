import tkinter as tk
from tkinter import ttk, messagebox

from models.booking_model import (
    get_all_bookings, get_bookings_by_flight,
    add_booking, cancel_booking, delete_booking,
)
from models.flight_model import get_all_flights
from models.passenger_model import get_passenger_by_passport, add_passenger

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

STATUS_RU = {
    "confirmed": "Подтверждено",
    "cancelled": "Отменено",
    "used": "Использовано",
}

CLASS_RU = {
    "economy": "Эконом",
    "business": "Бизнес",
    "first": "Первый",
}


class BookingsView(tk.Frame):
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
        tk.Label(row, text="Бронирования",
                 font=(FF, 18, "bold"),
                 bg=COLORS["bg"], fg=COLORS["text_main"]).grid(row=0, column=0, sticky="w")
        tk.Button(row, text="Новое бронирование",
                  font=(FF, 10), bg=COLORS["accent"], fg="white",
                  relief="flat", padx=14, pady=6, cursor="hand2",
                  command=self._on_add).grid(row=0, column=1, sticky="e")

    def _build_toolbar(self):
        row = tk.Frame(self, bg=COLORS["bg"])
        row.grid(row=1, column=0, sticky="ew", padx=24, pady=10)

        tk.Label(row, text="Фильтр по рейсу:",
                 font=(FF, 10), bg=COLORS["bg"],
                 fg=COLORS["text_sub"]).pack(side="left")

        flights = get_all_flights()
        self._flight_map = {"Все рейсы": None}
        self._flight_map.update({
            f"{f['flight_number']}  {f['origin_city']} — {f['dest_city']}": f["flight_id"]
            for f in flights
        })

        self._filter_var = tk.StringVar(value="Все рейсы")
        cb = ttk.Combobox(row, textvariable=self._filter_var,
                          values=list(self._flight_map),
                          width=34, font=(FF, 10), state="readonly")
        cb.pack(side="left", padx=(8, 0))
        cb.bind("<<ComboboxSelected>>", lambda _: self._on_filter())

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

        columns = ("id", "passenger", "flight", "route", "dep", "seat", "cls", "price", "status")
        self._tree = ttk.Treeview(card, columns=columns,
                                  show="headings", selectmode="browse")

        col_cfg = [
            ("id", "№", 40, "center"),
            ("passenger", "Пассажир", 160, "w"),
            ("flight", "Рейс", 70, "center"),
            ("route", "Маршрут", 180, "w"),
            ("dep", "Вылет", 120, "center"),
            ("seat", "Место", 60, "center"),
            ("cls", "Класс", 80, "center"),
            ("price", "Цена, ₽", 90, "e"),
            ("status", "Статус", 110, "center"),
        ]
        for cid, heading, width, anchor in col_cfg:
            self._tree.heading(cid, text=heading,
                               command=lambda c=cid: self._sort_by(c))
            self._tree.column(cid, width=width, minwidth=40, anchor=anchor)

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
        self._tree.tag_configure("cancelled", foreground=COLORS["danger"])

        vsb = ttk.Scrollbar(card, orient="vertical", command=self._tree.yview)
        self._tree.configure(yscrollcommand=vsb.set)
        self._tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")

        self._ctx = tk.Menu(self, tearoff=0)
        self._ctx.add_command(label="Отменить бронирование", command=self._on_cancel)
        self._ctx.add_separator()
        self._ctx.add_command(label="Удалить запись", command=self._on_delete)
        self._tree.bind("<Button-3>", self._show_ctx)
        self._tree.bind("<Button-2>", self._show_ctx)

    def _build_statusbar(self):
        self._status = tk.StringVar()
        tk.Label(self, textvariable=self._status,
                 font=(FF, 9), bg=COLORS["bg"],
                 fg=COLORS["text_sub"]).grid(row=3, column=0, sticky="w", padx=26, pady=(4, 10))

    def _load(self, rows=None):
        self._tree.delete(*self._tree.get_children())
        data = rows if rows is not None else get_all_bookings()
        for i, b in enumerate(data):
            tags = []
            if i % 2:
                tags.append("odd")
            if b["status"] == "cancelled":
                tags.append("cancelled")
            self._tree.insert(
                "", "end",
                iid=str(b["booking_id"]),
                tags=tuple(tags),
                values=(
                    b["booking_id"],
                    b["passenger_name"],
                    b["flight_number"],
                    f"{b['origin_city']} — {b['dest_city']}",
                    b["departure_time"][:16],
                    b["seat_number"],
                    CLASS_RU.get(b["class"], b["class"]),
                    f"{b['price']:,.0f}",
                    STATUS_RU.get(b["status"], b["status"]),
                )
            )
        self._status.set(f"Записей: {len(data)}")

    def _on_filter(self):
        flight_id = self._flight_map.get(self._filter_var.get())
        if flight_id is None:
            self._load()
        else:
            rows = get_bookings_by_flight(flight_id)
            self._load(_adapt_manifest(rows))

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

    def _on_cancel(self):
        bid = self._selected_id()
        if not bid:
            return
        if not messagebox.askyesno("Отмена бронирования",
                                   "Отменить выбранное бронирование?", parent=self):
            return
        try:
            cancel_booking(bid)
            self._load()
        except ValueError as e:
            messagebox.showerror("Ошибка", str(e), parent=self)

    def _on_delete(self):
        bid = self._selected_id()
        if not bid:
            return
        if not messagebox.askyesno("Удаление",
                                   "Полностью удалить запись о бронировании?", parent=self):
            return
        delete_booking(bid)
        self._load()

    def _on_add(self):
        dlg = _AddBookingDialog(self)
        self.wait_window(dlg)
        if dlg.result:
            try:
                add_booking(**dlg.result)
                self._load()
                messagebox.showinfo("Готово", "Бронирование оформлено.", parent=self)
            except ValueError as e:
                messagebox.showerror("Ошибка", str(e), parent=self)


def _adapt_manifest(rows):
    result = []
    for b in rows:
        result.append({
            "booking_id": b["booking_id"],
            "passenger_name": f"{b['last_name']} {b['first_name']}",
            "flight_number": "—",
            "origin_city": "—",
            "dest_city": "—",
            "departure_time": "—",
            "seat_number": b["seat_number"],
            "class": b["class"],
            "price": b["price"],
            "status": b["status"],
        })
    return result


class _AddBookingDialog(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Новое бронирование")
        self.resizable(False, False)
        self.grab_set()
        self.result = None

        flights = get_all_flights()
        self._flight_map = {
            f"{f['flight_number']}  {f['origin_city']} — {f['dest_city']}  ({f['departure_time'][:10]})": f["flight_id"]
            for f in flights
            if f["status"] == "scheduled"
        }
        self._build()

    def _build(self):
        tk.Label(self, text="Новое бронирование",
                 font=(FF, 13, "bold"),
                 fg=COLORS["text_main"]).grid(row=0, column=0, columnspan=2,
                                              sticky="w", padx=20, pady=(16, 12))
        tk.Frame(self, bg=COLORS["border"], height=1).grid(
            row=1, column=0, columnspan=2, sticky="ew", padx=20)

        tk.Label(self, text="Паспорт пассажира",
                 font=(FF, 10), fg=COLORS["text_sub"],
                 anchor="w").grid(row=2, column=0, sticky="w", padx=(20, 10), pady=6)
        passport_frame = tk.Frame(self)
        passport_frame.grid(row=2, column=1, sticky="ew", padx=(0, 20), pady=6)
        self._passport_var = tk.StringVar()
        tk.Entry(passport_frame, textvariable=self._passport_var,
                 font=(FF, 10), width=20, relief="flat",
                 highlightbackground=COLORS["border"],
                 highlightthickness=1).pack(side="left", ipady=4, ipadx=4)
        tk.Button(passport_frame, text="Найти",
                  font=(FF, 9), bg=COLORS["accent"], fg="white",
                  relief="flat", padx=8,
                  command=self._find_passenger).pack(side="left", padx=(6, 0))

        self._passenger_label = tk.Label(self, text="Пассажир не найден",
                                         font=(FF, 9), fg=COLORS["text_light"])
        self._passenger_label.grid(row=3, column=1, sticky="w", padx=(0, 20), pady=(0, 4))
        self._passenger_id = None

        tk.Label(self, text="Рейс",
                 font=(FF, 10), fg=COLORS["text_sub"],
                 anchor="w").grid(row=4, column=0, sticky="w", padx=(20, 10), pady=6)
        self._flight_var = tk.StringVar()
        ttk.Combobox(self, textvariable=self._flight_var,
                     values=list(self._flight_map),
                     width=36, font=(FF, 10), state="readonly").grid(
            row=4, column=1, padx=(0, 20), pady=6, sticky="ew")

        tk.Label(self, text="Номер места",
                 font=(FF, 10), fg=COLORS["text_sub"],
                 anchor="w").grid(row=5, column=0, sticky="w", padx=(20, 10), pady=6)
        self._seat_var = tk.StringVar()
        tk.Entry(self, textvariable=self._seat_var,
                 font=(FF, 10), width=10, relief="flat",
                 highlightbackground=COLORS["border"],
                 highlightthickness=1).grid(row=5, column=1, padx=(0, 20), pady=6, sticky="w")

        tk.Label(self, text="Класс",
                 font=(FF, 10), fg=COLORS["text_sub"],
                 anchor="w").grid(row=6, column=0, sticky="w", padx=(20, 10), pady=6)
        self._class_var = tk.StringVar(value="economy")
        class_frame = tk.Frame(self)
        class_frame.grid(row=6, column=1, sticky="w", padx=(0, 20), pady=6)
        for val, label in CLASS_RU.items():
            tk.Radiobutton(class_frame, text=label, variable=self._class_var,
                           value=val, font=(FF, 10)).pack(side="left", padx=(0, 12))

        tk.Label(self, text="Цена, ₽",
                 font=(FF, 10), fg=COLORS["text_sub"],
                 anchor="w").grid(row=7, column=0, sticky="w", padx=(20, 10), pady=6)
        self._price_var = tk.StringVar()
        tk.Entry(self, textvariable=self._price_var,
                 font=(FF, 10), width=14, relief="flat",
                 highlightbackground=COLORS["border"],
                 highlightthickness=1).grid(row=7, column=1, padx=(0, 20), pady=6, sticky="w")

        self.columnconfigure(1, weight=1)
        tk.Frame(self, bg=COLORS["border"], height=1).grid(
            row=8, column=0, columnspan=2, sticky="ew", padx=20, pady=(8, 0))

        bf = tk.Frame(self)
        bf.grid(row=9, column=0, columnspan=2, pady=14)
        tk.Button(bf, text="Оформить",
                  font=(FF, 10), bg=COLORS["accent"], fg="white",
                  relief="flat", padx=14,
                  command=self._ok).pack(side="left", padx=6)
        tk.Button(bf, text="Отмена",
                  font=(FF, 10), relief="flat", padx=14,
                  command=self.destroy).pack(side="left")

    def _find_passenger(self):
        passport = self._passport_var.get().strip()
        if not passport:
            messagebox.showwarning("Введите номер паспорта", "", parent=self)
            return
        p = get_passenger_by_passport(passport)
        if p:
            self._passenger_id = p["passenger_id"]
            self._passenger_label.config(
                text=f"{p['last_name']} {p['first_name']}",
                fg=COLORS["success"])
        else:
            self._passenger_id = None
            self._passenger_label.config(
                text="Не найден — пассажир будет создан при оформлении",
                fg=COLORS["warning"] if False else COLORS["text_light"])
            self._ask_create_passenger(passport)

    def _ask_create_passenger(self, passport):
        if not messagebox.askyesno(
                "Пассажир не найден",
                f"Паспорт {passport} не найден в базе.\nЗарегистрировать нового пассажира?",
                parent=self):
            return
        dlg = _NewPassengerDialog(self, passport)
        self.wait_window(dlg)
        if dlg.result:
            try:
                new_id = add_passenger(**dlg.result)
                self._passenger_id = new_id
                self._passenger_label.config(
                    text=f"{dlg.result['last_name']} {dlg.result['first_name']} (новый)",
                    fg=COLORS["success"])
            except ValueError as e:
                messagebox.showerror("Ошибка", str(e), parent=self)

    def _ok(self):
        if not self._passenger_id:
            messagebox.showwarning("Пассажир не выбран",
                                   "Найдите пассажира по паспорту.", parent=self)
            return
        if not self._flight_var.get():
            messagebox.showwarning("Выберите рейс", "", parent=self)
            return
        if not self._seat_var.get().strip():
            messagebox.showwarning("Введите номер места", "", parent=self)
            return
        try:
            price = float(self._price_var.get().strip())
        except ValueError:
            messagebox.showerror("Ошибка", "Цена должна быть числом.", parent=self)
            return

        flight_id = self._flight_map[self._flight_var.get()]
        self.result = {
            "passenger_id": self._passenger_id,
            "flight_id": flight_id,
            "seat_number": self._seat_var.get().strip().upper(),
            "seat_class": self._class_var.get(),
            "price": price,
        }
        self.destroy()


class _NewPassengerDialog(tk.Toplevel):
    def __init__(self, parent, passport):
        super().__init__(parent)
        self.title("Новый пассажир")
        self.resizable(False, False)
        self.grab_set()
        self.result = None
        self._passport = passport
        self._build()

    def _build(self):
        tk.Label(self, text="Данные пассажира",
                 font=(FF, 13, "bold"),
                 fg=COLORS["text_main"]).grid(row=0, column=0, columnspan=2,
                                              sticky="w", padx=20, pady=(16, 12))
        tk.Frame(self, bg=COLORS["border"], height=1).grid(
            row=1, column=0, columnspan=2, sticky="ew", padx=20)

        self._vars = {}
        fields = [
            ("last_name", "Фамилия"),
            ("first_name", "Имя"),
            ("email", "Email"),
            ("phone", "Телефон"),
        ]
        for i, (key, label) in enumerate(fields):
            tk.Label(self, text=label,
                     font=(FF, 10), fg=COLORS["text_sub"],
                     anchor="w").grid(row=i + 2, column=0, sticky="w", padx=(20, 10), pady=6)
            var = tk.StringVar()
            self._vars[key] = var
            tk.Entry(self, textvariable=var,
                     font=(FF, 10), width=26, relief="flat",
                     highlightbackground=COLORS["border"],
                     highlightthickness=1).grid(row=i + 2, column=1,
                                                padx=(0, 20), pady=6, sticky="ew")

        tk.Label(self, text=f"Паспорт: {self._passport}",
                 font=(FF, 9), fg=COLORS["text_light"]).grid(
            row=6, column=1, sticky="w", padx=(0, 20), pady=(0, 8))

        self.columnconfigure(1, weight=1)
        bf = tk.Frame(self)
        bf.grid(row=7, column=0, columnspan=2, pady=14)
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
        self.result = {
            "last_name": vals["last_name"],
            "first_name": vals["first_name"],
            "passport_num": self._passport,
            "email": vals["email"],
            "phone": vals["phone"],
        }
        self.destroy()