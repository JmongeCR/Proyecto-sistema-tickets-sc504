import tkinter as tk
from tkinter import ttk, messagebox
from db.connection import connect_to_db
import oracledb

def open_comment_window(parent, ticket_id, user_id):
    win = tk.Toplevel(parent)
    win.title("Comentarios del Ticket")
    win.geometry("600x400")

    tk.Label(win, text=f"Comentarios del Ticket #{ticket_id}", font=("Arial", 12, "bold")).pack(pady=10)

    comment_list = tk.Listbox(win, width=80, height=10)
    comment_list.pack(pady=10)

    def cargar_comentarios():
        comment_list.delete(0, tk.END)
        conn = connect_to_db()
        if conn:
            try:
                cur = conn.cursor()
                cur.execute("""
                    SELECT c.ID_COMENTARIO, u.NOMBRE || ' ' || u.APELLIDO1 AS USUARIO,
                           c.CONTENIDO, TO_CHAR(c.FECHA_COMENTARIO, 'DD-MM-YYYY HH24:MI')
                    FROM TKT_COMENTARIO c
                    JOIN TKT_USUARIO u ON c.ID_USUARIO = u.ID_USUARIO
                    WHERE c.ID_TICKET = :1
                    ORDER BY c.FECHA_COMENTARIO DESC
                """, (ticket_id,))

                for row in cur.fetchall():
                    comment_list.insert(tk.END, f"[{row[3]}] {row[1]}: {row[2]}")
            except Exception as e:
                messagebox.showerror("Error", f"Error al cargar comentarios: {e}")
            finally:
                cur.close()
                conn.close()

    # Caja de nuevo comentario
    tk.Label(win, text="Nuevo Comentario:").pack()
    text_comentario = tk.Text(win, height=4, width=70)
    text_comentario.pack(pady=5)

    def agregar_comentario():
        contenido = text_comentario.get("1.0", tk.END).strip()
        if not contenido:
            messagebox.showwarning("Advertencia", "El comentario no puede estar vacío")
            return

        conn = connect_to_db()
        if conn:
            try:
                cur = conn.cursor()
                cur.callproc("PKG_COMENTARIOS.INSERTAR_COMENTARIO", [ticket_id, user_id, contenido])
                conn.commit()
                messagebox.showinfo("Éxito", "Comentario agregado correctamente")
                text_comentario.delete("1.0", tk.END)
                cargar_comentarios()
            except Exception as e:
                messagebox.showerror("Error", f"Error al insertar comentario: {e}")
            finally:
                cur.close()
                conn.close()

    tk.Button(win, text="Agregar Comentario", command=agregar_comentario).pack(pady=5)
    tk.Button(win, text="Cerrar", command=win.destroy).pack(pady=10)

    cargar_comentarios()
    win.mainloop()
