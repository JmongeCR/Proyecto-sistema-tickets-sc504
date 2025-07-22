create or replace PACKAGE pkg_tiquetes AS
  -- Procedimiento de crear tiquetes
    PROCEDURE crear_ticket (
        p_asunto       IN VARCHAR2,
        p_descripcion  IN VARCHAR2,
        p_id_usuario   IN NUMBER,
        p_id_estado    IN NUMBER,
        p_id_prioridad IN NUMBER,
        p_id_categoria IN NUMBER
    );
 -- Procedimiento de actualizar tiquetes
    PROCEDURE actualizar_ticket (
        p_id_ticket    IN NUMBER,
        p_asunto       IN VARCHAR2,
        p_descripcion  IN VARCHAR2,
        p_id_estado    IN NUMBER,
        p_id_prioridad IN NUMBER,
        p_id_categoria IN NUMBER
    );
 -- Procedimiento de eliminar tiquetes
    PROCEDURE eliminar_ticket (
        p_id_ticket IN NUMBER
    );
 -- Procedimiento de listar todos los tiquetes
    PROCEDURE listar_tickets;

  -- Función para contar tiquetes
    FUNCTION contar_tiquetes_por_usuario (
        p_id_usuario IN NUMBER
    ) RETURN NUMBER;

END pkg_tiquetes;