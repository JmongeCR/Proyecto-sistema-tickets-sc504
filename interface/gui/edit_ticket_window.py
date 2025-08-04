import tkinter as tk
from tkinter import ttk, messagebox
from db.connection import connect_to_db
import oracledb

def open_edit_ticket_window(parent, ticket_data):
    ticket_id, asunto, _, estado_actual, prioridad_actual, categoria_actual, *_ = ticket_data

    win = tk.Toplevel(parent)
    win.title(f"Editar Ticket #{ticket_id}")
    win.geometry("400x350")

    tk.Label(win, text=f"Asunto: {asunto}", font=("Arial", 10, "bold")).pack(pady=5)

    tk.Label(win, text="Nuevo Estado:").pack()
    estado_cb = ttk.Combobox(win, state="readonly")
    estado_cb.pack()

    tk.Label(win, text="Nueva Prioridad:").pack()
    prioridad_cb = ttk.Combobox(win, state="readonly")
    prioridad_cb.pack()

    tk.Label(win, text="Nueva Categoría:").pack()
    categoria_cb = ttk.Combobox(win, state="readonly")
    categoria_cb.pack()

    conn = connect_to_db()
    estados = {}
    prioridades = {}
    categorias = {}
    if conn:
        try:
            cur = conn.cursor()

            cur.execute("SELECT ID_ESTADO, NOMBRE_ESTADO FROM TKT_ESTADO")
            for row in cur.fetchall():
                estados[row[1]] = row[0]
            estado_cb['values'] = list(estados.keys())
            estado_cb.set(estado_actual)

            cur.execute("SELECT ID_PRIORIDAD, NIVEL_PRIORIDAD FROM TKT_PRIORIDAD")
            for row in cur.fetchall():
                prioridades[row[1]] = row[0]
            prioridad_cb['values'] = list(prioridades.keys())
            prioridad_cb.set(prioridad_actual)

            cur.execute("SELECT ID_CATEGORIA, NOMBRE_CATEGORIA FROM TKT_CATEGORIA")
            for row in cur.fetchall():
                categorias[row[1]] = row[0]
            categoria_cb['values'] = list(categorias.keys())
            categoria_cb.set(categoria_actual)

        except Exception as e:
            messagebox.showerror("Error", str(e))
        finally:
            cur.close()
            conn.close()

    def guardar_cambios():
        nuevo_estado = estados.get(estado_cb.get())
        nueva_prioridad = prioridades.get(prioridad_cb.get())
        nueva_categoria = categorias.get(categoria_cb.get())

        if not (nuevo_estado and nueva_prioridad and nueva_categoria):
            messagebox.showerror("Error", "Todos los campos deben estar seleccionados.")
            return

        conn = connect_to_db()
        if conn:
            try:
                cur = conn.cursor()
                cur.callproc("PKG_TIQUETES.ACTUALIZAR_TICKET", [
                    ticket_id, asunto, "", nuevo_estado, nueva_prioridad, nueva_categoria
                ])
                conn.commit()
                messagebox.showinfo("Éxito", "Ticket actualizado correctamente.")
                win.destroy()
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo actualizar el ticket: {e}")
            finally:
                cur.close()
                conn.close()

    tk.Button(win, text="Guardar Cambios", command=guardar_cambios).pack(pady=10)
    tk.Button(win, text="Cancelar", command=win.destroy).pack()

    win.mainloop()
