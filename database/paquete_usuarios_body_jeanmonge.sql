--------------------------------------------------------
-- Archivo creado  - sábado-julio-19-2025   
--------------------------------------------------------
--------------------------------------------------------
--  DDL for Package Body PKG_USUARIOS
--------------------------------------------------------

  CREATE OR REPLACE EDITIONABLE PACKAGE BODY "TICKET_ADMIN"."PKG_USUARIOS" AS

    -- Procedimiento: Insertar nuevo usuario
    PROCEDURE insertar_usuario (
        p_nombre       IN VARCHAR2,
        p_apellido1    IN VARCHAR2,
        p_apellido2    IN VARCHAR2,
        p_correo       IN VARCHAR2,
        p_contrasena   IN VARCHAR2,
        p_telefono     IN VARCHAR2,
        p_id_rol       IN NUMBER
    ) IS
    BEGIN
        INSERT INTO TKT_USUARIO (
            NOMBRE, APELLIDO1, APELLIDO2, CORREO, CONTRASENA, TELEFONO, FECHA_REGISTRO, ID_ROL
        ) VALUES (
            p_nombre, p_apellido1, p_apellido2, p_correo, p_contrasena, p_telefono, SYSDATE, p_id_rol
        );
    END insertar_usuario;

    -- Procedimiento: Actualizar usuario
    PROCEDURE actualizar_usuario (
        p_id_usuario   IN NUMBER,
        p_nombre       IN VARCHAR2,
        p_apellido1    IN VARCHAR2,
        p_apellido2    IN VARCHAR2,
        p_telefono     IN VARCHAR2
    ) IS
    BEGIN
        UPDATE TKT_USUARIO
        SET NOMBRE = p_nombre,
            APELLIDO1 = p_apellido1,
            APELLIDO2 = p_apellido2,
            TELEFONO = p_telefono
        WHERE ID_USUARIO = p_id_usuario;
    END actualizar_usuario;

    -- Procedimiento: Eliminar usuario
    PROCEDURE eliminar_usuario (
        p_id_usuario IN NUMBER
    ) IS
    BEGIN
        DELETE FROM TKT_USUARIO
        WHERE ID_USUARIO = p_id_usuario;
    END eliminar_usuario;

    -- Procedimiento: Listar usuarios
    PROCEDURE listar_usuarios IS
    BEGIN
        FOR u IN (SELECT ID_USUARIO, NOMBRE, APELLIDO1, CORREO FROM TKT_USUARIO)
        LOOP
            DBMS_OUTPUT.PUT_LINE('ID: ' || u.ID_USUARIO || ', Nombre: ' || u.NOMBRE || ', Apellido: ' || u.APELLIDO1 || ', Correo: ' || u.CORREO);
        END LOOP;
    END listar_usuarios;

    -- Función: Obtener usuario por correo
    FUNCTION obtener_usuario_por_correo (
        p_correo IN VARCHAR2
    ) RETURN VARCHAR2 IS
        v_nombre TKT_USUARIO.NOMBRE%TYPE;
    BEGIN
        SELECT NOMBRE INTO v_nombre
        FROM TKT_USUARIO
        WHERE CORREO = p_correo;

        RETURN v_nombre;
    EXCEPTION
        WHEN NO_DATA_FOUND THEN
            RETURN 'No encontrado';
    END obtener_usuario_por_correo;

    -- Función: Verificar si un correo ya está registrado
    FUNCTION existe_correo (
        p_correo IN VARCHAR2
    ) RETURN NUMBER IS
        v_count NUMBER;
    BEGIN
        SELECT COUNT(*) INTO v_count
        FROM TKT_USUARIO
        WHERE CORREO = p_correo;

        RETURN v_count;
    END existe_correo;

END PKG_USUARIOS;

/
