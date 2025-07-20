--------------------------------------------------------
-- Archivo creado  - sábado-julio-19-2025   
--------------------------------------------------------
--------------------------------------------------------
--  DDL for Package PKG_USUARIOS
--------------------------------------------------------

  CREATE OR REPLACE EDITIONABLE PACKAGE "TICKET_ADMIN"."PKG_USUARIOS" AS
    PROCEDURE insertar_usuario (
        p_nombre       IN VARCHAR2,
        p_apellido1    IN VARCHAR2,
        p_apellido2    IN VARCHAR2,
        p_correo       IN VARCHAR2,
        p_contrasena   IN VARCHAR2,
        p_telefono     IN VARCHAR2,
        p_id_rol       IN NUMBER
    );

    PROCEDURE actualizar_usuario (
        p_id_usuario   IN NUMBER,
        p_nombre       IN VARCHAR2,
        p_apellido1    IN VARCHAR2,
        p_apellido2    IN VARCHAR2,
        p_telefono     IN VARCHAR2
    );

    PROCEDURE eliminar_usuario (
        p_id_usuario IN NUMBER
    );

    PROCEDURE listar_usuarios;

    FUNCTION obtener_usuario_por_correo (
        p_correo IN VARCHAR2
    ) RETURN VARCHAR2;

  FUNCTION existe_correo(p_correo VARCHAR2) RETURN NUMBER;



END PKG_USUARIOS;

/
