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


def _load_listas():
    conn = cur = None
    out = {"estados": {}, "prioridades": {}, "categorias": {}}
    try:
        conn = connect_to_db(); cur = conn.cursor()
        for proc, key in [
            ("PKG_UI_LISTAS.LISTAR_ESTADOS", "estados"),
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


def open_edit_ticket_window(parent, id_ticket, asunto_actual, id_usuario):
    win = tk.Toplevel(parent)
    win.title(f"Editar Ticket #{id_ticket}")
    win.geometry("780x560")
    win.transient(parent); win.grab_set()

    top = tk.Frame(win); top.pack(fill=tk.X, padx=12, pady=8)

    tk.Label(top, text="Asunto", width=12, anchor="w").grid(row=0, column=0, sticky="w")
    ent_asunto = tk.Entry(top); ent_asunto.insert(0, asunto_actual or "")
    ent_asunto.grid(row=0, column=1, sticky="ew", padx=(0,10))

    tk.Label(top, text="Descripción", width=12, anchor="w").grid(row=1, column=0, sticky="nw")
    txt_desc = tk.Text(top, height=5); txt_desc.grid(row=1, column=1, sticky="ew")
    top.columnconfigure(1, weight=1)

    listas = _load_listas()

    def mk_selector(parent, label, values: dict, row):
        tk.Label(parent, text=label, width=12, anchor="w").grid(row=row, column=0, sticky="w", pady=4)
        names = list(values.keys()); default = names[0] if names else ""
        if HAS_COMBO:
            cb = ttk.Combobox(parent, state="readonly", values=names)
            if default: cb.set(default)
            cb.grid(row=row, column=1, sticky="ew")
            return lambda: values.get(cb.get())
        else:
            var = tk.StringVar(value=default)
            tk.OptionMenu(parent, var, *names).grid(row=row, column=1, sticky="ew")
            return lambda: values.get(var.get())

    get_estado    = mk_selector(top, "Estado",    listas["estados"],    2)
    get_prioridad = mk_selector(top, "Prioridad", listas["prioridades"], 3)
    get_categoria = mk_selector(top, "Categoría", listas["categorias"], 4)

    def guardar():
        asunto = ent_asunto.get().strip()
        desc   = txt_desc.get("1.0", "end-1c").strip()
        if not asunto:
            messagebox.showerror("Validación", "Digite un asunto.")
            return
        conn = cur = None
        try:
            conn = connect_to_db(); cur = conn.cursor()
            cur.callproc("PKG_TIQUETES.ACTUALIZAR_TICKET", [
                int(id_ticket), asunto, desc,
                int(get_estado()), int(get_prioridad()), int(get_categoria())
            ])
            conn.commit()
            messagebox.showinfo("Éxito", "Ticket actualizado.")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo actualizar el ticket:\n{e}")
        finally:
            try:
                if cur: cur.close()
                if conn: conn.close()
            except: pass

    tk.Button(top, text="Guardar Cambios", command=guardar).grid(row=5, column=1, sticky="e", pady=6)

    # ----------- Comentarios (sin hilos) -----------
    sep = tk.Frame(win, height=1, bg="#ddd"); sep.pack(fill=tk.X, padx=12, pady=4)

    cm = tk.Frame(win); cm.pack(fill=tk.BOTH, expand=True, padx=12, pady=(2,8))
    tk.Label(cm, text=f"Comentarios del Ticket #{id_ticket}",
             font=("Arial", 10, "bold")).pack(anchor="w")

    list_frame = tk.Frame(cm); list_frame.pack(fill=tk.BOTH, expand=True, pady=(4,4))
    lst = tk.Listbox(list_frame)
    lst.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    sb = tk.Scrollbar(list_frame, orient=tk.VERTICAL, command=lst.yview)
    sb.pack(side=tk.RIGHT, fill=tk.Y)
    lst.config(yscrollcommand=sb.set)

    status = tk.Label(cm, text="", anchor="w")
    status.pack(fill=tk.X)

    entry_frame = tk.Frame(cm); entry_frame.pack(fill=tk.X, pady=(4,0))
    tk.Label(entry_frame, text="Nuevo comentario:").pack(anchor="w")
    txt = tk.Text(entry_frame, height=4)
    txt.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    btn_add = tk.Button(entry_frame, text="Agregar")
    btn_add.pack(side=tk.LEFT, padx=8)

    def cargar():
        status.config(text="Cargando comentarios…")
        lst.delete(0, tk.END)
        conn = cur = ref = None
        try:
            conn = connect_to_db(); cur = conn.cursor()
            rc = cur.var(oracledb.DB_TYPE_CURSOR)
            cur.callproc("PKG_COMENTARIOS.LISTAR_COMENTARIOS_X_TICKET", [int(id_ticket), rc])
            ref = rc.getvalue()
            for cid, usuario, contenido, fecha in (ref.fetchall() or []):
                try:
                    ftxt = fecha.strftime("%Y-%m-%d %H:%M")
                except Exception:
                    ftxt = str(fecha)
                lst.insert(tk.END, f"[{ftxt}] {usuario}: {contenido}")
        except Exception as e:
            messagebox.showerror("Comentarios", f"No se pudieron cargar:\n{e}")
        finally:
            status.config(text="")
            try:
                if ref: ref.close()
                if cur: cur.close()
                if conn: conn.close()
            except: pass

    def agregar():
        contenido = txt.get("1.0", "end-1c").strip()
        if not contenido:
            messagebox.showwarning("Comentario", "El comentario no puede estar vacío.")
            return
        conn = cur = None
        try:
            conn = connect_to_db(); cur = conn.cursor()
            cur.callproc("PKG_COMENTARIOS.INSERTAR_COMENTARIO",
                         [int(id_ticket), int(id_usuario), contenido])
            conn.commit()
            txt.delete("1.0", "end")
            cargar()
        except Exception as e:
            messagebox.showerror("Comentario", f"No se pudo insertar:\n{e}")
        finally:
            try:
                if cur: cur.close()
                if conn: conn.close()
            except: pass

    btn_add.config(command=agregar)
    cargar()
    return win
