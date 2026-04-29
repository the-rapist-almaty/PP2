
--  FUNCTION: search_contacts
--  Searches across first_name, email, and all phone numbers

CREATE OR REPLACE FUNCTION search_contacts(p_query TEXT)
RETURNS TABLE(
    id         INT,
    first_name VARCHAR,
    email      VARCHAR,
    birthday   DATE,
    group_name VARCHAR,
    phones     TEXT
) AS $$
BEGIN
    RETURN QUERY
        SELECT DISTINCT
            c.id,
            c.first_name,
            c.email,
            c.birthday,
            g.name,
            STRING_AGG(p.phone || ' (' || COALESCE(p.type, '?') || ')', ', ') AS phones
        FROM contacts c
        LEFT JOIN groups g  ON g.id = c.group_id
        LEFT JOIN phones p  ON p.contact_id = c.id
        WHERE
            c.first_name ILIKE '%' || p_query || '%'
            OR c.email   ILIKE '%' || p_query || '%'
            OR p.phone   ILIKE '%' || p_query || '%'
        GROUP BY c.id, c.first_name, c.email, c.birthday, g.name
        ORDER BY c.first_name;
END;
$$ LANGUAGE plpgsql;



--  FUNCTION: get_contacts_paginated
--  Returns contacts with pagination

CREATE OR REPLACE FUNCTION get_contacts_paginated(
    p_limit  INT,
    p_offset INT,
    p_sort   VARCHAR DEFAULT 'name'   -- 'name' | 'birthday' | 'date'
)
RETURNS TABLE(
    id         INT,
    first_name VARCHAR,
    email      VARCHAR,
    birthday   DATE,
    group_name VARCHAR,
    phones     TEXT,
    created_at TIMESTAMP
) AS $$
DECLARE
    v_order TEXT;
BEGIN
    IF p_sort = 'birthday' THEN
        v_order := 'c.birthday ASC NULLS LAST';
    ELSIF p_sort = 'date' THEN
        v_order := 'c.created_at DESC';
    ELSE
        v_order := 'c.first_name ASC';
    END IF;

    RETURN QUERY EXECUTE format(
        'SELECT DISTINCT
            c.id,
            c.first_name,
            c.email,
            c.birthday,
            g.name,
            STRING_AGG(p.phone || %L || COALESCE(p.type, %L) || %L, %L),
            c.created_at
         FROM contacts c
         LEFT JOIN groups g ON g.id = c.group_id
         LEFT JOIN phones p ON p.contact_id = c.id
         GROUP BY c.id, c.first_name, c.email, c.birthday, g.name, c.created_at
         ORDER BY %s
         LIMIT %s OFFSET %s',
        ' (', '?', ')', ', ',
        v_order,
        p_limit,
        p_offset
    );
END;
$$ LANGUAGE plpgsql;



--  PROCEDURE: add_phone
--  Adds a new phone number to an existing contact

CREATE OR REPLACE PROCEDURE add_phone(
    p_contact_name VARCHAR,
    p_phone        VARCHAR,
    p_type         VARCHAR
)
LANGUAGE plpgsql AS $$
DECLARE
    v_id INT;
BEGIN
    SELECT id INTO v_id FROM contacts WHERE first_name = p_contact_name LIMIT 1;
    IF v_id IS NULL THEN
        RAISE EXCEPTION 'Contact "%" not found', p_contact_name;
    END IF;
    INSERT INTO phones (contact_id, phone, type) VALUES (v_id, p_phone, p_type);
END;
$$;



--  PROCEDURE: move_to_group
--  Moves a contact to a group; creates group if missing

CREATE OR REPLACE PROCEDURE move_to_group(
    p_contact_name VARCHAR,
    p_group_name   VARCHAR
)
LANGUAGE plpgsql AS $$
DECLARE
    v_contact_id INT;
    v_group_id   INT;
BEGIN
    SELECT id INTO v_contact_id FROM contacts WHERE first_name = p_contact_name LIMIT 1;
    IF v_contact_id IS NULL THEN
        RAISE EXCEPTION 'Contact "%" not found', p_contact_name;
    END IF;

    SELECT id INTO v_group_id FROM groups WHERE name = p_group_name;
    IF v_group_id IS NULL THEN
        INSERT INTO groups (name) VALUES (p_group_name) RETURNING id INTO v_group_id;
    END IF;

    UPDATE contacts SET group_id = v_group_id WHERE id = v_contact_id;
END;
$$;



--  PROCEDURE: upsert_contact
--  Inserts a new contact; if name exists, updates email/birthday

CREATE OR REPLACE PROCEDURE upsert_contact(
    p_name     VARCHAR,
    p_email    VARCHAR DEFAULT NULL,
    p_birthday DATE    DEFAULT NULL,
    p_group    VARCHAR DEFAULT 'Other'
)
LANGUAGE plpgsql AS $$
DECLARE
    v_group_id   INT;
    v_contact_id INT;
BEGIN
    SELECT id INTO v_group_id FROM groups WHERE name = p_group;
    IF v_group_id IS NULL THEN
        INSERT INTO groups (name) VALUES (p_group) RETURNING id INTO v_group_id;
    END IF;

    SELECT id INTO v_contact_id FROM contacts WHERE first_name = p_name LIMIT 1;
    IF v_contact_id IS NULL THEN
        INSERT INTO contacts (first_name, email, birthday, group_id)
        VALUES (p_name, p_email, p_birthday, v_group_id);
    ELSE
        UPDATE contacts
        SET email    = COALESCE(p_email,    email),
            birthday = COALESCE(p_birthday, birthday),
            group_id = v_group_id
        WHERE id = v_contact_id;
    END IF;
END;
$$;



--  PROCEDURE: delete_contact
--  Deletes by name or phone

CREATE OR REPLACE PROCEDURE delete_contact(
    p_name  VARCHAR DEFAULT NULL,
    p_phone VARCHAR DEFAULT NULL
)
LANGUAGE plpgsql AS $$
BEGIN
    IF p_name IS NOT NULL THEN
        DELETE FROM contacts WHERE first_name = p_name;
    ELSIF p_phone IS NOT NULL THEN
        DELETE FROM contacts
        WHERE id IN (SELECT contact_id FROM phones WHERE phone = p_phone);
    ELSE
        RAISE EXCEPTION 'Provide at least one of: name or phone';
    END IF;
END;
$$;
