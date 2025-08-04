import tkinter as tk
from tkinter import ttk, messagebox
from db.connection import connect_to_db
import oracledb

def open_assign_ticket_window(parent, ticket_id):
    win = tk.Toplevel(parent)
    win.title("Asignar Técnico")
    win.geometry("350x250")

    tk.Label(win, text=f"Asignar a Ticket ID: {ticket_id}", font=("Arial", 11, "bold")).pack(pady=10)
    
    tk.Label(win, text="Seleccione Técnico:").pack()
    combo_tecnico = ttk.Combobox(win, state="readonly", width=35)
    combo_tecnico.pack(pady=10)

    tecnicos_dict = {}

    conn = connect_to_db()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT u.ID_USUARIO, u.NOMBRE || ' ' || u.APELLIDO1 AS NOMBRE_COMPLETO
                FROM TKT_USUARIO u
                JOIN TKT_ROL r ON u.ID_ROL = r.ID_ROL
                WHERE LOWER(r.NOMBRE_ROL) = 'técnico'
            """)
            tecnicos = cur.fetchall()
            for t in tecnicos:
                tecnicos_dict[f"{t[0]} - {t[1]}"] = t[0]
            combo_tecnico['values'] = list(tecnicos_dict.keys())
        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar técnicos: {e}")
        finally:
            cur.close()
            conn.close()

    def asignar():
        seleccionado = combo_tecnico.get()
        if not seleccionado:
            messagebox.showwarning("Advertencia", "Debe seleccionar un técnico")
            return

        id_tecnico = tecnicos_dict[seleccionado]

        conn = connect_to_db()
        if conn:
            try:
                cur = conn.cursor()
                cur.callproc("PKG_TIQUETES.ASIGNAR_TICKET", [ticket_id, id_tecnico])
                conn.commit()
                messagebox.showinfo("Éxito", "Técnico asignado correctamente")
                win.destroy()
            except Exception as e:
                messagebox.showerror("Error", f"Error al asignar: {e}")
            finally:
                cur.close()
                conn.close()

    tk.Button(win, text="Asignar Técnico", command=asignar).pack(pady=15)
    tk.Button(win, text="Cancelar", command=win.destroy).pack()

    win.mainloop()
