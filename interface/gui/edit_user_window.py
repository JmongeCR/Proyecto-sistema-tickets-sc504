
import tkinter as tk
from tkinter import ttk, messagebox
from db.connection import connect_to_db
import oracledb

def open_edit_user_window(parent, user_data, on_success):
    ventana = tk.Toplevel(parent)
    ventana.title("Modificar Usuario")
    ventana.geometry("400x500")
    ventana.resizable(False, False)

    labels = ["Nombre", "Apellido1", "Apellido2", "Correo", "Contraseña", "Teléfono", "Rol"]
    entries = {}

    for i, label in enumerate(labels):
        tk.Label(ventana, text=label).pack()
        if label == "Rol":
            rol_combobox = ttk.Combobox(ventana, state="readonly")
            rol_combobox.pack()
            entries[label] = rol_combobox
        else:
            entry = tk.Entry(ventana, show="*" if label == "Contraseña" else None)
            entry.pack()
            entries[label] = entry

    # Obtener roles desde BD
    roles_dict = {}
    conn = connect_to_db()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("SELECT ID_ROL, NOMBRE_ROL FROM TKT_ROL")
            for rol_id, rol_nombre in cur.fetchall():
                roles_dict[rol_nombre] = rol_id
            entries["Rol"]["values"] = list(roles_dict.keys())
        finally:
            cur.close()
            conn.close()

    # Llenar campos con los datos actuales
    user_id, nombre, apellido1, apellido2, correo, contrasena, telefono, rol_nombre = user_data
    entries["Nombre"].insert(0, nombre)
    entries["Apellido1"].insert(0, apellido1)
    entries["Apellido2"].insert(0, apellido2)
    entries["Correo"].insert(0, correo)
    entries["Contraseña"].insert(0, contrasena)
    entries["Teléfono"].insert(0, telefono)
    entries["Rol"].set(rol_nombre)

    def guardar_cambios():
        nuevo_nombre = entries["Nombre"].get()
        nuevo_apellido1 = entries["Apellido1"].get()
        nuevo_apellido2 = entries["Apellido2"].get()
        nuevo_correo = entries["Correo"].get()
        nueva_contra = entries["Contraseña"].get()
        nuevo_telefono = entries["Teléfono"].get()
        nuevo_rol = roles_dict.get(entries["Rol"].get())

        if not all([nuevo_nombre, nuevo_apellido1, nuevo_correo, nueva_contra, nuevo_telefono, nuevo_rol]):
            messagebox.showerror("Error", "Todos los campos son obligatorios.")
            return

        conn = connect_to_db()
        if conn:
            try:
                cur = conn.cursor()
                cur.callproc("PKG_USUARIOS.ACTUALIZAR_USUARIO", [
                    user_id, nuevo_nombre, nuevo_apellido1, nuevo_apellido2,
                    nuevo_correo, nueva_contra, nuevo_telefono, nuevo_rol
                ])
                conn.commit()
                messagebox.showinfo("Éxito", "Usuario actualizado correctamente.")
                ventana.destroy()
                on_success()
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo actualizar: {e}")
            finally:
                cur.close()
                conn.close()

    tk.Button(ventana, text="Guardar Cambios", command=guardar_cambios).pack(pady=10)
    tk.Button(ventana, text="Cancelar", command=ventana.destroy).pack(pady=5)
