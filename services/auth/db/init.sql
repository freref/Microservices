-- Create the 'users' database
CREATE DATABASE users;

-- Connect to the 'users' database
\c users;

-- Create the 'users' table
CREATE TABLE users (
  id SERIAL PRIMARY KEY,
  username VARCHAR(50) NOT NULL UNIQUE,
  password VARCHAR(255) NOT NULL
);
