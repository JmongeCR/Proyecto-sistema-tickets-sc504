
import os
import oracledb

ORA_USER = os.getenv("ORA_USER", "TICKET_ADMIN")
ORA_PASS = os.getenv("ORA_PASS", "Ticket2025")
ORA_DSN  = os.getenv("ORA_DSN",  "localhost/ORCLPDB")

def _conn():
    return oracledb.connect(user=ORA_USER, password=ORA_PASS, dsn=ORA_DSN, encoding="UTF-8")

def login(correo: str, clave: str):
    """
    Llama a PKG_USUARIOS.LOGIN_USUARIO(correo, clave, o_id, o_nombre, o_id_rol)
    Retorna (id_usuario, nombre, id_rol)
    """
    conn = _conn()
    try:
        cur = conn.cursor()
        o_id  = cur.var(oracledb.DB_TYPE_NUMBER)
        o_nom = cur.var(oracledb.DB_TYPE_VARCHAR)
        o_rol = cur.var(oracledb.DB_TYPE_NUMBER)
        cur.callproc("PKG_USUARIOS.LOGIN_USUARIO", [correo, clave, o_id, o_nom, o_rol])
        return int(o_id.getvalue()), o_nom.getvalue(), int(o_rol.getvalue())
    finally:
        try:
            cur.close()
        except:
            pass
        conn.close()
