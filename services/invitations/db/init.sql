CREATE DATABASE invitations;
\c invitations;

CREATE TABLE invitations (
    id SERIAL PRIMARY KEY,
    event_id INT NOT NULL,
    invitee VARCHAR(100) NOT NULL,
    status VARCHAR(20) NOT NULL
);