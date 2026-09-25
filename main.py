from __future__ import annotations

import csv
import sqlite3
from datetime import datetime
from pathlib import Path

from kivy.app import App
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.uix.scrollview import ScrollView
from kivy.uix.spinner import Spinner
from kivy.uix.textinput import TextInput

APP_NAME = "ANVI Garments"
VERSION = "8.9.18"
DATE_FMT = "%d-%m-%Y"
PASSWORD = "admin123"


def show_message(title: str, message: str) -> None:
    Popup(
        title=title,
        content=Label(text=message, halign="center", valign="middle"),
        size_hint=(0.86, 0.34),
    ).open()


class Database:
    def __init__(self, path: Path):
        self.path = path
        self.conn = sqlite3.connect(str(path))
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.create_tables()
        self.seed()

    def create_tables(self):
        self.conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS employees (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_code TEXT NOT NULL UNIQUE,
                name TEXT NOT NULL,
                mobile TEXT DEFAULT ''
            );
            CREATE TABLE IF NOT EXISTS work_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE
            );
            CREATE TABLE IF NOT EXISTS records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                work_date TEXT NOT NULL,
                employee_code TEXT DEFAULT '',
                worker_name TEXT NOT NULL,
                mobile TEXT DEFAULT '',
                work_item TEXT NOT NULL,
                quantity REAL NOT NULL,
                rate REAL NOT NULL,
                amount REAL NOT NULL,
                created_at TEXT NOT NULL
            );
            """
        )
        self.conn.commit()

    def seed(self):
        employees = [
            ("EMP001", "Sunita Patil", "9876543210"),
            ("EMP002", "Ramesh Jadhav", "9876543211"),
            ("EMP003", "Meena Shaikh", "9876543212"),
            ("EMP004", "Amit More", "9876543213"),
        ]
        items = ["Stitching", "Cutting", "Finishing", "Packing", "Quality Check"]
        self.conn.executemany(
            "INSERT OR IGNORE INTO employees(employee_code,name,mobile) VALUES(?,?,?)",
            employees,
        )
        self.conn.executemany(
            "INSERT OR IGNORE INTO work_items(name) VALUES(?)",
            [(x,) for x in items],
        )
        self.conn.commit()

    def employee_rows(self):
        return self.conn.execute(
            "SELECT employee_code,name,mobile FROM employees ORDER BY name"
        ).fetchall()

    def item_names(self):
        return [r[0] for r in self.conn.execute("SELECT name FROM work_items ORDER BY name")]

    def records(self, search=""):
        q = """
            SELECT id,work_date,employee_code,worker_name,mobile,work_item,quantity,rate,amount
            FROM records
        """
        args = []
        if search.strip():
            q += " WHERE worker_name LIKE ? OR employee_code LIKE ? OR mobile LIKE ?"
            s = f"%{search.strip()}%"
            args = [s, s, s]
        q += " ORDER BY id DESC"
        return self.conn.execute(q, args).fetchall()

    def add_record(self, values):
        self.conn.execute(
            """INSERT INTO records
            (work_date,employee_code,worker_name,mobile,work_item,quantity,rate,amount,created_at)
            VALUES(?,?,?,?,?,?,?,?,?)""",
            (*values, datetime.now().isoformat(timespec="seconds")),
        )
        self.conn.commit()

    def update_record(self, record_id, values):
        self.conn.execute(
            """UPDATE records SET worker_name=?,mobile=?,work_item=?,quantity=?,rate=?,amount=?
            WHERE id=?""",
            (*values, record_id),
        )
        self.conn.commit()

    def delete_record(self, record_id):
        self.conn.execute("DELETE FROM records WHERE id=?", (record_id,))
        self.conn.commit()

    def export_csv(self, target: Path):
        rows = self.records()
        with target.open("w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow(["Entry ID","Date","Employee ID","Worker Name","Mobile","Work Item","Quantity","Rate","Amount"])
            writer.writerows(rows)

    def close(self):
        self.conn.close()


class BaseScreen(Screen):
    def title_bar(self, title):
        box = BoxLayout(size_hint_y=None, height=dp(58), spacing=dp(8))
        box.add_widget(Label(text=title, font_size=dp(22), bold=True))
        return box

    def back_button(self):
        b = Button(text="BACK", size_hint_y=None, height=dp(48))
        b.bind(on_release=lambda *_: setattr(self.manager, "current", "dashboard"))
        return b


class LoginScreen(BaseScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        root = BoxLayout(orientation="vertical", padding=dp(28), spacing=dp(16))
        root.add_widget(Label(text=APP_NAME, font_size=dp(30), bold=True, size_hint_y=None, height=dp(70)))
        root.add_widget(Label(text="Stitching a Brighter Tomorrow", size_hint_y=None, height=dp(35)))
        self.password = TextInput(hint_text="Enter Password", password=True, multiline=False, size_hint_y=None, height=dp(50))
        root.add_widget(self.password)
        login = Button(text="LOGIN", size_hint_y=None, height=dp(55))
        login.bind(on_release=self.login)
        root.add_widget(login)
        root.add_widget(Label(text=f"Version {VERSION}", size_hint_y=None, height=dp(40)))
        self.add_widget(root)

    def login(self, *_):
        if self.password.text == PASSWORD:
            self.password.text = ""
            self.manager.current = "dashboard"
        else:
            show_message("Login Failed", "Invalid password.")


class DashboardScreen(BaseScreen):
    def on_pre_enter(self):
        self.clear_widgets()
        root = BoxLayout(orientation="vertical", padding=dp(18), spacing=dp(10))
        root.add_widget(self.title_bar(f"{APP_NAME} v{VERSION}"))
        for text, screen in [
            ("WORK ENTRY", "work"),
            ("SAVED RECORDS", "records"),
            ("EMPLOYEES", "employees"),
            ("WORK ITEMS", "items"),
            ("REPORTS", "reports"),
            ("BACKUP / EXPORT", "backup"),
            ("SETTINGS", "settings"),
            ("LOGOUT", "login"),
        ]:
            b = Button(text=text, size_hint_y=None, height=dp(52))
            b.bind(on_release=lambda _, s=screen: setattr(self.manager, "current", s))
            root.add_widget(b)
        self.add_widget(root)


class WorkEntryScreen(BaseScreen):
    def on_pre_enter(self):
        self.build()

    def build(self):
        self.clear_widgets()
        scroll = ScrollView()
        root = BoxLayout(orientation="vertical", padding=dp(18), spacing=dp(9), size_hint_y=None)
        root.bind(minimum_height=root.setter("height"))
        root.add_widget(self.title_bar("WORK ENTRY"))

        root.add_widget(Label(text="Work Date", size_hint_y=None, height=dp(28)))
        date_row = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(6))
        self.date_input = TextInput(text=datetime.now().strftime(DATE_FMT), multiline=False)
        date_btn = Button(text="TODAY", size_hint_x=None, width=dp(90))
        date_btn.bind(on_release=lambda *_: setattr(self.date_input, "text", datetime.now().strftime(DATE_FMT)))
        date_row.add_widget(self.date_input); date_row.add_widget(date_btn)
        root.add_widget(date_row)

        root.add_widget(Label(text="Employee", size_hint_y=None, height=dp(28)))
        self.employee_spinner = Spinner(text="Select Employee", size_hint_y=None, height=dp(48))
        self.employee_spinner.values = [r[1] for r in App.get_running_app().db.employee_rows()]
        self.employee_spinner.bind(text=self.employee_selected)
        root.add_widget(self.employee_spinner)

        self.emp_code = TextInput(hint_text="Employee ID", multiline=False, readonly=True, size_hint_y=None, height=dp(48))
        self.mobile = TextInput(hint_text="Mobile Number", multiline=False, size_hint_y=None, height=dp(48))
        root.add_widget(self.emp_code); root.add_widget(self.mobile)

        self.work_spinner = Spinner(text="Select Work Item", values=App.get_running_app().db.item_names(), size_hint_y=None, height=dp(48))
        root.add_widget(self.work_spinner)
        self.quantity = TextInput(hint_text="Quantity", multiline=False, input_filter="float", size_hint_y=None, height=dp(48))
        self.rate = TextInput(hint_text="Rate", multiline=False, input_filter="float", size_hint_y=None, height=dp(48))
        self.amount = Label(text="Amount: ₹ 0.00", font_size=dp(20), bold=True, size_hint_y=None, height=dp(50))
        root.add_widget(self.quantity); root.add_widget(self.rate); root.add_widget(self.amount)
        self.quantity.bind(text=self.calculate); self.rate.bind(text=self.calculate)

        save = Button(text="SAVE", size_hint_y=None, height=dp(55)); save.bind(on_release=self.save); root.add_widget(save)
        root.add_widget(self.back_button())
        scroll.add_widget(root); self.add_widget(scroll)

    def employee_selected(self, _, name):
        for code, employee, mobile in App.get_running_app().db.employee_rows():
            if employee == name:
                self.emp_code.text = code
                self.mobile.text = mobile
                break

    def calculate(self, *_):
        try:
            amount = float(self.quantity.text) * float(self.rate.text)
            self.amount.text = f"Amount: ₹ {amount:,.2f}"
        except ValueError:
            self.amount.text = "Amount: ₹ 0.00"

    def save(self, *_):
        try:
            date = datetime.strptime(self.date_input.text.strip(), DATE_FMT).strftime(DATE_FMT)
            if self.employee_spinner.text == "Select Employee": raise ValueError("Select an employee.")
            if self.work_spinner.text == "Select Work Item": raise ValueError("Select a work item.")
            quantity = float(self.quantity.text); rate = float(self.rate.text)
            if quantity < 0 or rate < 0: raise ValueError("Quantity and rate cannot be negative.")
            employee = next((r for r in App.get_running_app().db.employee_rows() if r[1] == self.employee_spinner.text), None)
            if not employee: raise ValueError("Employee not found.")
            App.get_running_app().db.add_record((date, employee[0], employee[1], self.mobile.text.strip(), self.work_spinner.text, quantity, rate, quantity * rate))
            show_message("Saved", "Work record saved successfully.")
            self.quantity.text = ""; self.rate.text = ""; self.calculate()
        except ValueError as exc:
            show_message("Validation", str(exc))


class RecordsScreen(BaseScreen):
    def on_pre_enter(self): self.build()

    def build(self):
        self.clear_widgets()
        root = BoxLayout(orientation="vertical", padding=dp(12), spacing=dp(8))
        root.add_widget(self.title_bar("SAVED RECORDS"))
        search = TextInput(hint_text="Search worker / ID / mobile", multiline=False, size_hint_y=None, height=dp(46))
        root.add_widget(search)
        scroll = ScrollView()
        content = BoxLayout(orientation="vertical", spacing=dp(8), size_hint_y=None)
        content.bind(minimum_height=content.setter("height"))
        self.content = content
        def refresh(*_): self.populate(search.text)
        search.bind(text=refresh)
        self.populate("")
        scroll.add_widget(content); root.add_widget(scroll); root.add_widget(self.back_button()); self.add_widget(root)

    def populate(self, search):
        self.content.clear_widgets()
        rows = App.get_running_app().db.records(search)
        if not rows:
            self.content.add_widget(Label(text="No saved records", size_hint_y=None, height=dp(50)))
            return
        for row in rows:
            rid, date, code, name, mobile, work, qty, rate, amount = row
            box = BoxLayout(orientation="vertical", size_hint_y=None, height=dp(150), padding=dp(6))
            box.add_widget(Label(text=f"#{rid}  {date}  {name}", size_hint_y=None, height=dp(28)))
            box.add_widget(Label(text=f"{code} | {mobile} | {work}", size_hint_y=None, height=dp(26)))
            box.add_widget(Label(text=f"Qty: {qty:g} | Rate: ₹{rate:g} | Amount: ₹{amount:,.2f}", size_hint_y=None, height=dp(30)))
            buttons = BoxLayout(size_hint_y=None, height=dp(42), spacing=dp(6))
            edit = Button(text="EDIT"); edit.bind(on_release=lambda _, r=row: self.edit_record(r))
            delete = Button(text="DELETE"); delete.bind(on_release=lambda _, rid=rid: self.delete(rid))
            buttons.add_widget(edit); buttons.add_widget(delete); box.add_widget(buttons); self.content.add_widget(box)

    def delete(self, rid):
        App.get_running_app().db.delete_record(rid); self.build()

    def edit_record(self, row):
        rid, date, code, name, mobile, work, qty, rate, amount = row
        root = BoxLayout(orientation="vertical", padding=dp(12), spacing=dp(7))
        date_field = TextInput(text=date, readonly=True, size_hint_y=None, height=dp(44))
        worker = TextInput(text=name, multiline=False, size_hint_y=None, height=dp(44))
        mobile_field = TextInput(text=mobile, multiline=False, size_hint_y=None, height=dp(44))
        work_field = Spinner(text=work, values=App.get_running_app().db.item_names(), size_hint_y=None, height=dp(44))
        qty_field = TextInput(text=str(qty), multiline=False, input_filter="float", size_hint_y=None, height=dp(44))
        rate_field = TextInput(text=str(rate), multiline=False, input_filter="float", size_hint_y=None, height=dp(44))
        for label, field in [("Date (locked)", date_field),("Worker Name",worker),("Mobile",mobile_field),("Work Item",work_field),("Quantity",qty_field),("Rate",rate_field)]:
            root.add_widget(Label(text=label, size_hint_y=None, height=dp(24))); root.add_widget(field)
        buttons = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(6))
        popup = Popup(title="Edit Saved Record", content=root, size_hint=(0.94, 0.92))
        save = Button(text="SAVE")
        cancel = Button(text="CANCEL")
        buttons.add_widget(save); buttons.add_widget(cancel); root.add_widget(buttons)
        cancel.bind(on_release=popup.dismiss)
        def save_edit(*_):
            try:
                q=float(qty_field.text); r=float(rate_field.text)
                if q < 0 or r < 0: raise ValueError("Quantity and rate cannot be negative.")
                App.get_running_app().db.update_record(rid, (worker.text.strip(), mobile_field.text.strip(), work_field.text, q, r, q*r))
                popup.dismiss(); self.build(); show_message("Updated", "Record updated successfully.")
            except ValueError as exc: show_message("Validation", str(exc))
        save.bind(on_release=save_edit)
        popup.open()


class SimpleListScreen(BaseScreen):
    title = "LIST"
    def on_pre_enter(self):
        self.clear_widgets(); root=BoxLayout(orientation="vertical",padding=dp(18),spacing=dp(8)); root.add_widget(self.title_bar(self.title)); self.populate(root); root.add_widget(self.back_button()); self.add_widget(root)
    def populate(self, root): pass


class EmployeesScreen(SimpleListScreen):
    title="EMPLOYEES"
    def populate(self, root):
        for code,name,mobile in App.get_running_app().db.employee_rows(): root.add_widget(Label(text=f"{code} | {name} | {mobile}",size_hint_y=None,height=dp(42)))


class ItemsScreen(SimpleListScreen):
    title="WORK ITEMS"
    def populate(self, root):
        for item in App.get_running_app().db.item_names(): root.add_widget(Label(text=item,size_hint_y=None,height=dp(42)))


class ReportsScreen(BaseScreen):
    def on_pre_enter(self):
        self.clear_widgets(); rows=App.get_running_app().db.records(); total=sum(r[8] for r in rows)
        root=BoxLayout(orientation="vertical",padding=dp(20),spacing=dp(14)); root.add_widget(self.title_bar("REPORTS")); root.add_widget(Label(text=f"Total Records: {len(rows)}",size_hint_y=None,height=dp(45))); root.add_widget(Label(text=f"Total Amount: ₹ {total:,.2f}",font_size=dp(22),bold=True,size_hint_y=None,height=dp(55))); root.add_widget(self.back_button()); self.add_widget(root)


class BackupScreen(BaseScreen):
    def on_pre_enter(self):
        self.clear_widgets(); root=BoxLayout(orientation="vertical",padding=dp(20),spacing=dp(12)); root.add_widget(self.title_bar("BACKUP / EXPORT")); export=Button(text="EXPORT CSV",size_hint_y=None,height=dp(52)); export.bind(on_release=self.export); root.add_widget(export); root.add_widget(Label(text="CSV export is saved in the app's private storage.",halign="center")); root.add_widget(self.back_button()); self.add_widget(root)
    def export(self,*_):
        target=Path(App.get_running_app().user_data_dir)/f"ANVI_Garments_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"; App.get_running_app().db.export_csv(target); show_message("Backup Created", str(target))


class SettingsScreen(BaseScreen):
    def on_pre_enter(self):
        self.clear_widgets(); root=BoxLayout(orientation="vertical",padding=dp(20),spacing=dp(12)); root.add_widget(self.title_bar("SETTINGS")); root.add_widget(Label(text=f"{APP_NAME}\nVersion {VERSION}\nLocal SQLite database enabled",halign="center")); root.add_widget(self.back_button()); self.add_widget(root)


class ANVIGarmentsApp(App):
    def build(self):
        self.title=APP_NAME
        self.db=Database(Path(self.user_data_dir)/"anvi_garments.db")
        sm=ScreenManager()
        for cls,name in [(LoginScreen,"login"),(DashboardScreen,"dashboard"),(WorkEntryScreen,"work"),(RecordsScreen,"records"),(EmployeesScreen,"employees"),(ItemsScreen,"items"),(ReportsScreen,"reports"),(BackupScreen,"backup"),(SettingsScreen,"settings")]: sm.add_widget(cls(name=name))
        return sm
    def on_stop(self):
        if hasattr(self,"db"): self.db.close()


if __name__ == "__main__":
    ANVIGarmentsApp().run()
