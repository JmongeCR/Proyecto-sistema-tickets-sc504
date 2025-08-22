# gui/manage_users_window.py
import tkinter as tk
from tkinter import messagebox
from threading import Thread

try:
    from tkinter import ttk
    HAS_TTK = hasattr(ttk, "Treeview")
except Exception:
    ttk = None
    HAS_TTK = False

import oracledb
from db.connection import connect_to_db


# ---------- utilidades ----------
def _widget_alive(w):
    try:
        return bool(w) and w.winfo_exists()
    except Exception:
        return False

def _safe_after(w, ms, fn):
    try:
        if _widget_alive(w):
            w.after(ms, fn)
    except Exception:
        pass

def _run_in_thread(win, fn, on_done):
    def runner():
        try:
            res, err = fn(), None
        except Exception as e:
            res, err = None, e
        _safe_after(win, 0, lambda: on_done(res, err))
    Thread(target=runner, daemon=True).start()

def _norm_role_name(s: str) -> str:
    if s is None:
        return ""
    s = s.strip().lower()
    # normaliza acentos comunes
    s = (s.replace("á", "a")
           .replace("é", "e")
           .replace("í", "i")
           .replace("ó", "o")
           .replace("ú", "u"))
    return s


# ---------- detección de esquema ----------
LIKELY_IDS       = ("ID_USUARIO", "USUARIO_ID", "ID", "IDUSER")
LIKELY_NOMBRES   = ("NOMBRE", "NAME", "FIRST_NAME")
LIKELY_AP1       = ("APELLIDO1", "AP1", "PRIMER_APELLIDO", "LAST_NAME", "SURNAME")
LIKELY_AP2       = ("APELLIDO2", "AP2", "SEGUNDO_APELLIDO")
LIKELY_CORREOS   = ("CORREO", "EMAIL", "USUARIO_EMAIL", "MAIL", "E_MAIL", "USERNAME")
LIKELY_ROLES     = ("ROL", "ROLE", "TIPO", "TIPO_USUARIO", "PROFILE", "NOMBRE_ROL")
LIKELY_ID_ROL    = ("ID_ROL", "ROL_ID")
LIKELY_ACTIVOS   = ("ACTIVO", "ENABLED", "ESTADO", "STATUS", "IS_ACTIVE", "HABILITADO")

def _detect_columns(colset):
    """Devuelve nombres reales existentes en la tabla para cada campo lógico."""
    def pick(cands):
        for c in cands:
            if c in colset:
                return c
        return None
    return {
        "ID":       pick(LIKELY_IDS),
        "NOMBRE":   pick(LIKELY_NOMBRES),
        "AP1":      pick(LIKELY_AP1),
        "AP2":      pick(LIKELY_AP2),
        "CORREO":   pick(LIKELY_CORREOS),
        "ROL":      pick(LIKELY_ROLES),
        "ID_ROL":   pick(LIKELY_ID_ROL),
        "ACTIVO":   pick(LIKELY_ACTIVOS),
    }


# ---------- mapeo de roles ----------
def _load_roles(cur):
    id_to_name = {}
    name_to_id = {}
    try:
        cur.execute("SELECT ID_ROL, NOMBRE_ROL FROM TKT_ROL ORDER BY ID_ROL")
        for rid, rname in cur.fetchall():
            id_to_name[int(rid)] = str(rname)
            name_to_id[_norm_role_name(str(rname))] = int(rid)
    except Exception:
        # si no existe tabla de roles, usa defaults
        defaults = [(1, "Admin"), (2, "Técnico"), (3, "Usuario")]
        for rid, rname in defaults:
            id_to_name[rid] = rname
            name_to_id[_norm_role_name(rname)] = rid
    return {"id_to_name": id_to_name, "name_to_id": name_to_id}


# ---------- datos (paquetes si existen; si no, fallbacks) ----------
def _listar_usuarios(cur):
    # 1) Paquetes conocidos
    for call in (
        ("PKG_UI_LISTAS.LISTAR_USUARIOS_DETALLE", "proc"),
        ("PKG_USUARIOS.LISTAR_USUARIOS", "proc"),
        ("PKG_USUARIOS.LISTAR_USUARIOS", "func"),
    ):
        name, kind = call
        try:
            if kind == "proc":
                rc = cur.var(oracledb.DB_TYPE_CURSOR)
                cur.callproc(name, [rc])
                ref = rc.getvalue()
            else:
                ref = cur.callfunc(name, oracledb.DB_TYPE_CURSOR, [])
            cols = [d[0] for d in ref.description]
            rows = [dict(zip(cols, r)) for r in ref.fetchall()]
            try: ref.close()
            except: pass
            return rows, _detect_columns(set(cols)), _load_roles(cur)
        except Exception:
            pass

    # 2) Vista si existe
    try:
        cur.execute("SELECT * FROM V_USUARIOS_GESTION ORDER BY 1")
        cols = [d[0] for d in cur.description]
        rows = [dict(zip(cols, r)) for r in cur.fetchall()]
        return rows, _detect_columns(set(cols)), _load_roles(cur)
    except Exception:
        pass

    # 3) JOIN directo: TKT_USUARIO + TKT_ROL (agrega NOMBRE_ROL)
    try:
        cur.execute("""
            SELECT u.*, r.NOMBRE_ROL AS NOMBRE_ROL
            FROM TKT_USUARIO u
            LEFT JOIN TKT_ROL r ON r.ID_ROL = u.ID_ROL
            ORDER BY u.ID_USUARIO
        """)
        cols = [d[0] for d in cur.description]
        rows = [dict(zip(cols, r)) for r in cur.fetchall()]
        return rows, _detect_columns(set(cols)), _load_roles(cur)
    except Exception:
        pass

    # 4) SELECT * como último recurso
    cur.execute("SELECT * FROM TKT_USUARIO ORDER BY 1")
    cols = [d[0] for d in cur.description]
    rows = [dict(zip(cols, r)) for r in cur.fetchall()]
    return rows, _detect_columns(set(cols)), _load_roles(cur)


def _update_usuario(cur, u_norm, colmap, role_maps=None):
    """Actualiza con paquetes si existen; si no, UPDATE dinámico con columnas presentes."""
    # Paquete completo (si existe)
    try:
        cur.callproc("PKG_USUARIOS.ACTUALIZAR_USUARIO", [
            int(u_norm["ID_USUARIO"]),
            u_norm["NOMBRE"], u_norm["APELLIDO1"], u_norm.get("APELLIDO2", "") or "",
            u_norm["CORREO"], u_norm["ROL"], int(u_norm["ACTIVO"])
        ])
        return
    except Exception:
        pass

    sets = []
    vals = []

    if colmap["NOMBRE"]:
        sets.append(f'{colmap["NOMBRE"]} = :p{len(vals)+1}'); vals.append(u_norm["NOMBRE"])
    if colmap["AP1"]:
        sets.append(f'{colmap["AP1"]} = :p{len(vals)+1}'); vals.append(u_norm["APELLIDO1"])
    if colmap["AP2"]:
        sets.append(f'{colmap["AP2"]} = :p{len(vals)+1}'); vals.append(u_norm.get("APELLIDO2", "") or "")
    if colmap["CORREO"]:
        sets.append(f'{colmap["CORREO"]} = :p{len(vals)+1}'); vals.append(u_norm["CORREO"])

    # Rol: textual o numérico según columnas disponibles
    if colmap["ROL"]:
        sets.append(f'{colmap["ROL"]} = :p{len(vals)+1}'); vals.append(u_norm["ROL"])
    elif colmap["ID_ROL"] and role_maps:
        rid = role_maps["name_to_id"].get(_norm_role_name(u_norm["ROL"]))
        if rid:
            sets.append(f'{colmap["ID_ROL"]} = :p{len(vals)+1}'); vals.append(int(rid))

    if colmap["ACTIVO"] is not None:
        sets.append(f'{colmap["ACTIVO"]} = :p{len(vals)+1}'); vals.append(int(u_norm["ACTIVO"]))

    if not sets or not colmap["ID"]:
        raise RuntimeError("No hay columnas suficientes para actualizar este usuario.")

    sql = f'UPDATE TKT_USUARIO SET {", ".join(sets)} WHERE {colmap["ID"]} = :pid'
    vals.append(int(u_norm["ID_USUARIO"]))
    cur.execute(sql, vals)


def _update_estado(cur, id_usuario, nuevo, colmap):
    # Paquetes, si existen
    try:
        cur.callproc("PKG_USUARIOS.ACTUALIZAR_ESTADO", [int(id_usuario), int(nuevo)])
        return
    except Exception:
        pass
    try:
        if int(nuevo):
            cur.callproc("PKG_USUARIOS.ACTIVAR_USUARIO", [int(id_usuario)])
        else:
            cur.callproc("PKG_USUARIOS.DESACTIVAR_USUARIO", [int(id_usuario)])
        return
    except Exception:
        pass
    # UPDATE dinámico si hay columna de activo
    if not colmap["ACTIVO"] or not colmap["ID"]:
        raise RuntimeError("No existe columna de estado/activo ni paquetes para actualizar.")
    cur.execute(
        f'UPDATE TKT_USUARIO SET {colmap["ACTIVO"]} = :a WHERE {colmap["ID"]} = :id',
        [int(nuevo), int(id_usuario)]
    )


# ---------- normalización para UI ----------
def _to_int_bool(v):
    s = str(v).strip().lower()
    if s.isdigit():
        return int(s) != 0
    return s in ("s", "si", "sí", "true", "t", "y", "yes", "activo", "enabled", "1")

def _normalize_user_dict(d, colmap, role_maps=None):
    # ID
    uid = d.get(colmap["ID"]) if colmap["ID"] else d.get("ID_USUARIO") or d.get("ID")

    # Rol textual
    rol_text = ""
    if colmap["ROL"] and d.get(colmap["ROL"]) is not None:
        rol_text = str(d.get(colmap["ROL"]))
    elif colmap["ID_ROL"] and role_maps:
        try:
            rid = int(d.get(colmap["ID_ROL"]))
            rol_text = role_maps["id_to_name"].get(rid, str(rid))
        except Exception:
            rol_text = str(d.get(colmap["ID_ROL"]) or "")

    return {
        "ID_USUARIO": uid or "",
        "NOMBRE":     d.get(colmap["NOMBRE"]) or "",
        "APELLIDO1":  d.get(colmap["AP1"]) or "",
        "APELLIDO2":  d.get(colmap["AP2"]) or "",
        "CORREO":     d.get(colmap["CORREO"]) or d.get("USUARIO_EMAIL") or d.get("EMAIL") or "",
        "ROL":        rol_text or "",
        "ACTIVO":     _to_int_bool(d.get(colmap["ACTIVO"])) if colmap["ACTIVO"] else 1,
    }

def _display_tuple(u):
    return (
        u.get("ID_USUARIO") or "",
        u.get("NOMBRE") or "",
        u.get("APELLIDO1") or "",
        u.get("APELLIDO2") or "",
        u.get("CORREO") or "",
        u.get("ROL") or "",
        "Sí" if int(bool(u.get("ACTIVO", 0))) else "No",
    )


# ---------- UI ----------
def open_manage_users_window(parent):
    win = tk.Toplevel(parent)
    win.title("Gestionar Usuarios")
    win.geometry("1060x580")
    win.transient(parent)
    win.grab_set()

    top = tk.Frame(win); top.pack(fill=tk.X, padx=10, pady=8)
    tk.Label(top, text="Gestión de usuarios", font=("Arial", 11, "bold")).pack(side=tk.LEFT)

    cols = ("ID", "Nombre", "Apellido1", "Apellido2", "Correo", "Rol", "Activo")
    container = tk.Frame(win); container.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 8))
    if HAS_TTK:
        tree = ttk.Treeview(container, columns=cols, show="headings", height=18)
        for c in cols:
            tree.heading(c, text=c)
        tree.column("ID", width=60, anchor="center")
        tree.column("Nombre", width=160, anchor="w")
        tree.column("Apellido1", width=140, anchor="w")
        tree.column("Apellido2", width=140, anchor="w")
        tree.column("Correo", width=240, anchor="w")
        tree.column("Rol", width=120, anchor="center")
        tree.column("Activo", width=70, anchor="center")
        vsb = ttk.Scrollbar(container, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=vsb.set)
        tree.pack(side="left", fill=tk.BOTH, expand=True); vsb.pack(side="right", fill="y")
    else:
        tree = tk.Listbox(container); tree.pack(fill=tk.BOTH, expand=True)

    status = tk.Label(win, text="", anchor="w")
    status.pack(fill=tk.X, padx=10, pady=(0, 8))

    bar = tk.Frame(win); bar.pack(fill=tk.X, padx=10, pady=(0, 10))
    btn_refrescar = tk.Button(bar, text="Refrescar")
    btn_crear     = tk.Button(bar, text="Crear nuevo")
    btn_editar    = tk.Button(bar, text="Editar seleccionado")
    btn_toggle    = tk.Button(bar, text="Activar/Desactivar")
    btn_cerrar    = tk.Button(bar, text="Cerrar", bg="#d33", fg="white", command=win.destroy)
    for b in (btn_refrescar, btn_crear, btn_editar, btn_toggle, btn_cerrar):
        b.pack(side=tk.LEFT, padx=6)

    data_rows = []
    id_map = {}
    colmap = None
    role_maps = None  # {"id_to_name": {...}, "name_to_id": {...}}

    def clear_tree():
        if HAS_TTK:
            for iid in tree.get_children():
                tree.delete(iid)
        else:
            tree.delete(0, tk.END)

    def fill_tree(rows, _colmap, _role_maps):
        clear_tree()
        id_map.clear()
        if HAS_TTK:
            for i, d in enumerate(rows):
                u = _normalize_user_dict(d, _colmap, _role_maps)
                iid = tree.insert("", "end", values=_display_tuple(u))
                id_map[iid] = i
        else:
            for i, d in enumerate(rows):
                u = _normalize_user_dict(d, _colmap, _role_maps)
                tree.insert(tk.END, " | ".join(map(str, _display_tuple(u))))
                id_map[str(i)] = i

    def load_users():
        status.config(text="Cargando usuarios…")
        btn_refrescar.config(state="disabled")
        def worker():
            conn = cur = None
            try:
                conn = connect_to_db()
                try: conn.call_timeout = 60000
                except Exception: pass
                cur = conn.cursor(); cur.arraysize = 200
                rows, detected, roles = _listar_usuarios(cur)
                return (rows, detected, roles)
            finally:
                try:
                    if cur: cur.close()
                except: pass
                try:
                    if conn: conn.close()
                except: pass
        def done(payload, err):
            nonlocal data_rows, colmap, role_maps
            if err:
                messagebox.showerror("Usuarios", f"No se pudo listar usuarios:\n{err}")
                status.config(text=""); btn_refrescar.config(state="normal"); return
            data_rows, colmap, role_maps = payload
            fill_tree(data_rows, colmap, role_maps)
            status.config(text=f"{len(data_rows)} usuario(s) cargados.")
            btn_refrescar.config(state="normal")
        _run_in_thread(win, worker, done)

    def get_selected_index():
        if HAS_TTK:
            sel = tree.selection()
            if not sel: return None
            return id_map.get(sel[0])
        else:
            sel = tree.curselection()
            if not sel: return None
            return sel[0] if sel[0] < len(data_rows) else None

    def edit_selected():
        idx = get_selected_index()
        if idx is None:
            messagebox.showwarning("Selección", "Seleccione un usuario.")
            return
        u0 = _normalize_user_dict(data_rows[idx], colmap, role_maps)

        ed = tk.Toplevel(win)
        ed.title(f"Editar Usuario #{u0['ID_USUARIO']}")
        ed.geometry("540x380"); ed.transient(win); ed.grab_set()

        frm = tk.Frame(ed); frm.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)
        for i in range(2): frm.columnconfigure(i, weight=1)

        tk.Label(frm, text="Nombre").grid(row=0, column=0, sticky="w", pady=4)
        e_nombre = tk.Entry(frm); e_nombre.grid(row=0, column=1, sticky="ew"); e_nombre.insert(0, u0["NOMBRE"])

        tk.Label(frm, text="Apellido 1").grid(row=1, column=0, sticky="w", pady=4)
        e_ap1 = tk.Entry(frm); e_ap1.grid(row=1, column=1, sticky="ew"); e_ap1.insert(0, u0["APELLIDO1"])

        tk.Label(frm, text="Apellido 2").grid(row=2, column=0, sticky="w", pady=4)
        e_ap2 = tk.Entry(frm); e_ap2.grid(row=2, column=1, sticky="ew"); e_ap2.insert(0, u0.get("APELLIDO2",""))

        tk.Label(frm, text="Correo").grid(row=3, column=0, sticky="w", pady=4)
        e_mail = tk.Entry(frm); e_mail.grid(row=3, column=1, sticky="ew"); e_mail.insert(0, u0["CORREO"])

        tk.Label(frm, text="Rol").grid(row=4, column=0, sticky="w", pady=4)
        # opciones de rol tomadas de BD (si existen), con fallback
        role_names = list(role_maps["id_to_name"].values()) if role_maps else ["Admin","Técnico","Usuario"]
        if "Tecnico" in role_names and "Técnico" not in role_names:
            role_names.append("Técnico")
        role_names = sorted(set(role_names), key=lambda x: _norm_role_name(x))
        rol_var = tk.StringVar(value=(u0["ROL"] or (role_names[0] if role_names else "")))
        if HAS_TTK:
            ttk.Combobox(frm, state="readonly", textvariable=rol_var, values=role_names).grid(row=4, column=1, sticky="ew")
        else:
            tk.OptionMenu(frm, rol_var, *role_names).grid(row=4, column=1, sticky="ew")

        activo_var = tk.IntVar(value=int(bool(u0["ACTIVO"])))
        tk.Checkbutton(frm, text="Activo", variable=activo_var).grid(row=5, column=1, sticky="w", pady=6)

        status_ed = tk.Label(ed, text="", anchor="w"); status_ed.pack(fill=tk.X, padx=12)
        bar_ed = tk.Frame(ed); bar_ed.pack(fill=tk.X, padx=12, pady=8)
        btn_save = tk.Button(bar_ed, text="Guardar"); btn_save.pack(side=tk.LEFT, padx=6)
        tk.Button(bar_ed, text="Cancelar", command=ed.destroy).pack(side=tk.LEFT, padx=6)

        def do_save():
            if not colmap or not colmap["ID"]:
                messagebox.showerror("Guardar", "No se detectó columna ID en la tabla de usuarios.")
                return
            u_new = {
                "ID_USUARIO": u0["ID_USUARIO"],
                "NOMBRE": e_nombre.get().strip(),
                "APELLIDO1": e_ap1.get().strip(),
                "APELLIDO2": e_ap2.get().strip(),
                "CORREO": e_mail.get().strip().lower(),
                "ROL": rol_var.get().strip(),
                "ACTIVO": int(bool(activo_var.get())),
            }
            if not u_new["NOMBRE"] or not u_new["APELLIDO1"] or not u_new["CORREO"] or not u_new["ROL"]:
                messagebox.showerror("Validación", "Nombre, Apellido 1, Correo y Rol son obligatorios.")
                return

            btn_save.config(state="disabled"); status_ed.config(text="Guardando…")
            def worker():
                conn = cur = None
                try:
                    conn = connect_to_db()
                    try: conn.call_timeout = 60000
                    except Exception: pass
                    cur = conn.cursor()
                    _update_usuario(cur, u_new, colmap, role_maps)
                    conn.commit()
                finally:
                    try:
                        if cur: cur.close()
                    except: pass
                    try:
                        if conn: conn.close()
                    except: pass
            def done(_res, err):
                btn_save.config(state="normal"); status_ed.config(text="")
                if err:
                    messagebox.showerror("Guardar", f"No se pudo actualizar el usuario:\n{err}")
                    return
                load_users(); ed.destroy()
            _run_in_thread(ed, worker, done)

        btn_save.config(command=do_save)

    def toggle_selected():
        idx = get_selected_index()
        if idx is None:
            messagebox.showwarning("Selección", "Seleccione un usuario.")
            return
        u0 = _normalize_user_dict(data_rows[idx], colmap, role_maps)
        nuevo = 0 if int(bool(u0["ACTIVO"])) else 1
        if not messagebox.askyesno("Confirmación",
                                   f"¿Desea {'activar' if nuevo else 'desactivar'} al usuario #{u0['ID_USUARIO']}?"):
            return
        status.config(text="Actualizando estado…"); btn_toggle.config(state="disabled")
        def worker():
            conn = cur = None
            try:
                conn = connect_to_db()
                cur = conn.cursor()
                _update_estado(cur, u0["ID_USUARIO"], nuevo, colmap)
                conn.commit()
            finally:
                try:
                    if cur: cur.close()
                except: pass
                try:
                    if conn: conn.close()
                except: pass
        def done(_res, err):
            btn_toggle.config(state="normal"); status.config(text="")
            if err:
                messagebox.showerror("Estado", f"No se pudo actualizar el estado:\n{err}")
            else:
                load_users()
        _run_in_thread(win, worker, done)

    def crear_nuevo():
        """Reusa la ventana de registro y refresca al cerrar."""
        try:
            from gui.register_window import open_register_window
        except Exception as e:
            messagebox.showerror("Usuarios", f"No pude abrir el formulario de creación:\n{e}")
            return

        try:
            # intenta firma con parent/is_admin
            w = open_register_window(is_admin=True, parent=win)
        except TypeError:
            try:
                w = open_register_window(is_admin=True)
            except TypeError:
                w = open_register_window()

        try:
            win.wait_window(w)
        except Exception:
            pass

        load_users()

    btn_refrescar.config(command=load_users)
    btn_crear.config(command=crear_nuevo)
    btn_editar.config(command=edit_selected)
    btn_toggle.config(command=toggle_selected)

    _safe_after(win, 30, load_users)
    return win
