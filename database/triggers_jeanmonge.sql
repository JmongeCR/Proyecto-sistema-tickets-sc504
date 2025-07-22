--------------------------------------------------------
-- Archivo creado  - sábado-julio-19-2025   
--------------------------------------------------------
--------------------------------------------------------
--  DDL for Trigger TRG_CORREO_UNICO
--------------------------------------------------------

  CREATE OR REPLACE EDITIONABLE TRIGGER "TICKET_ADMIN"."TRG_CORREO_UNICO" 
BEFORE INSERT ON TKT_USUARIO
FOR EACH ROW
DECLARE
    v_count NUMBER;
BEGIN
    SELECT COUNT(*) INTO v_count
    FROM TKT_USUARIO
    WHERE CORREO = :NEW.CORREO;

    IF v_count > 0 THEN
        RAISE_APPLICATION_ERROR(-20001, 'El correo ya está registrado');
    END IF;
END;
/
ALTER TRIGGER "TICKET_ADMIN"."TRG_CORREO_UNICO" ENABLE;

--------------------------------------------------------
-- Archivo creado  - lunes-julio-22-2025   
--------------------------------------------------------
--------------------------------------------------------
--  DDL for Trigger TRG_CREACION_TIQUETE
--------------------------------------------------------
CREATE OR REPLACE TRIGGER trg_aviso_creacion_ticket
AFTER INSERT ON TKT_TICKET
FOR EACH ROW
DECLARE
  v_usuario_nombre VARCHAR2(200);
BEGIN
  -- Obtener el nombre completo del usuario que creó el ticket
  SELECT NOMBRE || ' ' || APELLIDO1 INTO v_usuario_nombre
  FROM TKT_USUARIO
  WHERE ID_USUARIO = :NEW.ID_USUARIO_CLIENTE;

  -- Mostrar mensaje
  DBMS_OUTPUT.PUT_LINE('🎫 Se ha creado un nuevo ticket (ID: ' || :NEW.ID_TICKET || ') por el usuario: ' || v_usuario_nombre || '.');
EXCEPTION
  WHEN OTHERS THEN
    DBMS_OUTPUT.PUT_LINE('🎫 Se creó un ticket, pero ocurrió un error al obtener el nombre del usuario: ' || SQLERRM);
END;
