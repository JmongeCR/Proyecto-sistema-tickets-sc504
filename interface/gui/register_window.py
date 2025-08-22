import tkinter as tk
from tkinter import messagebox
try:
    from tkinter import ttk
    HAS_COMBO = hasattr(ttk, "Combobox")
except Exception:
    ttk = None
    HAS_COMBO = False

from db.connection import connect_to_db
import oracledb


def open_register_window(is_admin: bool = False):

    try:
        from gui.login_window import login_window
    except Exception:
        login_window = None

    reg = tk.Toplevel() if tk._default_root else tk.Tk()
    reg.title("Registro de Usuario")
    reg.geometry("400x520")

    # centrar ventana
    reg.update_idletasks()
    w, h = 400, 520
    x = (reg.winfo_screenwidth() // 2) - (w // 2)
    y = (reg.winfo_screenheight() // 2) - (h // 2)
    reg.geometry(f"{w}x{h}+{x}+{y}")

    # campos
    fields = {}
    for label in ["Nombre", "Primer Apellido", "Segundo Apellido", "Correo", "Contraseña", "Teléfono"]:
        tk.Label(reg, text=label).pack(pady=3)
        ent = tk.Entry(reg, show="*" if label == "Contraseña" else None)
        ent.pack()
        fields[label] = ent

    # ----- cargar roles desde paquete -----
    tk.Label(reg, text="Rol").pack(pady=3)

    roles_dict = {}    
    roles_nombres = []  

    conn = None
    cur = None
    try:
        conn = connect_to_db()
        cur  = conn.cursor()
        rc   = cur.var(oracledb.DB_TYPE_CURSOR)

        # PKG_UI_LISTAS.LISTAR_ROLES(o_cursor OUT SYS_REFCURSOR)
        cur.callproc("PKG_UI_LISTAS.LISTAR_ROLES", [rc])
        ref = rc.getvalue()
        rows = ref.fetchall() if ref is not None else []
        if ref is not None:
            ref.close()

        for rol_id, rol_name in rows:
            roles_dict[str(rol_name)] = int(rol_id)

        roles_nombres = list(roles_dict.keys())
        if not roles_nombres:
            raise RuntimeError("No hay roles definidos en la BD.")

        # restringir si no es admin
        if not is_admin:
            prefer = [r for r in roles_nombres if "usuario" in r.lower()]
            if prefer:
                roles_nombres = prefer

    except Exception as e:
        messagebox.showerror("Roles", f"No se pudieron cargar roles:\n{e}")
        try:
            if cur: cur.close()
        finally:
            if conn: conn.close()
        reg.destroy()
        return
    finally:
        try:
            if cur: cur.close()
        finally:
            if conn: conn.close()


    if HAS_COMBO:
        combo_rol = ttk.Combobox(reg, state="readonly", values=roles_nombres)
        combo_rol.pack()
        if roles_nombres:
            combo_rol.current(0)

        def get_rol_sel():
            return combo_rol.get()
    else:
        rol_var = tk.StringVar(reg, value=(roles_nombres[0] if roles_nombres else ""))
        combo_rol = tk.OptionMenu(reg, rol_var, *roles_nombres)
        combo_rol.pack()

        def get_rol_sel():
            return rol_var.get()

    # ----- acciones -----
    def register_user():
        nombre     = fields["Nombre"].get().strip()
        ap1        = fields["Primer Apellido"].get().strip()
        ap2        = fields["Segundo Apellido"].get().strip()
        correo     = fields["Correo"].get().strip().lower()   # normaliza correo
        clave      = fields["Contraseña"].get().strip()
        tel        = fields["Teléfono"].get().strip()
        rol_nom    = get_rol_sel().strip()
        id_rol     = roles_dict.get(rol_nom)

        if not (nombre and ap1 and correo and clave and id_rol):
            messagebox.showerror("Validación", "Complete los campos obligatorios.")
            return

        conn = None
        cur = None
        try:
            conn = connect_to_db()
            cur  = conn.cursor()

            # ¿correo existe? 
            o_existe = cur.var(oracledb.DB_TYPE_NUMBER)
            cur.callproc("PKG_USUARIOS.EXISTE_CORREO", [correo, o_existe])
            if int(o_existe.getvalue() or 0) == 1:
                messagebox.showerror("Registro", "Este correo ya está registrado.")
                return

 
            cur.callproc("PKG_USUARIOS.INSERTAR_USUARIO", [
                nombre, ap1, (ap2 if ap2 else None),
                correo, clave, (tel if tel else None), id_rol
            ])
            conn.commit()


            o_result = cur.var(oracledb.DB_TYPE_NUMBER)
            o_id     = cur.var(oracledb.DB_TYPE_NUMBER)
            o_rol    = cur.var(oracledb.DB_TYPE_VARCHAR)
            ok = False
            try:

                cur.callproc("PKG_USUARIOS.LOGIN_USUARIO", [correo, clave, o_result, o_id, o_rol])
                ok = int(o_result.getvalue() or 0) == 1
            except oracledb.DatabaseError:
                # Firma 2: (correo, clave, o_id, o_rol)
                o_id  = cur.var(oracledb.DB_TYPE_NUMBER)
                o_rol = cur.var(oracledb.DB_TYPE_VARCHAR)
                cur.callproc("PKG_USUARIOS.LOGIN_USUARIO", [correo, clave, o_id, o_rol])
                ok = o_id.getvalue() is not None

            if not ok:
                messagebox.showwarning(
                    "Registro OK pero login falló",
                    "Se registró el usuario, pero el paquete de login no lo reconoce.\n"
                    "Verifique que LOGIN_USUARIO compare correos con LOWER(TRIM(...))."
                )
            else:
                messagebox.showinfo("Registro", "Usuario registrado y verificado. Ya puede iniciar sesión.")
                reg.destroy()
                if login_window and not is_admin:
                    login_window()

        except Exception as e:
            messagebox.showerror("Error", str(e))
        finally:
            try:
                if cur: cur.close()
            finally:
                if conn: conn.close()

    def cancelar():
        reg.destroy()
        if login_window and not is_admin:
            login_window()

    tk.Button(reg, text="Crear", command=register_user).pack(pady=10)
    tk.Button(reg, text="Cancelar", command=cancelar).pack(pady=5)
    reg.mainloop()


if __name__ == "__main__":
    open_register_window()
