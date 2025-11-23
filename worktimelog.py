import tkinter as tk
import ttkbootstrap as tb
from ttkbootstrap.constants import *
from tkinter import messagebox
from datetime import datetime
import os
import json

class TimeLoggerApplication:
    def __init__(self, root):
        self.root = root
        self.root.title("Munkaidő logoló by Zsolte")
        self.root.geometry('+{}+{}'.format(root.winfo_screenwidth() - 450, root.winfo_screenheight() - 650))

        # Mai dátum log fájl json formában
        self.date_str = datetime.now().strftime("%Y-%m-%d")
        self.filename = f"worktime_log_{self.date_str}.json"

        # Adatok formátuma: { "munkafolyamat neve": idő másodpercben }
        self.data = {}

        # Dátumválasztó
        tb.Label(root, text="Dátum kiválasztása:").grid(row=0, column=0, padx=5, pady=5, sticky='w')
        self.date_picker = tb.Entry(root)
        self.date_picker.grid(row=0, column=1, padx=5, pady=5, sticky='w')
        self.date_picker.insert(0, self.date_str)
        self.load_date_button = tb.Button(root, text="Betöltés", command=self.load_by_date, bootstyle=SECONDARY)
        self.load_date_button.grid(row=0, column=2, padx=5, pady=5)

        # Input beviteli mező és gomb
        self.entry = tb.Entry(root, width=35)
        self.entry.grid(row=1, column=0, columnspan=2, sticky='ew', padx=5, pady=5)
        self.add_button = tb.Button(root, text="Hozzáadás", command=self.add_task, bootstyle=SUCCESS)
        self.add_button.grid(row=1, column=2, padx=5, pady=5)

        # Lista feladatokkal (natív tkinter Listbox)
        self.listbox = tk.Listbox(root, height=12, width=50)
        self.listbox.grid(row=2, column=0, columnspan=3, padx=5, pady=5, sticky='ew')
        self.listbox.bind('<<ListboxSelect>>', self.on_select)

        # Indító és stop gomb, idő kijelző
        self.start_button = tb.Button(root, text="Start", command=self.start_timer, bootstyle=PRIMARY)
        self.stop_button = tb.Button(root, text="Stop", command=self.stop_timer, state='disabled', bootstyle=DANGER)
        self.timer_label = tb.Label(root, text="Idő: 00:00:00", bootstyle=INVERSE)

        self.start_button.grid(row=3, column=0, padx=5, pady=5, sticky='ew')
        self.stop_button.grid(row=3, column=1, padx=5, pady=5, sticky='ew')
        self.timer_label.grid(row=3, column=2, padx=5, pady=5, sticky='ew')

        # Idő hozzáadó gombok
        self.add_10min = tb.Button(root, text="+10 perc", command=lambda: self.add_time(600), bootstyle=INFO)
        self.add_30min = tb.Button(root, text="+30 perc", command=lambda: self.add_time(1800), bootstyle=INFO)
        self.add_1h = tb.Button(root, text="+1 óra", command=lambda: self.add_time(3600), bootstyle=INFO)

        self.add_10min.grid(row=4, column=0, padx=5, pady=5, sticky='ew')
        self.add_30min.grid(row=4, column=1, padx=5, pady=5, sticky='ew')
        self.add_1h.grid(row=4, column=2, padx=5, pady=5, sticky='ew')

        self.timer_running = False
        self.time_started = None
        self.selected_task = None
        self.elapsed_seconds = 0

        self.load_tasks()
        self.update_timer()

    def load_tasks(self):
        if os.path.exists(self.filename):
            with open(self.filename, "r", encoding="utf-8") as f:
                try:
                    self.data = json.load(f)
                except json.JSONDecodeError:
                    self.data = {}
        else:
            self.data = {}
        self.refresh_listbox()

    def save_tasks(self):
        with open(self.filename, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)

    def refresh_listbox(self):
        self.listbox.delete(0, 'end')
        for task, seconds in self.data.items():
            self.listbox.insert('end', f"{task} - {self.seconds_to_hms(seconds)}")

    def add_task(self):
        task_name = self.entry.get().strip()
        if not task_name:
            messagebox.showwarning("Figyelem", "Adj meg egy munkafolyamat nevet!")
            return
        if task_name in self.data:
            messagebox.showwarning("Figyelem", "Ez a munkafolyamat már létezik!")
            return
        self.data[task_name] = 0
        self.save_tasks()
        self.refresh_listbox()
        self.entry.delete(0, 'end')

    def on_select(self, event):
        selection = self.listbox.curselection()
        if selection:
            index = selection[0]
            task_str = self.listbox.get(index)
            task_name = task_str.split(' - ')[0]
            self.selected_task = task_name
            self.elapsed_seconds = self.data.get(task_name, 0)
            self.timer_label.config(text=f"Idő: {self.seconds_to_hms(self.elapsed_seconds)}")
        else:
            self.selected_task = None
            self.timer_label.config(text="Idő: 00:00:00")

    def start_timer(self):
        if not self.selected_task:
            messagebox.showwarning("Figyelem", "Válassz ki egy munkafolyamatot a listából!")
            return
        if self.timer_running:
            return
        self.timer_running = True
        self.time_started = datetime.now()
        self.start_button.config(state='disabled')
        self.stop_button.config(state='normal')

    def stop_timer(self):
        if not self.timer_running:
            return
        self.timer_running = False
        elapsed = (datetime.now() - self.time_started).total_seconds()
        self.elapsed_seconds += int(elapsed)
        self.data[self.selected_task] = self.elapsed_seconds
        self.save_tasks()
        self.refresh_listbox()
        self.timer_label.config(text=f"Idő: {self.seconds_to_hms(self.elapsed_seconds)}")
        self.start_button.config(state='normal')
        self.stop_button.config(state='disabled')

    def add_time(self, seconds):
        if not self.selected_task:
            messagebox.showwarning("Figyelem", "Válassz ki egy munkafolyamatot a listából!")
            return
        # Lehet hozzáadni időt futás közben, azonnal megjelenik
        if self.timer_running:
            elapsed = (datetime.now() - self.time_started).total_seconds()
            self.elapsed_seconds += int(elapsed)
            self.time_started = datetime.now()
        self.elapsed_seconds += seconds
        self.data[self.selected_task] = self.elapsed_seconds
        self.save_tasks()
        self.refresh_listbox()
        self.timer_label.config(text=f"Idő: {self.seconds_to_hms(self.elapsed_seconds)}")

    def load_by_date(self):
        date_value = self.date_picker.get().strip()
        try:
            datetime.strptime(date_value, "%Y-%m-%d")
        except ValueError:
            messagebox.showerror("Hibás dátum", "A dátum formátuma legyen: ÉÉÉÉ-HH-NN")
            return
        self.date_str = date_value
        self.filename = f"worktime_log_{self.date_str}.json"
        self.load_tasks()
        self.selected_task = None
        self.timer_running = False
        self.timer_label.config(text="Idő: 00:00:00")
        self.start_button.config(state='normal')
        self.stop_button.config(state='disabled')

    def update_timer(self):
        if self.timer_running and self.selected_task:
            elapsed = (datetime.now() - self.time_started).total_seconds()
            total = self.elapsed_seconds + int(elapsed)
            self.timer_label.config(text=f"Idő: {self.seconds_to_hms(total)}")
        self.root.after(1000, self.update_timer)

    def seconds_to_hms(self, seconds):
        hrs, rem = divmod(seconds, 3600)
        mins, secs = divmod(rem, 60)
        return f"{hrs:02}:{mins:02}:{secs:02}"

if __name__ == "__main__":
    root = tb.Window(themename="darkly")  # Többféle dark téma elérhető, pl. "darkly", "cyborg", "superhero"
    root.resizable(False, False) # Fix méret
    app = TimeLoggerApplication(root)
    root.mainloop()


#python -m PyInstaller --onefile --noconsole timelog_theme.py
# --> dist/timelog_theme.exe
