import tkinter as tk
from tkinter import messagebox
from db.connection import connect_to_db
from gui import register_window
from gui.dashboard_window import DashboardWindow
import oracledb

def login_window():
    window = tk.Toplevel() if tk._default_root else tk.Tk()
    window.title("Inicio de Sesión")
    window.geometry("400x350")

    # Centrar ventana
    window.update_idletasks()
    width = 400
    height = 350
    x = (window.winfo_screenwidth() // 2) - (width // 2)
    y = (window.winfo_screenheight() // 2) - (height // 2)
    window.geometry(f"{width}x{height}+{x}+{y}")

    # Mensaje de bienvenida
    tk.Label(window, text="Bienvenido al sistema de tickets para TI", font=("Arial", 12, "bold")).pack(pady=10)
    tk.Label(window, text="Por favor, inicie sesión o registre su usuario", font=("Arial", 10)).pack(pady=5)

    # Campos de entrada
    tk.Label(window, text="Correo:").pack(pady=5)
    entry_user = tk.Entry(window)
    entry_user.pack()

    tk.Label(window, text="Contraseña:").pack(pady=5)
    entry_pass = tk.Entry(window, show="*")
    entry_pass.pack()

    def iniciar_sesion():
        correo = entry_user.get()
        contrasena = entry_pass.get()
        conn = connect_to_db()
        if conn:
            try:
                cursor = conn.cursor()
                resultado = cursor.var(oracledb.NUMBER)
                id_usuario = cursor.var(oracledb.NUMBER)
                rol = cursor.var(oracledb.STRING)

                cursor.callproc("PKG_USUARIOS.LOGIN_USUARIO", [
                    correo, contrasena, resultado, id_usuario, rol
                ])

                if resultado.getvalue() == 1:
                    messagebox.showinfo("Éxito", f"Bienvenido {rol.getvalue()}")
                    window.destroy()
                    root = tk.Tk()
                    app = DashboardWindow(root, id_usuario.getvalue(), rol.getvalue())
                    root.mainloop()
                else:
                    messagebox.showerror("Error", "Credenciales incorrectas")
            except Exception as e:
                messagebox.showerror("Error", f"Ocurrió un error: {e}")
            finally:
                cursor.close()
                conn.close()

    # Botones
    tk.Button(window, text="Iniciar Sesión", command=iniciar_sesion).pack(pady=10)
    tk.Button(window, text="Crear Usuario", command=lambda: [window.destroy(), register_window.open_register_window()]).pack()
    tk.Button(window, text="Salir del Sistema", command=window.destroy, bg="red", fg="white").pack(pady=20)

    window.mainloop()

if __name__ == "__main__":
    login_window()
