from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "World"}


