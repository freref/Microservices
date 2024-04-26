-- Create the 'events' database
CREATE DATABASE events;

-- Connect to the 'events' database
\c events;

-- Create the 'events' table
CREATE TABLE events (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    organizer VARCHAR(100) NOT NULL,
    title VARCHAR(100) NOT NULL,
    description TEXT,
    is_public BOOLEAN NOT NULL
);
