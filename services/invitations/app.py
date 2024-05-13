from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from fastapi.responses import JSONResponse
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import Optional

app = FastAPI()


class Invitation(BaseModel):
    event_id: int
    invitee: str
    status: str = None


class InvitationRequest(BaseModel):
    invitee: Optional[str] = None
    status: Optional[str] = None
    event: Optional[int] = None

    class Config:
        schema_extra = {
            "example": {
                "invitee": "user1",
                "status": "Pending",
                "event": 1,
            }
        }


def get_db_connection():
    try:
        return psycopg2.connect(
            dbname="invitations",
            user=os.environ["POSTGRES_USER"],
            password=os.environ["POSTGRES_PASSWORD"],
            host=os.environ["DATABASE_HOST"],
            port="5432",
        )
    except psycopg2.Error as e:
        print("Unable to connect to the database")
        print(e)
        return None


# Create an invitation
@app.post("/invitations/")
async def create_invitation(invitation: Invitation):
    conn = get_db_connection()
    if conn is None:
        return JSONResponse(
            content={"error": "Unable to connect to the database"}, status_code=500
        )

    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO invitations (event_id, invitee, status) VALUES (%s, %s, %s)",
            (invitation.event_id, invitation.invitee, invitation.status),
        )
        conn.commit()
        return JSONResponse(
            content={
                "message": "Invitation created successfully",
            },
            status_code=201,
        )
    except psycopg2.Error as error:
        conn.rollback()
        return JSONResponse(
            content={"error": "Failed to create invitation", "detail": str(error)},
            status_code=400,
        )
    finally:
        cur.close()
        conn.close()


# Get invitations based on the query parameters
@app.get("/invitations/")
async def get_invitations(
    invitee: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    event: Optional[int] = Query(None),
):
    conn = get_db_connection()
    if conn is None:
        return JSONResponse(
            content={"error": "Unable to connect to the database"}, status_code=500
        )

    query = "SELECT event_id, invitee, status FROM invitations"
    params = []
    conditions = []

    if invitee is not None:
        conditions.append("invitee = %s")
        params.append(invitee)

    if status is not None:
        conditions.append("status = %s")
        params.append(status)

    if event is not None:
        conditions.append("event_id = %s")
        params.append(event)

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cur.execute(query, tuple(params))
        invitations = cur.fetchall()
        return JSONResponse(content={"invitations": invitations}, status_code=200)
    except psycopg2.Error as error:
        conn.rollback()
        return JSONResponse(
            content={"error": "Failed to fetch invitations", "detail": str(error)},
            status_code=400,
        )
    finally:
        cur.close()
        conn.close()


# Update invitation status of an invitee for a specific event
@app.patch("/invitations/{event_id}/{invitee}")
async def update_invitation_status(event_id: int, invitee: str, status: str):
    conn = get_db_connection()
    if conn is None:
        return JSONResponse(
            content={"error": "Unable to connect to the database"}, status_code=500
        )

    cur = conn.cursor()
    try:
        cur.execute(
            "UPDATE invitations SET status = %s WHERE event_id = %s AND invitee = %s;",
            (status, event_id, invitee),
        )
        conn.commit()
        return JSONResponse(
            content={"message": "Invitation updated successfully"}, status_code=200
        )
    except psycopg2.Error as error:
        conn.rollback()
        return JSONResponse(
            content={"error": "Failed to update invitation", "detail": str(error)},
            status_code=400,
        )
    finally:
        cur.close()
        conn.close()
