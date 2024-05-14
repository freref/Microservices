CREATE DATABASE calendar;
\c calendar;

CREATE TABLE calendars (
    owner VARCHAR(100) PRIMARY KEY,
    shared_with VARCHAR(100)[] NOT NULL
);
