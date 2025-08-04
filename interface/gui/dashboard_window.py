import tkinter as tk
from tkinter import ttk, messagebox
import oracledb
from db.connection import connect_to_db
from gui.create_ticket_window import open_create_ticket_window
from gui.edit_ticket_window import open_edit_ticket_window
from gui.assign_ticket_window import open_assign_ticket_window
from gui.comment_window import open_comment_window
from gui.manage_users_window import open_manage_users_window
from gui.audit_window import open_audit_window

class DashboardWindow:
    def __init__(self, root, user_id, user_role):
        self.root = root
        self.user_id = user_id
        self.user_role = user_role

        self.root.title("Panel de Tickets")
        self.root.geometry("1000x550")

        self.setup_widgets()
        self.cargar_tickets()

    def setup_widgets(self):
        tk.Label(self.root, text=f"Usuario ID: {self.user_id} | Rol: {self.user_role}", font=("Arial", 10, "italic")).pack(pady=5)

        self.tree = ttk.Treeview(self.root, columns=("ID", "Asunto", "Usuario", "Estado", "Prioridad", "Categoría", "Técnico"), show="headings")
        for col in self.tree["columns"]:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=130)
        self.tree.pack(fill=tk.BOTH, expand=True, pady=10)

        self.tree.bind("<Double-1>", self.on_ticket_double_click)

        boton_frame = tk.Frame(self.root)
        boton_frame.pack(pady=10)

        tk.Button(boton_frame, text="Actualizar", command=self.cargar_tickets).pack(side=tk.LEFT, padx=5)

        if self.user_role.lower() in ('cliente', 'usuario', 'soporte', 'técnico'):
            tk.Button(boton_frame, text="Crear Ticket", command=lambda: open_create_ticket_window(self.root, self.user_id)).pack(side=tk.LEFT, padx=5)

        if self.user_role.lower() in ('técnico', 'soporte', 'administrador'):
            tk.Button(boton_frame, text="Asignar Técnico", command=self.asignar_tecnico).pack(side=tk.LEFT, padx=5)

        tk.Button(boton_frame, text="Comentarios", command=self.ver_comentarios).pack(side=tk.LEFT, padx=5)

        if self.user_role.lower() == 'administrador':
            tk.Button(boton_frame, text="Gestionar Usuarios", command=lambda: open_manage_users_window(self.root)).pack(side=tk.LEFT, padx=5)
            tk.Button(boton_frame, text="Auditoría", command=self.ver_auditoria).pack(side=tk.LEFT, padx=5)

        tk.Button(boton_frame, text="Cerrar Sesión", command=self.cerrar_sesion, bg="red", fg="white").pack(side=tk.LEFT, padx=5)

    def cargar_tickets(self):
        try:
            conn = connect_to_db()
            cursor = conn.cursor()
            self.tree.delete(*self.tree.get_children())

            if self.user_role.lower() in ('cliente', 'usuario'):
                cursor.execute("""
                    SELECT ID_TICKET, ASUNTO, USUARIO_CLIENTE, ESTADO, PRIORIDAD, CATEGORIA, TECNICO
                    FROM VW_TICKETS_DETALLE
                    WHERE ID_TICKET IN (
                        SELECT ID_TICKET FROM TKT_TICKET WHERE ID_USUARIO_CLIENTE = :1
                    )
                    ORDER BY ID_TICKET
                """, (self.user_id,))
            else:
                cursor.execute("""
                    SELECT ID_TICKET, ASUNTO, USUARIO_CLIENTE, ESTADO, PRIORIDAD, CATEGORIA, TECNICO
                    FROM VW_TICKETS_DETALLE
                    ORDER BY ID_TICKET
                """)

            for row in cursor:
                self.tree.insert("", tk.END, values=row)

        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar tickets: {e}")
        finally:
            if cursor: cursor.close()
            if conn: conn.close()

    def on_ticket_double_click(self, event):
        if self.user_role.lower() in ("soporte", "técnico"):
            selected_item = self.tree.focus()
            if selected_item:
                ticket_data = self.tree.item(selected_item)["values"]
                open_edit_ticket_window(self.root, ticket_data)

    def asignar_tecnico(self):
        selected_item = self.tree.focus()
        if not selected_item:
            messagebox.showwarning("Advertencia", "Seleccione un ticket para asignar")
            return
        ticket_data = self.tree.item(selected_item)["values"]
        ticket_id = ticket_data[0]
        open_assign_ticket_window(self.root, ticket_id)

    def ver_comentarios(self):
        selected_item = self.tree.focus()
        if not selected_item:
            messagebox.showwarning("Advertencia", "Seleccione un ticket para ver sus comentarios")
            return
        ticket_data = self.tree.item(selected_item)["values"]
        ticket_id = ticket_data[0]
        open_comment_window(self.root, ticket_id, self.user_id)

    def ver_auditoria(self):
        open_audit_window()

    def cerrar_sesion(self):
        self.root.destroy()
        from gui.login_window import login_window
        login_window()

if __name__ == "__main__":
    root = tk.Tk()
    app = DashboardWindow(root, user_id=61, user_role='Administrador')
    root.mainloop()
