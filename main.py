import tkinter as tk
from database.connection import init_db
from gui.main_window import MainWindow

def main():
    init_db()

    root = tk.Tk()
    app = MainWindow(root)
    root.mainloop()

if __name__ == "__main__":
    main()