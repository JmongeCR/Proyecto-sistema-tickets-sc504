import tkinter as tk
from tkinter import messagebox
from db.connection import connect_to_db
from gui import register_window

def login_window():
    root = tk.Tk()
    root.title("Inicio de Sesión")
    root.geometry("400x350")

    # Centrar ventana
    root.update_idletasks()
    width = 400
    height = 350
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f"{width}x{height}+{x}+{y}")

    # Mensaje de bienvenida
    tk.Label(root, text="Bienvenido al sistema de tickets para TI", font=("Arial", 12, "bold")).pack(pady=10)
    tk.Label(root, text="Por favor, inicie sesión o registre su usuario", font=("Arial", 10)).pack(pady=5)

    # Campos de entrada
    tk.Label(root, text="Correo:").pack(pady=5)
    entry_user = tk.Entry(root)
    entry_user.pack()

    tk.Label(root, text="Contraseña:").pack(pady=5)
    entry_pass = tk.Entry(root, show="*")
    entry_pass.pack()

    def iniciar_sesion():
        correo = entry_user.get()
        contrasena = entry_pass.get()
        conn = connect_to_db()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.callproc("PKG_USUARIOS.LOGIN_USUARIO", [correo, contrasena, None])
                result = cursor.fetchone()
                if result and result[0] == 1:
                    messagebox.showinfo("Éxito", "Inicio de sesión exitoso")
                    root.destroy()
                else:
                    messagebox.showerror("Error", "Credenciales incorrectas")
            except Exception as e:
                messagebox.showerror("Error", f"Ocurrió un error: {e}")
            finally:
                cursor.close()
                conn.close()

    # Botones
    tk.Button(root, text="Iniciar Sesión", command=iniciar_sesion).pack(pady=10)
    tk.Button(root, text="Crear Usuario", command=lambda: [root.destroy(), register_window.open_register_window()]).pack()
    tk.Button(root, text="Salir del Sistema", command=root.quit, bg="red", fg="white").pack(pady=20)

    root.mainloop()

if __name__ == "__main__":
    login_window()
