from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from fastapi.responses import JSONResponse
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from fastapi import FastAPI, Body
from typing import Optional

app = FastAPI()