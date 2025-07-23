
-------------------PAQUETE Y CUERPO ROLES---------------------------------------

CREATE OR REPLACE PACKAGE PKG_ROLES AS

    PROCEDURE crear_rol(p_id_rol in NUMBER, p_nombre_rol in VARCHAR2);
    PROCEDURE actualizar_rol(p_id_rol in NUMBER, p_nombre_rol in VARCHAR2);
    PROCEDURE eliminar_rol(p_id_rol in NUMBER);
    
END PKG_ROLES;
/

CREATE OR REPLACE PACKAGE BODY PKG_ROLES AS

---------------------Procedimiento para insertar un rol enla tabla--------------
    PROCEDURE crear_rol (p_id_rol IN NUMBER, p_nombre_rol IN VARCHAR2) IS
    BEGIN
        INSERT INTO TKT_ROL (ID_ROL, NOMBRE_ROL)
        VALUES (p_id_rol, p_nombre_rol);
    END crear_rol;
    
-------------------Procedimiento para actualizar un rol en la tabla-------------
    PROCEDURE actualizar_rol (p_id_rol IN NUMBER, p_nombre_rol IN VARCHAR2) IS
    BEGIN 
        UPDATE TKT_ROL
        SET NOMBRE_ROL = p_nombre_rol
        WHERE ID_ROL = p_id_rol;
    END actualizar_rol;
    
---------------------Procedimiento para insertar un rol en la tabla-------------
    PROCEDURE eliminar_rol (p_id_rol in NUMBER)IS 
    BEGIN
        DELETE FROM TKT_ROL
        WHERE ID_ROL = p_id_rol;
    END eliminar_rol;

END PKG_ROLES;
/
    
BEGIN 
PKG_ROLES.crear_rol(p_id_rol => 4, p_nombre_rol => 'Prueba');
END;

SELECT * FROM TKT_ROL;

BEGIN 
PKG_ROLES.actualizar_rol(p_id_rol => 4, p_nombre_rol => 'Prueba2');
END;

BEGIN
PKG_ROLES.eliminar_rol(p_id_rol => 4);
END;

CREATE OR REPLACE VIEW VW_ROLES AS
SELECT ID_ROL, NOMBRE_ROL
FROM TKT_ROL;

SELECT * FROM VW_ROLES
ORDER BY NOMBRE_ROL;

COMMIT;