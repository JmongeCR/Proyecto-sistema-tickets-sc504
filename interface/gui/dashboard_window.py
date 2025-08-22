# gui/dashboard_window.py
import tkinter as tk
from tkinter import messagebox, TclError
from threading import Thread
import oracledb
from db.connection import connect_to_db

# ----- ttk opcional -----
try:
    from tkinter import ttk
    HAS_TTK_TREE = hasattr(ttk, "Treeview")
except Exception:
    ttk = None
    HAS_TTK_TREE = False


class _SimpleTreeFallback(tk.Frame):
    def __init__(self, master, columns, show="headings", height=20):
        super().__init__(master)
        self.columns = list(columns)
        self._rows, self._iids, self._iid_to_index = [], [], {}

        hdr = tk.Frame(self); hdr.pack(fill=tk.X)
        for c in self.columns:
            tk.Label(hdr, text=c, font=("Arial", 9, "bold")).pack(side=tk.LEFT, padx=6)

        body = tk.Frame(self); body.pack(fill=tk.BOTH, expand=True)
        self._list = tk.Listbox(body, height=height)
        self._list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb = tk.Scrollbar(body, orient=tk.VERTICAL, command=self._list.yview)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        self._list.configure(yscrollcommand=sb.set)

    def heading(self, *_a, **_k): pass
    def column(self, *_a, **_k): pass
    def configure(self, **k):
        if "yscrollcommand" in k:
            self._list.configure(yscrollcommand=k["yscrollcommand"])
    def yview(self, *a): self._list.yview(*a)
    def bind(self, seq=None, func=None, add=None): self._list.bind(seq, func, add=add)
    def get_children(self): return list(self._iids)

    def _fmt(self, v):
        try:
            return f"{v[0]:>4}  {v[1]}  |  {v[2]}  |  {v[3]}  |  {v[4]}  |  {v[5]}  |  {v[6]}"
        except Exception:
            return "  ".join(str(x) for x in v)

    def insert(self, _parent, _index, values=()):
        iid = f"I{len(self._iids)+1}"
        self._iids.append(iid)
        self._rows.append(tuple(values))
        self._iid_to_index[iid] = len(self._rows) - 1
        self._list.insert(tk.END, self._fmt(values))
        return iid

    def selection(self):
        sel = self._list.curselection()
        return [f"I{int(sel[0])+1}"] if sel else []

    def item(self, iid, option=None):
        idx = self._iid_to_index.get(iid)
        if idx is None:
            return {}
        vals = self._rows[idx]
        return vals if option == "values" else {"values": vals}

    def delete(self, iid):
        if isinstance(iid, (list, tuple)):
            for x in iid:
                self.delete(x)
            return
        idx = self._iid_to_index.get(iid)
        if idx is None:
            return
        del self._rows[idx]
        del self._iids[idx]
        self._iid_to_index.clear()
        self._list.delete(0, tk.END)
        for i, vals in enumerate(self._rows, start=1):
            self._iid_to_index[f"I{i}"] = i - 1
            self._list.insert(tk.END, self._fmt(vals))
        self._iids = [f"I{i}" for i in range(1, len(self._rows)+1)]


# -------- utilidades --------
def _widget_alive(w):
    try:
        return bool(w) and w.winfo_exists()
    except Exception:
        return False

def _safe_after(widget, ms, fn):
    """Agenda fn con after solo si el widget sigue vivo."""
    try:
        if _widget_alive(widget):
            widget.after(ms, fn)
    except TclError:
        pass

def _safe_msg(title, text, kind="error"):
    """messagebox seguro (no revienta si el root murió)."""
    try:
        if not _widget_alive(tk._default_root):
            return
        if kind == "error":
            messagebox.showerror(title, text)
        elif kind == "warning":
            messagebox.showwarning(title, text)
        else:
            messagebox.showinfo(title, text)
    except Exception:
        pass

def _fetch_dicts_from_ref(ref):
    cols = [d[0] for d in ref.description]
    rows = [dict(zip(cols, row)) for row in ref.fetchall()]
    try:
        ref.close()
    except Exception:
        pass
    return rows

def _try_listar_simple(cur, proc_name):
    """Intenta proc OUT RC; si no, func RETURN RC."""
    try:
        rc = cur.var(oracledb.DB_TYPE_CURSOR)
        cur.callproc(proc_name, [rc])
        ref = rc.getvalue()
        return _fetch_dicts_from_ref(ref)
    except Exception as e_proc:
        try:
            ref = cur.callfunc(proc_name, oracledb.DB_TYPE_CURSOR, [])
            return _fetch_dicts_from_ref(ref)
        except Exception as e_func:
            raise RuntimeError(f"{proc_name}: Proc OUT RC -> {e_proc}\nFunc RETURN RC -> {e_func}")

def _try_listar_con_id(cur, proc_name, id_value):
    """Prueba (ID, OUT RC) y (OUT RC, ID)."""
    try:
        rc = cur.var(oracledb.DB_TYPE_CURSOR)
        cur.callproc(proc_name, [int(id_value), rc])
        ref = rc.getvalue()
        return _fetch_dicts_from_ref(ref)
    except Exception as e_a:
        try:
            rc = cur.var(oracledb.DB_TYPE_CURSOR)
            cur.callproc(proc_name, [rc, int(id_value)])
            ref = rc.getvalue()
            return _fetch_dicts_from_ref(ref)
        except Exception as e_b:
            raise RuntimeError(f"{proc_name}: (ID, OUT RC) -> {e_a}\n(OUT RC, ID) -> {e_b}")

def _row_to_values(d):
    return (
        d.get("ID_TICKET") or d.get("ID") or "",
        d.get("ASUNTO") or "",
        d.get("USUARIO_EMAIL") or d.get("USUARIO") or "",
        d.get("ESTADO") or "",
        d.get("PRIORIDAD") or "",
        d.get("CATEGORIA") or "",
        d.get("TECNICO_EMAIL") or d.get("TECNICO") or "",
    )

def _filter_rows_for_user(rows, user_id: int, user_email: str | None):
    uid_keys = ("ID_USUARIO", "USUARIO_ID", "IDUSER", "IDCLIENTE", "ID_USUARIO_CLIENTE")
    mail_keys = ("USUARIO_EMAIL", "EMAIL", "CORREO", "USUARIO")
    out = []
    for d in rows:
        keep = False
        for k in uid_keys:
            if k in d:
                try:
                    if int(d[k]) == int(user_id):
                        keep = True
                        break
                except Exception:
                    pass
        if not keep and user_email:
            uem = (user_email or "").strip().lower()
            for k in mail_keys:
                if k in d and isinstance(d[k], str) and (d[k] or "").strip().lower() == uem:
                    keep = True
                    break
        if keep:
            out.append(d)
    return out


class DashboardWindow:
    def __init__(self, root, user_id: int, role: str, user_email: str | None = None):
        self.root = root
        self.user_id = int(user_id)
        self.role = (role or "").strip()
        self.user_email = (user_email or "").strip().lower() if user_email else None

        self.root.title("Panel de Tickets")
        self.root.geometry("980x600")

        self._build_tree()
        self._bind_double_click()
        self._build_buttons()
        self._apply_role_visibility()

        self.status = tk.Label(self.root, text="", anchor="w")
        self.status.pack(fill=tk.X, padx=10, pady=(0, 6))

        self._destroyed = False
        self.root.bind("<Destroy>", lambda e: setattr(self, "_destroyed", True))

        self.load_tickets()

    # ---- helpers de clase ----
    def _ui_alive(self):
        return (not self._destroyed
                and _widget_alive(self.root)
                and _widget_alive(self.status)
                and _widget_alive(self.tree))

    def _safe(self, widget, **conf):
        if _widget_alive(widget):
            try:
                widget.config(**conf)
            except Exception:
                pass

    def _safe_tree_clear(self):
        if not _widget_alive(self.tree):
            return
        try:
            for iid in self.tree.get_children():
                self.tree.delete(iid)
        except Exception:
            pass

    # ---------------- UI ----------------
    def _build_tree(self):
        cols = ("ID", "Asunto", "Usuario", "Estado", "Prioridad", "Categoria", "Tecnico")
        if HAS_TTK_TREE:
            container = tk.Frame(self.root); container.pack(fill=tk.BOTH, expand=True, padx=10, pady=8)
            self.tree = ttk.Treeview(container, columns=cols, show="headings", height=20)
            for c in cols:
                self.tree.heading(c, text=c)
            self.tree.column("ID", width=70, anchor="center")
            self.tree.column("Asunto", width=260, anchor="w")
            self.tree.column("Usuario", width=220, anchor="w")
            self.tree.column("Estado", width=110, anchor="center")
            self.tree.column("Prioridad", width=110, anchor="center")
            self.tree.column("Categoria", width=140, anchor="w")
            self.tree.column("Tecnico", width=220, anchor="w")
            vsb = ttk.Scrollbar(container, orient="vertical", command=self.tree.yview)
            self.tree.configure(yscrollcommand=vsb.set)
            self.tree.pack(side="left", fill=tk.BOTH, expand=True)
            vsb.pack(side="right", fill="y")
        else:
            self.tree = _SimpleTreeFallback(self.root, columns=cols, height=20)
            self.tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=8)

    def _bind_double_click(self):
        def on_row_double_click(e):
            try:
                iid = None
                if HAS_TTK_TREE and hasattr(self.tree, "identify_row"):
                    try:
                        iid = self.tree.identify_row(e.y)
                    except Exception:
                        iid = None
                if not iid and hasattr(self.tree, "_list"):
                    try:
                        idx = self.tree._list.nearest(e.y)
                        if idx is not None and idx >= 0:
                            iid = f"I{idx+1}"
                            self.tree._list.selection_clear(0, "end")
                            self.tree._list.selection_set(idx)
                    except Exception:
                        pass
                if not iid:
                    sel = self.tree.selection()
                    iid = sel[0] if sel else None
                if not iid:
                    return
                values = self.tree.item(iid, "values")
                id_ticket = int(values[0]); asunto = values[1]
                from gui.edit_ticket_window import open_edit_ticket_window
                w = open_edit_ticket_window(self.root, id_ticket, asunto, self.user_id)
                self.root.wait_window(w)
                if self._ui_alive():
                    self.load_tickets()
            except Exception as ex:
                _safe_msg("Abrir ticket", str(ex), "error")
        self.tree.bind("<Double-1>", on_row_double_click)

    def _build_buttons(self):
        bar = tk.Frame(self.root); bar.pack(fill=tk.X, padx=10, pady=(0, 8))
        self.btn_actualizar  = tk.Button(bar, text="Actualizar",         command=self.load_tickets)
        self.btn_crear       = tk.Button(bar, text="Crear Ticket",       command=self._create_ticket)
        self.btn_editar      = tk.Button(bar, text="Editar",             command=self._edit_selected)
        self.btn_asignar     = tk.Button(bar, text="Asignar Técnico",    command=self._assign_selected)
        self.btn_comentarios = tk.Button(bar, text="Comentarios",        command=self._comments_selected)
        self.btn_gestion     = tk.Button(bar, text="Gestionar Usuarios", command=self._open_manage_users)
        self.btn_auditoria   = tk.Button(bar, text="Auditoría",          command=self._open_audit)
        self.btn_salir       = tk.Button(bar, text="Cerrar Sesión", bg="#d33", fg="white",
                                         command=self.root.destroy)
        for b in (self.btn_actualizar, self.btn_crear, self.btn_editar,
                  self.btn_asignar, self.btn_comentarios, self.btn_gestion,
                  self.btn_auditoria, self.btn_salir):
            b.pack(side=tk.LEFT, padx=6)

    def _apply_role_visibility(self):
        rol = (self.role or "").lower()
        if rol.startswith("admin"):
            return
        elif rol.startswith("técnico") or rol.startswith("tecnico"):
            self.btn_gestion.pack_forget(); self.btn_auditoria.pack_forget()
        else:
            self.btn_asignar.pack_forget(); self.btn_editar.pack_forget()
            self.btn_gestion.pack_forget(); self.btn_auditoria.pack_forget()

    # --------------- helpers ---------------
    def _get_selected_ticket(self):
        sel = self.tree.selection()
        if not sel:
            _safe_msg("Selección", "Seleccione un ticket.", "warning")
            return None
        return self.tree.item(sel[0], "values")

    def _edit_selected(self):
        item = self._get_selected_ticket()
        if not item: return
        id_ticket = int(item[0]); asunto = item[1]
        from gui.edit_ticket_window import open_edit_ticket_window
        w = open_edit_ticket_window(self.root, id_ticket, asunto, self.user_id)
        self.root.wait_window(w)
        if self._ui_alive(): self.load_tickets()

    def _assign_selected(self):
        item = self._get_selected_ticket()
        if not item: return
        id_ticket = int(item[0])
        from gui.assign_ticket_window import open_assign_ticket_window
        w = open_assign_ticket_window(self.root, id_ticket)
        self.root.wait_window(w)
        if self._ui_alive(): self.load_tickets()

    def _comments_selected(self):
        item = self._get_selected_ticket()
        if not item: return
        id_ticket = int(item[0]); asunto = item[1]
        from gui.edit_ticket_window import open_edit_ticket_window
        w = open_edit_ticket_window(self.root, id_ticket, asunto, self.user_id)
        self.root.wait_window(w)
        if self._ui_alive(): self.load_tickets()

    def _create_ticket(self):
        from gui.create_ticket_window import open_create_ticket_window
        w = open_create_ticket_window(self.root, self.user_id)
        self.root.wait_window(w)
        if self._ui_alive(): self.load_tickets()

    def _open_manage_users(self):
        from gui.manage_users_window import open_manage_users_window
        w = open_manage_users_window(self.root)
        self.root.wait_window(w)

    def _open_audit(self):
        from gui.audit_window import open_audit_window
        w = open_audit_window(self.root)
        self.root.wait_window(w)

    # --------------- CARGA ---------------
    def load_tickets(self):
        if not self._ui_alive(): return
        self._safe(self.status, text="Cargando tickets…")
        self._safe(self.btn_actualizar, state="disabled")
        self._safe_tree_clear()

        def worker():
            conn = cur = None
            try:
                conn = connect_to_db()
                cur = conn.cursor()
                cur.arraysize = 200
                rol = (self.role or "").lower()

                # Admin / Técnico
                if rol.startswith("admin") or rol.startswith("técnico") or rol.startswith("tecnico"):
                    return _try_listar_simple(cur, "PKG_UI_LISTAS.LISTAR_TICKETS_DETALLE")

                # Usuario 
                try:
                    rows = _try_listar_con_id(cur, "PKG_UI_LISTAS.LISTAR_TICKETS_DETALLE_X_USUARIO", self.user_id)
                    if rows:
                        return rows
                except Exception:
                    pass

                all_rows = _try_listar_simple(cur, "PKG_UI_LISTAS.LISTAR_TICKETS_DETALLE")
                filtered = _filter_rows_for_user(all_rows, self.user_id, self.user_email)
                if filtered:
                    return filtered
                return all_rows

            finally:
                try:
                    if cur: cur.close()
                except Exception:
                    pass
                try:
                    if conn: conn.close()
                except Exception:
                    pass

        def done(rows_dicts):
            if not self._ui_alive(): return
            for d in (rows_dicts or []):
                self.tree.insert("", "end", values=_row_to_values(d))
            self._safe(self.status, text=f"{len(rows_dicts or [])} ticket(s) cargados.")
            self._safe(self.btn_actualizar, state="normal")

        def on_error(err):
            if not self._ui_alive(): return
            _safe_msg("Error", f"No se pudieron cargar los tickets (paquetes):\n{err}", "error")
            self._safe(self.status, text="")
            self._safe(self.btn_actualizar, state="normal")

        def run():
            try:
                rs = worker()
            except Exception as e:
                _safe_after(self.root, 0, lambda: on_error(e))
                return
            _safe_after(self.root, 0, lambda: done(rs))

        Thread(target=run, daemon=True).start()
