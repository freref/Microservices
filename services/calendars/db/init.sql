CREATE DATABASE calendars;
\c calendars;

CREATE TABLE calendars (
    owner VARCHAR(100) PRIMARY KEY,
    shared_with VARCHAR(100)[] NOT NULL
);
