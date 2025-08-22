# gui/edit_ticket_window.py
import tkinter as tk
from tkinter import messagebox

try:
    from tkinter import ttk
    HAS_COMBO = hasattr(ttk, "Combobox")
except Exception:
    ttk = None
    HAS_COMBO = False

from threading import Thread
import oracledb
from db.connection import connect_to_db


# ---------- utilidades seguras para hilos/Tk ----------
def _widget_alive(w):
    try:
        return bool(w) and w.winfo_exists()
    except Exception:
        return False

def _safe_after(w, ms, fn):
    """Agenda fn solo si la ventana sigue viva y el mainloop está activo."""
    try:
        if _widget_alive(w):
            w.after(ms, fn)
    except Exception:
        # evita "main thread is not in main loop"
        pass


def _run_in_thread(win, fn, on_done):
    """Ejecuta fn() en un hilo; al terminar, llama on_done(res, err) en UI si la ventana sigue viva."""
    def runner():
        try:
            res, err = fn(), None
        except Exception as e:
            res, err = None, e
        _safe_after(win, 0, lambda: on_done(res, err))
    Thread(target=runner, daemon=True).start()


def open_edit_ticket_window(parent, id_ticket: int, asunto_actual: str, id_usuario: int):
    win = tk.Toplevel(parent)
    win.title(f"Editar Ticket #{id_ticket}")
    win.geometry("820x620")
    win.transient(parent)
    win.grab_set()

    # ------- Cabecera -------
    top = tk.Frame(win)
    top.pack(fill=tk.X, padx=12, pady=8)
    top.columnconfigure(1, weight=1)

    tk.Label(top, text="Asunto", width=12, anchor="w").grid(row=0, column=0, sticky="w")
    ent_asunto = tk.Entry(top)
    ent_asunto.insert(0, asunto_actual or "")
    ent_asunto.grid(row=0, column=1, sticky="ew", padx=(0, 10))

    tk.Label(top, text="Descripción", width=12, anchor="w").grid(row=1, column=0, sticky="nw", pady=(6, 0))
    txt_desc = tk.Text(top, height=5)
    txt_desc.grid(row=1, column=1, sticky="ew", pady=(6, 0))

    # Selectores
    tk.Label(top, text="Estado", width=12, anchor="w").grid(row=2, column=0, sticky="w", pady=6)
    tk.Label(top, text="Prioridad", width=12, anchor="w").grid(row=3, column=0, sticky="w", pady=6)
    tk.Label(top, text="Categoría", width=12, anchor="w").grid(row=4, column=0, sticky="w", pady=6)

    estado_var = tk.StringVar()
    prioridad_var = tk.StringVar()
    categoria_var = tk.StringVar()

    if HAS_COMBO:
        cb_estado = ttk.Combobox(top, state="readonly", textvariable=estado_var)
        cb_prior  = ttk.Combobox(top, state="readonly", textvariable=prioridad_var)
        cb_categ  = ttk.Combobox(top, state="readonly", textvariable=categoria_var)
        cb_estado.grid(row=2, column=1, sticky="ew")
        cb_prior.grid(row=3, column=1, sticky="ew")
        cb_categ.grid(row=4, column=1, sticky="ew")
    else:
        cb_estado = tk.OptionMenu(top, estado_var, "")
        cb_prior  = tk.OptionMenu(top, prioridad_var, "")
        cb_categ  = tk.OptionMenu(top, categoria_var, "")
        cb_estado.grid(row=2, column=1, sticky="ew")
        cb_prior.grid(row=3, column=1, sticky="ew")
        cb_categ.grid(row=4, column=1, sticky="ew")

    # Mapeos nombre -> id para guardar
    ids_por_nombre = {"estado": {}, "prioridad": {}, "categoria": {}}

    # ------- Comentarios -------
    sep = tk.Frame(win, height=1, bg="#ddd")
    sep.pack(fill=tk.X, padx=12, pady=8)

    cm = tk.Frame(win)
    cm.pack(fill=tk.BOTH, expand=True, padx=12, pady=(2, 8))
    tk.Label(cm, text=f"Comentarios del Ticket #{id_ticket}", font=("Arial", 10, "bold")).pack(anchor="w")

    list_frame = tk.Frame(cm); list_frame.pack(fill=tk.BOTH, expand=True, pady=(4, 4))
    lst = tk.Listbox(list_frame); lst.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    sb = tk.Scrollbar(list_frame, orient=tk.VERTICAL, command=lst.yview)
    sb.pack(side=tk.RIGHT, fill=tk.Y)
    lst.config(yscrollcommand=sb.set)

    status = tk.Label(cm, text="", anchor="w")
    status.pack(fill=tk.X)

    entry_frame = tk.Frame(cm); entry_frame.pack(fill=tk.X, pady=(4, 0))
    tk.Label(entry_frame, text="Nuevo comentario:").pack(anchor="w")
    txt = tk.Text(entry_frame, height=4); txt.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    btn_add = tk.Button(entry_frame, text="Agregar"); btn_add.pack(side=tk.LEFT, padx=8)

    # --------- Carga de listas (async) ----------
    def cargar_listas_worker():
        conn = cur = None
        res = {"estados": [], "prioridades": [], "categorias": []}
        try:
            conn = connect_to_db()
            cur = conn.cursor()
            for proc, key in [
                ("PKG_UI_LISTAS.LISTAR_ESTADOS", "estados"),
                ("PKG_UI_LISTAS.LISTAR_PRIORIDADES", "prioridades"),
                ("PKG_UI_LISTAS.LISTAR_CATEGORIAS", "categorias"),
            ]:
                rc = cur.var(oracledb.DB_TYPE_CURSOR)
                cur.callproc(proc, [rc])
                ref = rc.getvalue()
                rows = ref.fetchall()  # [(ID, NOMBRE), ...]
                try:
                    ref.close()
                except Exception:
                    pass
                res[key] = rows
            return res
        finally:
            try:
                if cur: cur.close()
            except Exception:
                pass
            try:
                if conn: conn.close()
            except Exception:
                pass

    def cargar_listas_done(data, err):
        if err:
            messagebox.showerror("Listas", f"No se pudieron cargar las listas:\n{err}")
            return

        def fill_combo(widget, var, rows, mapdict):
            nombres = []
            mapdict.clear()
            for rid, nombre in rows:
                nombre = str(nombre)
                mapdict[nombre] = int(rid)
                nombres.append(nombre)
            if HAS_COMBO:
                widget["values"] = nombres
                if nombres:
                    var.set(nombres[0])
            else:
                menu = widget["menu"]
                menu.delete(0, "end")
                for n in nombres:
                    menu.add_command(label=n, command=lambda v=n: var.set(v))
                if nombres:
                    var.set(nombres[0])

        fill_combo(cb_estado, estado_var, data["estados"],   ids_por_nombre["estado"])
        fill_combo(cb_prior,  prioridad_var, data["prioridades"], ids_por_nombre["prioridad"])
        fill_combo(cb_categ,  categoria_var, data["categorias"],  ids_por_nombre["categoria"])

    _run_in_thread(win, cargar_listas_worker, cargar_listas_done)

    # --------- Comentarios: cargar (async) ----------
    def cargar_comentarios_worker():
        conn = cur = ref = None
        try:
            conn = connect_to_db()
            # evita DPY-4024 si tarda un poco
            try:
                conn.call_timeout = 60000  # 60s (0 = sin límite)
            except Exception:
                pass

            cur = conn.cursor()
            cur.arraysize = 200

            # Firma real: (p_id_ticket IN, o_cursor OUT)
            rc = cur.var(oracledb.DB_TYPE_CURSOR)
            cur.callproc("PKG_COMENTARIOS.LISTAR_COMENTARIOS_X_TICKET", [int(id_ticket), rc])
            ref = rc.getvalue()

            rows = []
            while True:
                chunk = ref.fetchmany(200)
                if not chunk:
                    break
                for cid, usuario, contenido, fecha in chunk:
                    try:
                        if hasattr(contenido, "read"):
                            contenido = contenido.read()  # CLOB
                    except Exception:
                        contenido = str(contenido)
                    ftxt = fecha.strftime("%Y-%m-%d %H:%M") if hasattr(fecha, "strftime") else str(fecha)
                    rows.append((cid, str(usuario), str(contenido), ftxt))
            return rows

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

    def cargar_comentarios_done(rows, err):
        status.config(text="")
        lst.delete(0, tk.END)
        if err:
            messagebox.showerror("Comentarios", f"Error al cargar comentarios:\n{err}")
            return
        for cid, usuario, contenido, ftxt in (rows or []):
            lst.insert(tk.END, f"[{ftxt}] {usuario}: {contenido}")

    def cargar_comentarios_async():
        status.config(text="Cargando comentarios…")
        _run_in_thread(win, cargar_comentarios_worker, cargar_comentarios_done)

    # --------- Insertar comentario (async) ----------
    def agregar_async():
        contenido = txt.get("1.0", "end-1c").strip()
        if not contenido:
            messagebox.showwarning("Advertencia", "El comentario no puede estar vacío")
            return
        btn_add.config(state="disabled")
        status.config(text="Guardando comentario…")

        def worker():
            conn = cur = None
            try:
                conn = connect_to_db()
                cur = conn.cursor()
                cur.callproc(
                    "PKG_COMENTARIOS.INSERTAR_COMENTARIO",
                    [int(id_ticket), int(id_usuario), contenido]
                )
                conn.commit()
            finally:
                try:
                    if cur: cur.close()
                except Exception:
                    pass
                try:
                    if conn: conn.close()
                except Exception:
                    pass

        def done(_res, err):
            btn_add.config(state="normal")
            status.config(text="")
            if err:
                messagebox.showerror("Error", f"Error al insertar comentario:\n{err}")
            else:
                txt.delete("1.0", "end")
                cargar_comentarios_async()

        _run_in_thread(win, worker, done)

    btn_add.config(command=agregar_async)

    # --------- Guardar ticket (async) ----------
    def guardar_async():
        asunto = ent_asunto.get().strip()
        desc   = txt_desc.get("1.0", "end-1c").strip()
        if not asunto:
            messagebox.showerror("Validación", "Digite un asunto.")
            return

        nom_estado    = estado_var.get()
        nom_prioridad = prioridad_var.get()
        nom_categoria = categoria_var.get()

        try:
            id_estado    = ids_por_nombre["estado"][nom_estado]
            id_prioridad = ids_por_nombre["prioridad"][nom_prioridad]
            id_categoria = ids_por_nombre["categoria"][nom_categoria]
        except KeyError:
            messagebox.showerror("Validación", "Seleccione estado/prioridad/categoría válidos.")
            return

        def worker():
            conn = cur = None
            try:
                conn = connect_to_db()
                cur = conn.cursor()
                cur.callproc(
                    "PKG_TIQUETES.ACTUALIZAR_TICKET",
                    [int(id_ticket), asunto, desc, int(id_estado), int(id_prioridad), int(id_categoria)]
                )
                conn.commit()
            finally:
                try:
                    if cur: cur.close()
                except Exception:
                    pass
                try:
                    if conn: conn.close()
                except Exception:
                    pass

        def done(_res, err):
            if err:
                messagebox.showerror("Error", f"No se pudo actualizar el ticket:\n{err}")
            else:
                messagebox.showinfo("Éxito", "Ticket actualizado.")

        _run_in_thread(win, worker, done)

    tk.Button(top, text="Guardar Cambios", command=guardar_async).grid(row=5, column=1, sticky="e", pady=10)

    # Primera carga de comentarios (segura)
    _safe_after(win, 50, cargar_comentarios_async)
    return win
