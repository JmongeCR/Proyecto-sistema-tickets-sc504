import tkinter as tk
from tkinter import messagebox
try:
    from tkinter import ttk
    HAS_COMBO = hasattr(ttk, "Combobox")
except Exception:
    ttk = None
    HAS_COMBO = False

import oracledb
from db.connection import connect_to_db


def open_assign_ticket_window(parent, ticket_id: int):
    win = tk.Toplevel(parent)
    win.title(f"Asignar Técnico")
    win.geometry("360x200")
    tk.Label(win, text=f"Ticket #{ticket_id}", font=("Arial", 12, "bold")).pack(pady=(8, 2))
    tk.Label(win, text="Seleccione técnico:").pack()

    combo = None
    tecnicos_dict = {}

    conn = cur = None
    try:
        conn = connect_to_db(); cur = conn.cursor()
        rc = cur.var(oracledb.DB_TYPE_CURSOR)
        # Debe devolver (ID_USUARIO, NOMBRE_COMPLETO)
        cur.callproc("PKG_UI_LISTAS.LISTAR_TECNICOS_ACTIVOS", [rc])
        rows = rc.getvalue().fetchall()  # [(id, nombre), ...]
        names = []
        for r in rows:
            # Soporta 2 o más columnas; tomamos primeras 2
            tid, tname = int(r[0]), str(r[1])
            tecnicos_dict[tname] = tid
            names.append(tname)

        if HAS_COMBO:
            combo = ttk.Combobox(win, state="readonly", values=names)
            if names: combo.current(0)
            combo.pack(pady=8)
        else:
            var = tk.StringVar(win, value=(names[0] if names else ""))
            combo = tk.OptionMenu(win, var, *names)
            combo.pack(pady=8)
            combo.get = var.get  # unificar API

    except Exception as e:
        messagebox.showerror("Técnicos", f"No se pudieron cargar técnicos:\n{e}")
        try:
            if cur: cur.close()
            if conn: conn.close()
        except: pass
        win.destroy()
        return
    finally:
        try:
            if cur: cur.close()
            if conn: conn.close()
        except: pass

    def do_assign():
        nombre = combo.get()
        if not nombre:
            messagebox.showwarning("Asignar", "Seleccione un técnico.")
            return
        id_tecnico = tecnicos_dict[nombre]
        conn2 = cur2 = None
        try:
            conn2 = connect_to_db(); cur2 = conn2.cursor()
            cur2.callproc("PKG_TIQUETES.ASIGNAR_TICKET", [int(ticket_id), int(id_tecnico)])
            conn2.commit()
            messagebox.showinfo("Asignación", "Técnico asignado correctamente.")
            win.destroy()
        except Exception as e:
            messagebox.showerror("Asignación", f"No se pudo asignar:\n{e}")
        finally:
            try:
                if cur2: cur2.close()
                if conn2: conn2.close()
            except: pass

    tk.Button(win, text="Asignar", command=do_assign).pack(pady=(8, 6))
    tk.Button(win, text="Cancelar", command=win.destroy).pack()
    return win
