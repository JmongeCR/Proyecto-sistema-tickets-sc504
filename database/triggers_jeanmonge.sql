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
