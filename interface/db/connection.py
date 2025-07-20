
import oracledb

def connect_to_db():
    try:
        conn = oracledb.connect(
            user="ticket_admin",
            password="Ticket2025",
            dsn="localhost/orclpdb"
        )
        return conn
    except Exception as e:
        print("Error al conectar:", e)
        return None

