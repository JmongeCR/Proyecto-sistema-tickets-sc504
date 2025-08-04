import tkinter as tk
from tkinter import ttk, messagebox
from db.connection import connect_to_db

def open_audit_window():
    win = tk.Toplevel()
    win.title("Auditoría del Sistema")
    win.geometry("900x450")

    notebook = ttk.Notebook(win)
    notebook.pack(fill=tk.BOTH, expand=True)

    # Cambios de estado
    frame_tickets = ttk.Frame(notebook)
    notebook.add(frame_tickets, text="Auditoría de Tickets")

    tree_tickets = ttk.Treeview(frame_tickets, columns=("ID Log", "ID Ticket", "Anterior", "Nuevo", "Fecha"), show="headings")
    for col in tree_tickets["columns"]:
        tree_tickets.heading(col, text=col)
        tree_tickets.column(col, width=150)
    tree_tickets.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    # Auditoría de usuarios
    frame_users = ttk.Frame(notebook)
    notebook.add(frame_users, text="Auditoría de Usuarios")

    tree_users = ttk.Treeview(frame_users, columns=("ID Auditoría", "ID Usuario", "Correo", "Fecha Registro"), show="headings")
    for col in tree_users["columns"]:
        tree_users.heading(col, text=col)
        tree_users.column(col, width=200)
    tree_users.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    def cargar_auditoria():
        conn = connect_to_db()
        if conn:
            try:
                cur = conn.cursor()

                # Cambios de estado
                cur.execute("SELECT ID_LOG, ID_TICKET, ESTADO_ANTERIOR, ESTADO_NUEVO, TO_CHAR(FECHA_CAMBIO, 'DD-MM-YYYY HH24:MI') FROM AUD_TICKET ORDER BY FECHA_CAMBIO DESC")
                for row in cur.fetchall():
                    tree_tickets.insert("", tk.END, values=row)

                # Auditoría de usuarios
                cur.execute("SELECT ID_AUD, ID_USUARIO, CORREO, TO_CHAR(FECHA_REGISTRO, 'DD-MM-YYYY HH24:MI') FROM AUD_USUARIO ORDER BY FECHA_REGISTRO DESC")
                for row in cur.fetchall():
                    tree_users.insert("", tk.END, values=row)

            except Exception as e:
                messagebox.showerror("Error", f"No se pudo cargar la auditoría: {e}")
            finally:
                cur.close()
                conn.close()

    cargar_auditoria()
    tk.Button(win, text="Cerrar", command=win.destroy, bg="red", fg="white").pack(pady=10)
    win.mainloop()
