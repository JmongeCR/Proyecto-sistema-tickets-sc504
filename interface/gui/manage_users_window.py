
import tkinter as tk
from tkinter import ttk, messagebox
from db.connection import connect_to_db
from gui.register_window import open_register_window
from gui.edit_user_window import open_edit_user_window
import oracledb

def open_manage_users_window(parent):
    win = tk.Toplevel(parent)
    win.title("Gestión de Usuarios")
    win.geometry("1000x500")

    tree = ttk.Treeview(win, columns=("ID", "Nombre", "Apellido1", "Apellido2", "Correo", "Contraseña", "Teléfono", "Rol"), show="headings")
    for col in tree["columns"]:
        tree.heading(col, text=col)
        tree.column(col, width=120)
    tree.pack(fill=tk.BOTH, expand=True, pady=10)

    def cargar_usuarios():
        tree.delete(*tree.get_children())
        conn = connect_to_db()
        if conn:
            try:
                cur = conn.cursor()
                cur.execute(
                    """
                    SELECT 
                        u.ID_USUARIO,
                        u.NOMBRE,
                        u.APELLIDO1,
                        u.APELLIDO2,
                        u.CORREO,
                        u.CONTRASENA,
                        u.TELEFONO,
                        r.NOMBRE_ROL
                    FROM TKT_USUARIO u
                    JOIN TKT_ROL r ON u.ID_ROL = r.ID_ROL
                    ORDER BY u.ID_USUARIO
                    """
                )
                for row in cur.fetchall():
                    tree.insert("", tk.END, values=row)
            except Exception as e:
                messagebox.showerror("Error", f"Error al cargar usuarios: {e}")
            finally:
                cur.close()
                conn.close()

    def eliminar_usuario():
        selected = tree.focus()
        if not selected:
            messagebox.showwarning("Advertencia", "Seleccione un usuario para eliminar")
            return

        user_data = tree.item(selected)["values"]
        user_id, nombre, *_ = user_data

        if messagebox.askyesno("Confirmar", f"¿Está seguro de eliminar a {nombre}?"):
            conn = connect_to_db()
            if conn:
                try:
                    cur = conn.cursor()
                    cur.callproc("PKG_USUARIOS.ELIMINAR_USUARIO", [user_id])
                    conn.commit()
                    messagebox.showinfo("Éxito", "Usuario eliminado")
                    cargar_usuarios()
                except Exception as e:
                    messagebox.showerror("Error", f"No se pudo eliminar: {e}")
                finally:
                    cur.close()
                    conn.close()

    def editar_usuario():
        selected = tree.selection()
        if selected:
            datos = tree.item(selected[0])["values"]
            open_edit_user_window(win, datos, cargar_usuarios)
        else:
            messagebox.showwarning("Atención", "Seleccione un usuario primero.")

    def crear_usuario():
        win.destroy()
        open_register_window(is_admin=True)

    btn_frame = tk.Frame(win)
    btn_frame.pack(pady=5)

    tk.Button(btn_frame, text="Crear Usuario", command=crear_usuario).pack(side=tk.LEFT, padx=5)
    tk.Button(btn_frame, text="Eliminar Usuario", command=eliminar_usuario).pack(side=tk.LEFT, padx=5)
    tk.Button(btn_frame, text="Editar Usuario", command=editar_usuario).pack(side=tk.LEFT, padx=5)
    tk.Button(btn_frame, text="Cerrar", command=win.destroy, bg="red", fg="white").pack(side=tk.LEFT, padx=5)

    cargar_usuarios()
    win.mainloop()
