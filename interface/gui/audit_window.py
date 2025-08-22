# gui/audit_window.py
import tkinter as tk
from tkinter import messagebox
from threading import Thread
try:
    from tkinter import ttk
except Exception:
    ttk = None

import oracledb
from db.connection import connect_to_db

def open_audit_window(parent):
    win = tk.Toplevel(parent)
    win.title("Auditoría")
    win.geometry("1000x600")

    # --- TOP BAR ---
    top = tk.Frame(win)
    top.pack(fill=tk.X, padx=10, pady=8)

    tk.Label(top, text="Tipo:").pack(side=tk.LEFT)
    tipo_var = tk.StringVar(value="Tickets")
    tk.OptionMenu(top, tipo_var, "Tickets", "Usuarios", "Asignaciones", "Accesos").pack(side=tk.LEFT, padx=6)

    tk.Label(top, text="Últimos días:").pack(side=tk.LEFT, padx=(12, 0))
    ent_dias = tk.Entry(top, width=6)
    ent_dias.insert(0, "30")
    ent_dias.pack(side=tk.LEFT, padx=6)

    # Checkbox Solo cerrados (solo aplica a Tickets)
    solo_cerrados_var = tk.BooleanVar(value=False)
    chk_cerrados = tk.Checkbutton(top, text="Solo cerrados", variable=solo_cerrados_var)
    chk_cerrados.pack(side=tk.LEFT, padx=(16, 0))

    # --- TREEVIEW ---
    mid = tk.Frame(win)
    mid.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 8))

    columns_tickets = ("fecha", "ticket_id", "estado_anterior", "estado_nuevo", "log_id")
    columns_usuarios = ("fecha", "usuario_id", "correo", "aud_id")
    columns_asig    = ("fecha", "ticket_id", "tecnico_anterior", "tecnico_nuevo", "aud_id")
    columns_accesos = ("fecha", "usuario_id", "correo", "accion", "aud_id")

    tree = ttk.Treeview(mid, show="headings", columns=columns_tickets, height=20)
    vsb = ttk.Scrollbar(mid, orient="vertical", command=tree.yview)
    hsb = ttk.Scrollbar(mid, orient="horizontal", command=tree.xview)
    tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

    tree.grid(row=0, column=0, sticky="nsew")
    vsb.grid(row=0, column=1, sticky="ns")
    hsb.grid(row=1, column=0, sticky="ew")
    mid.rowconfigure(0, weight=1)
    mid.columnconfigure(0, weight=1)

    status = tk.Label(win, text="", anchor="w")
    status.pack(fill=tk.X, padx=10)

    # --- helpers ---
    def _set_columns(tipo: str):
        if tipo == "Tickets":
            tree.configure(columns=columns_tickets)
            headers = [
                ("fecha", "Fecha/Hora", 170),
                ("ticket_id", "Ticket ID", 90),
                ("estado_anterior", "Estado Anterior", 160),
                ("estado_nuevo", "Estado Nuevo", 160),
                ("log_id", "Log ID", 80),
            ]
            chk_cerrados.configure(state="normal")
        elif tipo == "Usuarios":
            tree.configure(columns=columns_usuarios)
            headers = [
                ("fecha", "Fecha/Hora", 170),
                ("usuario_id", "Usuario ID", 100),
                ("correo", "Correo", 260),
                ("aud_id", "Aud ID", 80),
            ]
            chk_cerrados.configure(state="disabled")
        elif tipo == "Asignaciones":
            tree.configure(columns=columns_asig)
            headers = [
                ("fecha", "Fecha/Hora", 170),
                ("ticket_id", "Ticket ID", 90),
                ("tecnico_anterior", "Técnico Anterior", 160),
                ("tecnico_nuevo", "Técnico Nuevo", 160),
                ("aud_id", "Aud ID", 80),
            ]
            chk_cerrados.configure(state="disabled")
        else:  # Accesos
            tree.configure(columns=columns_accesos)
            headers = [
                ("fecha", "Fecha/Hora", 170),
                ("usuario_id", "Usuario ID", 100),
                ("correo", "Correo", 240),
                ("accion", "Acción", 90),
                ("aud_id", "Aud ID", 80),
            ]
            chk_cerrados.configure(state="disabled")

        for col, text, width in headers:
            tree.heading(col, text=text)
            tree.column(col, width=width, anchor="w", stretch=True)

    def _clear_tree():
        for i in tree.get_children():
            tree.delete(i)

    def _parse_dias():
        try:
            d = int((ent_dias.get() or "30").strip())
            if d <= 0:
                raise ValueError
            return d
        except Exception:
            return 30

    # --- loader (threaded) ---
    current_thread = {"t": None}

    def cargar():
        if current_thread["t"] and current_thread["t"].is_alive():
            return

        _clear_tree()
        status.config(text="Cargando auditoría…")
        _set_columns(tipo_var.get())
        dias = _parse_dias()
        filtro_cerrados = bool(solo_cerrados_var.get())
        tipo = tipo_var.get()

        def worker():
            conn = cur = ref = None
            rows = []
            err = None
            try:
                conn = connect_to_db()
                cur = conn.cursor()
                rc = cur.var(oracledb.DB_TYPE_CURSOR)

                if tipo == "Tickets":
                    # (id_log, id_tkt, est_old, est_new, fecha)
                    cur.callproc("PKG_UI_LISTAS.LISTAR_AUDITORIA_TICKETS", [rc, dias])
                    ref = rc.getvalue()
                    for id_log, id_tkt, est_old, est_new, fecha in ref:
                        fstr = fecha.strftime("%Y-%m-%d %H:%M:%S") if hasattr(fecha, "strftime") else str(fecha)
                        if filtro_cerrados and (str(est_new) or "").strip().lower() != "cerrado":
                            continue
                        rows.append((fstr, str(id_tkt), str(est_old), str(est_new), str(id_log)))

                elif tipo == "Usuarios":
                    # (id_aud, id_usr, correo, fecha)
                    cur.callproc("PKG_UI_LISTAS.LISTAR_AUDITORIA_USUARIOS", [rc, dias])
                    ref = rc.getvalue()
                    for id_aud, id_usr, correo, fecha in ref:
                        fstr = fecha.strftime("%Y-%m-%d %H:%M:%S") if hasattr(fecha, "strftime") else str(fecha)
                        rows.append((fstr, str(id_usr), str(correo), str(id_aud)))

                elif tipo == "Asignaciones":
                    # (id_aud_asig, id_ticket, tecnico_anterior, tecnico_nuevo, fecha)
                    cur.callproc("PKG_UI_LISTAS.LISTAR_AUDITORIA_ASIGNACIONES", [rc, dias])
                    ref = rc.getvalue()
                    for id_aud_asig, id_tkt, tec_old, tec_new, fecha in ref:
                        fstr = fecha.strftime("%Y-%m-%d %H:%M:%S") if hasattr(fecha, "strftime") else str(fecha)
                        rows.append((fstr, str(id_tkt), str(tec_old), str(tec_new), str(id_aud_asig)))

                else:  # Accesos
                    # (id_evento, id_usuario, correo, accion, fecha)
                    cur.callproc("PKG_AUDITORIA_UI.LISTAR_ACCESOS", [rc, dias, None, None, None, None, 300, 0])
                    ref = rc.getvalue()
                    for id_evt, id_usr, correo, accion, fecha in ref:
                        fstr = fecha.strftime("%Y-%m-%d %H:%M:%S") if hasattr(fecha, "strftime") else str(fecha)
                        rows.append((fstr, str(id_usr), str(correo), str(accion), str(id_evt)))

            except Exception as e:
                err = e
            finally:
                try:
                    if ref: ref.close()
                except Exception:
                    pass
                try:
                    if cur: cur.close()
                except Exception:
                    pass
                try:
                    if conn: conn.close()
                except Exception:
                    pass

            def done():
                if err:
                    messagebox.showerror("Auditoría", f"No se pudo cargar:\n{err}")
                    status.config(text="")
                    return
                # Tags visuales: resaltar cerrados en Tickets
                try:
                    tree.tag_configure("cerrado", background="#e8f5e9")
                except Exception:
                    pass

                for r in rows:
                    tags = ()
                    if tipo == "Tickets" and len(r) >= 4 and str(r[3]).strip().upper() == "CERRADO":
                        tags = ("cerrado",)
                    tree.insert("", "end", values=r, tags=tags)

                extra = ""
                if tipo == "Tickets" and filtro_cerrados:
                    extra = " (solo cerrados)"
                status.config(text=f"{len(rows)} evento(s).  (Tipo: {tipo}{extra} / Últimos {dias} días)")

            try:
                win.after(0, done)
            except Exception:
                pass

        t = Thread(target=worker, daemon=True)
        current_thread["t"] = t
        t.start()

    # --- bottom bar ---
    bar = tk.Frame(win)
    bar.pack(fill=tk.X, padx=10, pady=(0, 8))

    tk.Button(bar, text="Cargar (F5)", command=cargar).pack(side=tk.LEFT, padx=4)
    tk.Button(bar, text="Cerrar", command=win.destroy).pack(side=tk.RIGHT, padx=4)

    # Eventos
    win.bind("<F5>", lambda e: cargar())
    tipo_var.trace_add("write", lambda *_: _set_columns(tipo_var.get()))

    # Inicial
    _set_columns("Tickets")
    cargar()

    return win
