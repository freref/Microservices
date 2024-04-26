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

@app.get("/")
def read_root():
    return {"Hello": "World"}
