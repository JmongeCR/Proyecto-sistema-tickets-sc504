import tkinter as tk
from tkinter import messagebox
import oracledb
from db.connection import connect_to_db

def _normalize_role(role_raw: str) -> str:
    r = (role_raw or "").strip().lower()
    if r in ("admin", "administrador", "administrator"):
        return "Admin"
    if r in ("técnico", "tecnico", "tech", "soporte", "support"):
        return "Técnico"
    return "Usuario"

def login_window():
    root = tk.Tk()
    root.title("Inicio de Sesión")
    root.geometry("400x350")
    root.update_idletasks()
    w, h = 400, 350
    x = (root.winfo_screenwidth() // 2) - (w // 2)
    y = (root.winfo_screenheight() // 2) - (h // 2)
    root.geometry(f"{w}x{h}+{x}+{y}")

    tk.Label(root, text="Bienvenido al sistema de tickets para TI", font=("Arial", 12, "bold")).pack(pady=10)
    tk.Label(root, text="Por favor, inicie sesión o registre su usuario", font=("Arial", 10)).pack(pady=5)

    tk.Label(root, text="Correo:").pack(pady=(10, 3))
    entry_user = tk.Entry(root); entry_user.pack()
    tk.Label(root, text="Contraseña:").pack(pady=(10, 3))
    entry_pass = tk.Entry(root, show="*"); entry_pass.pack()

    def abrir_registro():
        try:
            from gui.register_window import open_register_window
            open_register_window(is_admin=False)
        except Exception as e:
            messagebox.showerror("Registro", f"No se pudo abrir registro:\n{e}")

    def iniciar_sesion():
        correo = entry_user.get().strip().lower()
        clave  = entry_pass.get().strip()
        if not correo or not clave:
            messagebox.showwarning("Validación", "Digite correo y contraseña.")
            return

        conn = cur = None
        try:
            conn = connect_to_db()
            cur = conn.cursor()

            o_result = cur.var(oracledb.DB_TYPE_NUMBER)
            o_id = cur.var(oracledb.DB_TYPE_NUMBER)
            o_rol = cur.var(oracledb.DB_TYPE_VARCHAR)

            ok = False; uid = None; rol_text = ""

            try:
                #(correo, clave, o_result, o_id, o_rol)
                cur.callproc("PKG_USUARIOS.LOGIN_USUARIO", [correo, clave, o_result, o_id, o_rol])
                ok = int(o_result.getvalue() or 0) == 1
                if ok:
                    uid = int(o_id.getvalue()); rol_text = str(o_rol.getvalue() or "")
            except oracledb.DatabaseError:
                try:
                   #(correo, clave, o_id, o_rol)
                    o_id = cur.var(oracledb.DB_TYPE_NUMBER)
                    o_rol = cur.var(oracledb.DB_TYPE_VARCHAR)
                    cur.callproc("PKG_USUARIOS.LOGIN_USUARIO", [correo, clave, o_id, o_rol])
                    v = o_id.getvalue()
                    ok = v is not None
                    if ok:
                        uid = int(v); rol_text = str(o_rol.getvalue() or "")
                except Exception as e2:
                    raise RuntimeError(f"No pude invocar PKG_USUARIOS.LOGIN_USUARIO:\n{e2}")

            if not ok or uid is None:
                messagebox.showerror("Login", "Credenciales incorrectas.")
                return

            role_norm = _normalize_role(rol_text)

            # Cargar Dashboard
            from gui.dashboard_window import DashboardWindow
            for wdg in root.winfo_children():
                try: wdg.destroy()
                except: pass
            root.geometry("980x600")
            DashboardWindow(root, user_id=uid, role=role_norm, user_email=correo)

        except Exception as e:
            messagebox.showerror("Error", f"Ocurrió un error al iniciar sesión:\n{e}")
        finally:
            try:
                if cur: cur.close()
            except: pass
            try:
                if conn: conn.close()
            except: pass

    tk.Button(root, text="Iniciar Sesión", command=iniciar_sesion).pack(pady=12)
    tk.Button(root, text="Crear Usuario", command=abrir_registro).pack()
    tk.Button(root, text="Salir del Sistema", command=root.destroy, bg="red", fg="white").pack(pady=16)
    root.mainloop()
