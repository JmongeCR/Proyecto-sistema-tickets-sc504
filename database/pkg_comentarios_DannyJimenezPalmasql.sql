CREATE SEQUENCE seq_usuarios START WITH 1 INCREMENT BY 1;

CREATE SEQUENCE seq_tickets START WITH 1 INCREMENT BY 1;
CREATE SEQUENCE seq_comentarios START WITH 1 INCREMENT BY 1;

CREATE TABLE usuarios (
    id NUMBER DEFAULT seq_usuarios.NEXTVAL PRIMARY KEY,
    nombre VARCHAR2(100) NOT NULL
);

CREATE TABLE tickets (
    id NUMBER DEFAULT seq_tickets.NEXTVAL PRIMARY KEY,
    usuario_id NUMBER NOT NULL,
    asunto VARCHAR2(100) NOT NULL,
    descripcion VARCHAR2(1000),
    fecha_creacion DATE DEFAULT SYSDATE,
    estado VARCHAR2(20),
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
);

CREATE TABLE comentarios (
    id NUMBER DEFAULT seq_comentarios.NEXTVAL PRIMARY KEY,
    ticket_id NUMBER NOT NULL,
    usuario_id NUMBER NOT NULL,
    contenido CLOB,
    fecha_comentario DATE DEFAULT SYSDATE,
    FOREIGN KEY (ticket_id) REFERENCES tickets(id),
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
);

CREATE OR REPLACE PACKAGE PKG_REPORTES AS
  FUNCTION cantidad_reportes_por_usuario(p_usuario_id NUMBER) RETURN NUMBER;
END PKG_REPORTES;
/
CREATE OR REPLACE PACKAGE BODY PKG_REPORTES AS
  FUNCTION cantidad_reportes_por_usuario(p_usuario_id NUMBER) RETURN NUMBER IS
    v_cantidad NUMBER;
  BEGIN
    SELECT COUNT(*) INTO v_cantidad
    FROM tickets
    WHERE usuario_id = p_usuario_id;
    RETURN v_cantidad;
  END cantidad_reportes_por_usuario;
END PKG_REPORTES;
/

CREATE OR REPLACE VIEW VW_REPORTE_X_USUARIO AS
SELECT u.id AS usuario_id,
       u.nombre AS usuario,
       COUNT(t.id) AS total_tickets
FROM usuarios u
LEFT JOIN tickets t ON t.usuario_id = u.id
GROUP BY u.id, u.nombre;

CREATE OR REPLACE PACKAGE PKG_COMENTARIOS AS
  PROCEDURE insertar_comentario(
      p_ticket_id   IN NUMBER,
      p_usuario_id  IN NUMBER,
      p_contenido   IN CLOB
  );
  PROCEDURE actualizar_comentario(
      p_comentario_id   IN NUMBER,
      p_nuevo_contenido IN CLOB
  );
  PROCEDURE eliminar_comentario(
      p_comentario_id IN NUMBER
  );
END PKG_COMENTARIOS;
/
CREATE OR REPLACE PACKAGE BODY PKG_COMENTARIOS AS

  PROCEDURE insertar_comentario(
      p_ticket_id   IN NUMBER,
      p_usuario_id  IN NUMBER,
      p_contenido   IN CLOB
  ) IS
  BEGIN
    INSERT INTO comentarios (ticket_id, usuario_id, contenido, fecha_comentario)
    VALUES (p_ticket_id, p_usuario_id, p_contenido, SYSDATE);
    COMMIT;
  END insertar_comentario;

  PROCEDURE actualizar_comentario(
      p_comentario_id   IN NUMBER,
      p_nuevo_contenido IN CLOB
  ) IS
  BEGIN
    UPDATE comentarios
    SET contenido = p_nuevo_contenido,
        fecha_comentario = SYSDATE
    WHERE id = p_comentario_id;
    COMMIT;
  END actualizar_comentario;

  PROCEDURE eliminar_comentario(
      p_comentario_id IN NUMBER
  ) IS
  BEGIN
    DELETE FROM comentarios
    WHERE id = p_comentario_id;
    COMMIT;
  END eliminar_comentario;

END PKG_COMENTARIOS;
/

CREATE OR REPLACE VIEW VW_COMENTARIOS_RECIENTES AS
SELECT c.id           AS comentario_id,
       c.ticket_id    AS ticket,
       u.nombre       AS usuario,
       c.contenido,
       c.fecha_comentario
FROM comentarios c
JOIN usuarios u ON c.usuario_id = u.id
WHERE c.fecha_comentario >= SYSDATE - 7;


