# db/connection.py
import os

# Intenta usar python-oracledb; si no, cae a cx_Oracle
try:
    import oracledb as _oracle
except Exception:
    import cx_Oracle as _oracle  # respaldo si no tienes oracledb

def connect_to_db():
    """
    Conexión simple (modo Thin por defecto). No uses 'encoding=' aquí.
    Ajusta las variables de entorno ORACLE_USER / ORACLE_PASS / ORACLE_DSN si quieres.
    """
    user = os.getenv("ORACLE_USER", "TICKET_ADMIN")
    password = os.getenv("ORACLE_PASS", "Ticket2025")
    dsn = os.getenv("ORACLE_DSN", "localhost:1521/ORCLPDB")

    conn = _oracle.connect(user=user, password=password, dsn=dsn)
    # Evita cuelgues en llamadas a paquetes (milisegundos; soportado por oracledb y cx_Oracle>=7)
    try:
        conn.call_timeout = 10000  # 10s
    except Exception:
        pass

    return conn
