from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.responses import JSONResponse
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from fastapi import FastAPI, Body

app = FastAPI()

class Invitation(BaseModel):
    event_id: int
    invitee: str
    response: str = None

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
    
@app.post("/invitations/")
async def create_invitation(invitation: Invitation):
    conn = get_db_connection()
    if conn is None:
        return JSONResponse(content={"error": "Unable to connect to the database"}, status_code=500)
    
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO invitations (event_id, invitee, response) VALUES (%s, %s, %s) RETURNING id;",
            (invitation.event_id, invitation.invitee, invitation.response)
        )
        invitation_id = cur.fetchone()[0]
        conn.commit()
        return JSONResponse(content={"message": "Invitation created successfully", "invitation_id": invitation_id}, status_code=201)
    except psycopg2.Error as error:
        conn.rollback()
        return JSONResponse(content={"error": "Failed to create invitation", "detail": str(error)}, status_code=400)
    finally:
        cur.close()
        conn.close()