# gui/edit_user_window.py
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

def open_edit_user_window(parent, user_tuple):
    # user_tuple: (ID, Nombre, Ap1, Ap2, Correo, Telefono, Rol)
    uid = int(user_tuple[0])

    win = tk.Toplevel(parent)
    win.title(f"Editar Usuario #{uid}")
    win.geometry("420x420")

    labels = ["Nombre","Primer Apellido","Segundo Apellido","Correo","Teléfono","Rol"]
    entries = {}

    for i, lab in enumerate(labels[:-1]):  # sin Rol
        tk.Label(win, text=lab).pack(anchor="w", padx=10, pady=(8 if i==0 else 4,2))
        e = tk.Entry(win); e.pack(fill="x", padx=10)
        entries[lab] = e
    entries["Nombre"].insert(0, str(user_tuple[1] or ""))
    entries["Primer Apellido"].insert(0, str(user_tuple[2] or ""))
    entries["Segundo Apellido"].insert(0, str(user_tuple[3] or ""))
    entries["Correo"].insert(0, str(user_tuple[4] or ""))
    entries["Teléfono"].insert(0, str(user_tuple[5] or ""))

    tk.Label(win, text="Rol").pack(anchor="w", padx=10, pady=(8,2))
    roles = {}
    try:
        conn = connect_to_db(); cur = conn.cursor()
        rc = cur.var(oracledb.DB_TYPE_CURSOR)
        cur.callproc("PKG_UI_LISTAS.LISTAR_ROLES", [rc])
        for rid, rname in rc.getvalue().fetchall():
            roles[str(rname)] = int(rid)
    finally:
        try: cur.close(); conn.close()
        except: pass

    names = list(roles.keys())
    if HAS_COMBO:
        cb = ttk.Combobox(win, state="readonly", values=names)
        if names: cb.current(max(0, names.index(user_tuple[6])) if user_tuple[6] in names else 0)
        cb.pack(fill="x", padx=10)
        get_rol = lambda: roles.get(cb.get())
    else:
        var = tk.StringVar(win, value=(user_tuple[6] if user_tuple[6] in names else (names[0] if names else "")))
        cb = tk.OptionMenu(win, var, *names); cb.pack(padx=10)
        get_rol = lambda: roles.get(var.get())

    def guardar():
        nombre  = entries["Nombre"].get().strip()
        ap1     = entries["Primer Apellido"].get().strip()
        ap2     = entries["Segundo Apellido"].get().strip() or None
        correo  = entries["Correo"].get().strip().lower()
        tel     = entries["Teléfono"].get().strip() or None
        id_rol  = get_rol()

        if not (nombre and ap1 and correo and id_rol):
            messagebox.showerror("Validación", "Complete los campos obligatorios.")
        else:
            conn = cur = None
            try:
                conn = connect_to_db(); cur = conn.cursor()
                # Firma 1 (sin contraseña):
                try:
                    cur.callproc("PKG_USUARIOS.ACTUALIZAR_USUARIO",
                                 [uid, nombre, ap1, ap2, correo, tel, id_rol])
                except oracledb.DatabaseError:
                    # Firma 2 (con contraseña opcional en medio):
                    cur.callproc("PKG_USUARIOS.ACTUALIZAR_USUARIO",
                                 [uid, nombre, ap1, ap2, correo, None, tel, id_rol])
                conn.commit()
                messagebox.showinfo("Usuario", "Datos actualizados.")
                win.destroy()
            except Exception as e:
                messagebox.showerror("Usuario", f"No se pudo actualizar:\n{e}")
            finally:
                try:
                    if cur: cur.close()
                    if conn: conn.close()
                except: pass

    tk.Button(win, text="Guardar", command=guardar).pack(pady=12)
    tk.Button(win, text="Cancelar", command=win.destroy).pack()
    return win
