import tkinter as tk
from tkinter import ttk, messagebox
from db.connection import connect_to_db
import oracledb

def open_create_ticket_window(parent, user_id):
    window = tk.Toplevel(parent)
    window.title("Crear Nuevo Ticket")
    window.geometry("400x400")

    tk.Label(window, text="Asunto:").pack()
    entry_asunto = tk.Entry(window, width=50)
    entry_asunto.pack()

    tk.Label(window, text="Descripción:").pack()
    entry_desc = tk.Text(window, height=5, width=50)
    entry_desc.pack()

    tk.Label(window, text="Prioridad:").pack()
    combo_prioridad = ttk.Combobox(window)
    combo_prioridad.pack()

    tk.Label(window, text="Categoría:").pack()
    combo_categoria = ttk.Combobox(window)
    combo_categoria.pack()

    def cargar_opciones():
        conn = connect_to_db()
        if conn:
            try:
                cur = conn.cursor()

                cur.execute("SELECT ID_PRIORIDAD, NIVEL_PRIORIDAD FROM TKT_PRIORIDAD")
                prioridades = cur.fetchall()
                combo_prioridad["values"] = [f"{r[0]} - {r[1]}" for r in prioridades]
                if prioridades:
                    combo_prioridad.current(0)

                cur.execute("SELECT ID_CATEGORIA, NOMBRE_CATEGORIA FROM TKT_CATEGORIA")
                categorias = cur.fetchall()
                combo_categoria["values"] = [f"{r[0]} - {r[1]}" for r in categorias]
                if categorias:
                    combo_categoria.current(0)
            except Exception as e:
                messagebox.showerror("Error", f"No se pudieron cargar las opciones: {e}")
            finally:
                cur.close()
                conn.close()

    def crear_ticket():
        asunto = entry_asunto.get()
        descripcion = entry_desc.get("1.0", tk.END).strip()
        id_prioridad = int(combo_prioridad.get().split(" - ")[0])
        id_categoria = int(combo_categoria.get().split(" - ")[0])

        conn = connect_to_db()
        if conn:
            try:
                cur = conn.cursor()
                cur.callproc("PKG_TIQUETES.CREAR_TICKET", [
                    asunto, descripcion, user_id, 1, id_prioridad, id_categoria
                ])
                conn.commit()
                messagebox.showinfo("Éxito", "Ticket creado correctamente")
                window.destroy()
            except Exception as e:
                messagebox.showerror("Error", f"Error al crear ticket: {e}")
            finally:
                cur.close()
                conn.close()

    tk.Button(window, text="Crear Ticket", command=crear_ticket).pack(pady=10)

    cargar_opciones()
    window.mainloop()
