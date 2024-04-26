-- Create the 'auth' database
CREATE DATABASE auth;

-- Connect to the 'auth' database
\c auth;

-- Create the 'auth' table
CREATE TABLE auth (
  id SERIAL PRIMARY KEY,
  username VARCHAR(50) NOT NULL UNIQUE,
  password VARCHAR(255) NOT NULL
);
