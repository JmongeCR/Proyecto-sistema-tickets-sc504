# gui/ui_basic.py
# Utilidades visuales 100% Tk: ListTable (tabla con Listbox monoespaciado) y SimpleCombo.


import tkinter as tk
from tkinter import messagebox


_MONO = ("Consolas", 10)


class ListTable(tk.Frame):
"""
Tabla simple con encabezados y una Listbox formateada en columnas fijas.
- headers: lista de títulos
- widths: lista con el ancho de cada columna en caracteres (opcional)
- on_row_double_click: callback(row_dict) al doble click
"""
def __init__(self, master, headers, widths=None, on_row_double_click=None):
super().__init__(master)
self.headers = headers
self.widths = widths or [20] * len(headers)
self.on_row_double_click = on_row_double_click


# Encabezado
header_frame = tk.Frame(self)
header_frame.pack(fill=tk.X)
for i, (h, w) in enumerate(zip(self.headers, self.widths)):
lbl = tk.Label(header_frame, text=h, font=_MONO, bd=1, relief=tk.SOLID)
lbl.pack(side=tk.LEFT, fill=tk.Y)
lbl.configure(width=w)


# Cuerpo con scroll
body_frame = tk.Frame(self)
body_frame.pack(fill=tk.BOTH, expand=True)


self.scroll_y = tk.Scrollbar(body_frame, orient=tk.VERTICAL)
self.scroll_x = tk.Scrollbar(body_frame, orient=tk.HORIZONTAL)


self.listbox = tk.Listbox(body_frame, font=_MONO, activestyle='none')
self.listbox.config(yscrollcommand=self.scroll_y.set, xscrollcommand=self.scroll_x.set)
self.scroll_y.config(command=self.listbox.yview)
self.scroll_x.config(command=self.listbox.xview)


self.listbox.bind('<Double-Button-1>', self._on_double)


self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
self.scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
self.scroll_x.pack(side=tk.BOTTOM, fill=tk.X)


self._rows = [] # lista de dicts por fila


def clear(self):
self.listbox.delete(0, tk.END)
self._rows.clear()


def _fmt_row(self, row_values):
# Ajusta cada columna a un ancho fijo (relleno con espacios)
cols = []
for v, w in zip(row_values, self.widths):
s = str(v) if v is not None else ""
if len(s) > w:
s = s[:max(0, w-1)] + "…"
cols.append(s.ljust(w))
return " ".join(cols)


def insert_dicts(self, rows, order=None):
""" rows: lista de diccionarios; order: lista de keys en el orden de columnas """
self.clear()
order = order or self.headers
for r in rows:
line = self._fmt_row([r.get(k, "") for k in order])
self.var.set("")