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


def _load_options():
    """Carga PRIORIDADES y CATEGORIAS via PKG_UI_LISTAS."""
    conn = cur = None
    out = {"prioridades": {}, "categorias": {}}
    try:
        conn = connect_to_db(); cur = conn.cursor()
        for proc, key in [
            ("PKG_UI_LISTAS.LISTAR_PRIORIDADES", "prioridades"),
            ("PKG_UI_LISTAS.LISTAR_CATEGORIAS",  "categorias"),
        ]:
            rc = cur.var(oracledb.DB_TYPE_CURSOR)
            cur.callproc(proc, [rc])
            out[key] = {str(r[1]): int(r[0]) for r in rc.getvalue().fetchall()}
    finally:
        try:
            if cur: cur.close()
            if conn: conn.close()
        except: pass
    return out


def open_create_ticket_window(parent, user_id: int):
    w = tk.Toplevel(parent)
    w.title("Crear Nuevo Ticket")
    w.geometry("420x360")

    tk.Label(w, text="Asunto:").pack(anchor="w", padx=10, pady=(10, 2))
    ent_asunto = tk.Entry(w); ent_asunto.pack(fill="x", padx=10)

    tk.Label(w, text="Descripción:").pack(anchor="w", padx=10, pady=(10, 2))
    txt_desc = tk.Text(w, height=6); txt_desc.pack(fill="both", expand=True, padx=10)

    opts = _load_options()

    def mk_combo(lbl, items):
        tk.Label(w, text=lbl).pack(anchor="w", padx=10, pady=(8, 2))
        names = list(items.keys())
        if HAS_COMBO:
            cb = ttk.Combobox(w, state="readonly", values=names)
            if names: cb.current(0)
            cb.pack(fill="x", padx=10)
            cb.get_id = lambda: items.get(cb.get())
        else:
            var = tk.StringVar(w, value=(names[0] if names else ""))
            cb = tk.OptionMenu(w, var, *names)
            cb.pack(padx=10)
            cb.get_id = lambda: items.get(var.get())
        return cb

    cb_pri = mk_combo("Prioridad:", opts["prioridades"])
    cb_cat = mk_combo("Categoría:", opts["categorias"])

    def crear():
        asunto = ent_asunto.get().strip()
        desc   = txt_desc.get("1.0", "end-1c").strip()
        if not asunto:
            messagebox.showerror("Validación", "Digite un asunto.")
            return
        id_pri = cb_pri.get_id()
        id_cat = cb_cat.get_id()

        conn = cur = None
        try:
            conn = connect_to_db(); cur = conn.cursor()
            # Intento 1: (asunto, desc, id_usuario, id_estado, id_prioridad, id_categoria, o_id OUT)
            o_id = cur.var(oracledb.DB_TYPE_NUMBER)
            try:
                cur.callproc("PKG_TIQUETES.CREAR_TICKET",
                             [asunto, desc, int(user_id), 1, int(id_pri), int(id_cat), o_id])
            except oracledb.DatabaseError:
                # Intento 2: sin estado explícito, con OUT
                try:
                    cur.callproc("PKG_TIQUETES.CREAR_TICKET",
                                 [asunto, desc, int(user_id), int(id_pri), int(id_cat), o_id])
                except oracledb.DatabaseError:
                    # Intento 3: sin OUT (lo maneja el paquete)
                    cur.callproc("PKG_TIQUETES.CREAR_TICKET",
                                 [asunto, desc, int(user_id), 1, int(id_pri), int(id_cat)])
            conn.commit()
            messagebox.showinfo("Ticket", "Ticket creado correctamente.")
            w.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo crear el ticket:\n{e}")
        finally:
            try:
                if cur: cur.close()
                if conn: conn.close()
            except: pass

    btn_bar = tk.Frame(w); btn_bar.pack(fill="x", pady=10)
    tk.Button(btn_bar, text="Crear Ticket", command=crear).pack(side="left", padx=10)
    tk.Button(btn_bar, text="Cancelar", command=w.destroy).pack(side="left")

    return w
