from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.responses import JSONResponse
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from fastapi import FastAPI, Body

app = FastAPI()

class Event(BaseModel):
    date: str
    organizer: str
    title: str
    description: str = None
    is_public: bool

class EventRequest(BaseModel):
    is_public: bool

def get_db_connection():
    try:
        return psycopg2.connect(
            dbname='events',
            user=os.environ['POSTGRES_USER'],
            password=os.environ['POSTGRES_PASSWORD'],
            host=os.environ['DATABASE_HOST'],
            port='5432'
        )
    except psycopg2.Error as e:
        print("Unable to connect to the database")
        print(e)
        return None

@app.post("/events/")
async def create_event(event: Event):
    conn = get_db_connection()
    if conn is None:
        return JSONResponse(content={"error": "Unable to connect to the database"}, status_code=500)
    
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO events (date, organizer, title, description, is_public) VALUES (%s, %s, %s, %s, %s) RETURNING id;",
            (event.date, event.organizer, event.title, event.description, event.is_public)
        )
        event_id = cur.fetchone()[0]
        conn.commit()
        return JSONResponse(content={"message": "Event created successfully", "event_id": event_id}, status_code=201)
    except psycopg2.Error as error:
        conn.rollback()
        return JSONResponse(content={"error": "Failed to create event", "detail": str(error)}, status_code=400)
    finally:
        cur.close()
        conn.close()

@app.get("/events/")
async def get_events(event_request: EventRequest):
    conn = get_db_connection()
    if conn is None:
        return JSONResponse(content={"error": "Unable to connect to the database"}, status_code=500)
    
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cur.execute("SELECT id, TO_CHAR(date, 'YYYY-MM-DD') as date, organizer, title, description, is_public FROM events WHERE is_public = %s", (event_request.is_public,))
        events = cur.fetchall()
        return JSONResponse(content={"events": events}, status_code=200)
    except psycopg2.Error as error:
        return JSONResponse(content={"error": "Failed to fetch events", "detail": str(error)}, status_code=400)
    finally:
        cur.close()
        conn.close()