
--  Drop existing tables (clean slate)

DROP TABLE IF EXISTS phones    CASCADE;
DROP TABLE IF EXISTS contacts  CASCADE;
DROP TABLE IF EXISTS groups    CASCADE;


--  Groups / categories

CREATE TABLE groups (
    id   SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL
);

INSERT INTO groups (name) VALUES ('Family'), ('Work'), ('Friend'), ('Other');


--  Contacts

CREATE TABLE contacts (
    id         SERIAL PRIMARY KEY,
    first_name VARCHAR(100) NOT NULL,
    email      VARCHAR(100),
    birthday   DATE,
    group_id   INTEGER REFERENCES groups(id),
    created_at TIMESTAMP DEFAULT NOW()
);


--  Phones  (1-to-many)

CREATE TABLE phones (
    id         SERIAL PRIMARY KEY,
    contact_id INTEGER REFERENCES contacts(id) ON DELETE CASCADE,
    phone      VARCHAR(20) NOT NULL,
    type       VARCHAR(10) CHECK (type IN ('home', 'work', 'mobile'))
);
