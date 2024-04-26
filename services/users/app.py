from fastapi import FastAPI, HTTPException
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from fastapi.responses import JSONResponse
from fastapi import FastAPI, Body

app = FastAPI()

def get_db_connection():
    try:
        return psycopg2.connect(
            dbname='users',
            user=os.environ['POSTGRES_USER'],
            password=os.environ['POSTGRES_PASSWORD'],
            host=os.environ['DATABASE_HOST'],
            port='5432'  # Standard PostgreSQL port
        )
    except psycopg2.Error as e:
        print("Unable to connect to the database")
        print(e)
        return None

@app.post("/register/")
def register(username: str = Body(...), password: str = Body(...)):
    conn = get_db_connection()
    if conn is None:
        return JSONResponse(content={"error": "Unable to connect to the database"}, status_code=500)
    
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cur.execute("INSERT INTO users (username, password) VALUES (%s, %s) RETURNING id;", (username, password))
        user_id = cur.fetchone()['id']
        conn.commit()
    except psycopg2.Error as e:
        conn.rollback()
        return JSONResponse(content={"error": "Failed to register user", "detail": str(e)}, status_code=400)
    finally:
        cur.close()
        conn.close()

    return JSONResponse(content={"message": "User registered successfully", "user_id": user_id}, status_code=200)

@app.post("/login/")
def login(username: str = Body(...), password: str = Body(...)):
    conn = get_db_connection()
    if conn is None:
        return JSONResponse(content={"error": "Unable to connect to the database"}, status_code=500)
    
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cur.execute("SELECT id FROM users WHERE username = %s AND password = %s;", (username, password))
        user = cur.fetchone()
        if not user:
            return JSONResponse(content={"error": "Invalid username or password"}, status_code=401)
    finally:
        cur.close()
        conn.close()

    return JSONResponse(content={"message": "Login successful", "user_id": user['id']}, status_code=200)

