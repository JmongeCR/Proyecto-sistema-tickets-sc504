create or replace PACKAGE BODY pkg_tiquetes AS
 -- Procedimiento de crear tiquetes
    PROCEDURE crear_ticket (
        p_asunto       IN VARCHAR2,
        p_descripcion  IN VARCHAR2,
        p_id_usuario   IN NUMBER,
        p_id_estado    IN NUMBER,
        p_id_prioridad IN NUMBER,
        p_id_categoria IN NUMBER
    ) IS
    BEGIN
        INSERT INTO tkt_ticket (
            asunto,
            descripcion,
            fecha_creacion,
            id_usuario_cliente,
            id_estado,
            id_prioridad,
            id_categoria
        ) VALUES ( p_asunto,
                   p_descripcion,
                   sysdate,
                   p_id_usuario,
                   p_id_estado,
                   p_id_prioridad,
                   p_id_categoria );
    COMMIT;
        dbms_output.put_line('Ticket creado exitosamente.');
    EXCEPTION
        WHEN OTHERS THEN
            dbms_output.put_line('Error al crear el ticket: ' || sqlerrm);
    END crear_ticket;
-- Procedimiento de actualizar tiquetes
    PROCEDURE actualizar_ticket (
        p_id_ticket    IN NUMBER,
        p_asunto       IN VARCHAR2,
        p_descripcion  IN VARCHAR2,
        p_id_estado    IN NUMBER,
        p_id_prioridad IN NUMBER,
        p_id_categoria IN NUMBER
    ) IS
    BEGIN
        UPDATE tkt_ticket
        SET
            asunto = p_asunto,
            descripcion = p_descripcion,
            id_estado = p_id_estado,
            id_prioridad = p_id_prioridad,
            id_categoria = p_id_categoria
        WHERE
            id_ticket = p_id_ticket;

        IF SQL%rowcount = 0 THEN
            dbms_output.put_line('No se encontró el ticket con ID: ' || p_id_ticket);
        ELSE
            dbms_output.put_line('Ticket actualizado exitosamente.');
        END IF;
    COMMIT;
    EXCEPTION
        WHEN OTHERS THEN
            dbms_output.put_line('Error al actualizar el ticket: ' || sqlerrm);
    END actualizar_ticket;

-- Procedimiento de eliminar tiquetes
    PROCEDURE eliminar_ticket (
        p_id_ticket IN NUMBER
    ) IS
    BEGIN
        DELETE FROM tkt_ticket
        WHERE
            id_ticket = p_id_ticket;

        IF SQL%rowcount = 0 THEN
            dbms_output.put_line('No se encontró el ticket con ID: ' || p_id_ticket);
        ELSE
            dbms_output.put_line('Ticket eliminado exitosamente.');
        END IF;
    COMMIT;
    EXCEPTION
        WHEN OTHERS THEN
            dbms_output.put_line('Error al eliminar el ticket: ' || sqlerrm);
    END eliminar_ticket;

-- Procedimiento de listar todos los tiquetes
    PROCEDURE listar_tickets IS
    BEGIN
        FOR t IN (
            SELECT
                t.id_ticket,
                t.asunto,
                t.descripcion,
                t.fecha_creacion,
                u.nombre
                || ' '
                || u.apellido1 AS usuario,
                e.nombre_estado,
                p.nivel_prioridad,
                c.nombre_categoria
            FROM
                     tkt_ticket t
                JOIN tkt_usuario   u ON t.id_usuario_cliente = u.id_usuario
                JOIN tkt_estado    e ON t.id_estado = e.id_estado
                JOIN tkt_prioridad p ON t.id_prioridad = p.id_prioridad
                JOIN tkt_categoria c ON t.id_categoria = c.id_categoria
            ORDER BY
                t.id_ticket
        ) LOOP
            dbms_output.put_line('ID: '
                                 || t.id_ticket
                                 || ' | Asunto: '
                                 || t.asunto
                                 || ' | Usuario: '
                                 || t.usuario
                                 || ' | Estado: '
                                 || t.nombre_estado
                                 || ' | Prioridad: '
                                 || t.nivel_prioridad
                                 || ' | Categoría: '
                                 || t.nombre_categoria);
        END LOOP;
    COMMIT;
    END listar_tickets;

-- Función para contar tiquetes por usuario
    FUNCTION contar_tiquetes_por_usuario (
        p_id_usuario IN NUMBER
    ) RETURN NUMBER IS
        v_total NUMBER;
    BEGIN
        SELECT
            COUNT(*)
        INTO v_total
        FROM
            tkt_ticket
        WHERE
            id_usuario_cliente = p_id_usuario;

        RETURN v_total;
    EXCEPTION
        WHEN OTHERS THEN
            dbms_output.put_line('Error al contar tiquetes: ' || sqlerrm);
            RETURN -1;
    END contar_tiquetes_por_usuario;

END pkg_tiquetes;