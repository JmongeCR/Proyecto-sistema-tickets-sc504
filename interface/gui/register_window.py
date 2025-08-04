import tkinter as tk
from tkinter import ttk, messagebox
from db.connection import connect_to_db
import oracledb

def open_register_window(is_admin=False):
    from gui.login_window import login_window  

    reg = tk.Tk()
    reg.title("Registro de Usuario")
    reg.geometry("400x500")

    # Centrar ventana
    reg.update_idletasks()
    width = 400
    height = 500
    x = (reg.winfo_screenwidth() // 2) - (width // 2)
    y = (reg.winfo_screenheight() // 2) - (height // 2)
    reg.geometry(f"{width}x{height}+{x}+{y}")

    # Campos
    fields = {}
    for label in ["Nombre", "Primer Apellido", "Segundo Apellido", "Correo", "Contraseña", "Teléfono"]:
        tk.Label(reg, text=label).pack()
        entry = tk.Entry(reg, show="*" if label == "Contraseña" else None)
        entry.pack()
        fields[label] = entry

    # Combo rol
    tk.Label(reg, text="Rol").pack()
    combo_rol = ttk.Combobox(reg, state="readonly")
    combo_rol.pack()

    roles_dict = {}
    conn = connect_to_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT ID_ROL, NOMBRE_ROL FROM TKT_ROL")
            for rol_id, rol_name in cursor.fetchall():
                roles_dict[rol_name] = rol_id

            if is_admin:
                combo_rol['values'] = list(roles_dict.keys())
                combo_rol.set("Usuario")
            else:
                combo_rol['values'] = ["Usuario"]
                combo_rol.current(0)
        except Exception as e:
            messagebox.showerror("Error", str(e))
        finally:
            cursor.close()
            conn.close()

    def register_user():
        nombre = fields["Nombre"].get()
        apellido1 = fields["Primer Apellido"].get()
        apellido2 = fields["Segundo Apellido"].get()
        correo = fields["Correo"].get()
        contrasena = fields["Contraseña"].get()
        telefono = fields["Teléfono"].get()
        rol = combo_rol.get()
        id_rol = roles_dict.get(rol, None)

        if not all([nombre, apellido1, correo, contrasena, rol]):
            messagebox.showerror("Error", "Por favor complete todos los campos obligatorios.")
            return

        conn = connect_to_db()
        if conn:
            try:
                cursor = conn.cursor()
                existe = cursor.var(oracledb.NUMBER)  # variable OUT
                cursor.callproc("PKG_USUARIOS.EXISTE_CORREO", [correo, existe])

                if existe.getvalue() == 1:
                    messagebox.showerror("Error", "Este correo ya está registrado")
                    return

                cursor.callproc("PKG_USUARIOS.INSERTAR_USUARIO", [
                    nombre, apellido1, apellido2, correo, contrasena, telefono, id_rol
                ])
                conn.commit()
                messagebox.showinfo("Éxito", "Usuario registrado correctamente.")
                reg.destroy()
                if not is_admin:
                    login_window()
            except Exception as e:
                messagebox.showerror("Error", str(e))
            finally:
                cursor.close()
                conn.close()

    def regresar():
        reg.destroy()
        if not is_admin:
            login_window()

    # Botones
    tk.Button(reg, text="Registrar", command=register_user).pack(pady=10)
    tk.Button(reg, text="Regresar", command=regresar).pack()

    reg.mainloop()

if __name__ == "__main__":
    open_register_window()
