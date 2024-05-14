from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from fastapi.responses import JSONResponse
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from fastapi import FastAPI, Body
from typing import Optional, List

app = FastAPI()

class SharedWithUpdate(BaseModel):
    owner: str
    shared_with: str

def get_db_connection():
    try:
        return psycopg2.connect(
            dbname="calendars",
            user=os.environ["POSTGRES_USER"],
            password=os.environ["POSTGRES_PASSWORD"],
            host=os.environ["DATABASE_HOST"],
            port="5432",
        )
    except psycopg2.Error as e:
        print("Unable to connect to the database")
        print(e)
        return None

@app.put("/share")
async def share_calendar(shared_with_update: SharedWithUpdate):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")

    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("SELECT * FROM calendars WHERE owner = %s", (shared_with_update.owner,))
            owner_record = cursor.fetchone()

            if owner_record:
                updated_shared_with = owner_record['shared_with'] + [shared_with_update.shared_with]
                cursor.execute(
                    "UPDATE calendars SET shared_with = %s WHERE owner = %s",
                    (updated_shared_with, shared_with_update.owner)
                )
            else:
                cursor.execute(
                    "INSERT INTO calendars (owner, shared_with) VALUES (%s, %s)",
                    (shared_with_update.owner, [shared_with_update.shared_with])
                )

            conn.commit()
            return JSONResponse(content={"message": "Calendar shared successfully"}, status_code=200)

    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail="An error occurred while sharing the calendar")
    finally:
        conn.close()

@app.get("/calendars")
async def get_calendars(owner: str):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")

    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("SELECT * FROM calendars WHERE owner = %s", (owner,))
            record = cursor.fetchone()
            if record:
                return JSONResponse(content=record, status_code=200)
            else:
                return JSONResponse(content={"message": "Calendar not found"}, status_code=404)
    except Exception as e:
        raise HTTPException(status_code=500, detail="An error occurred while getting the calendar")
    finally:
        conn.close()