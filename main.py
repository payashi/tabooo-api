import os

from fastapi import FastAPI

app = FastAPI()


@app.get("/")
def hello_world():
    return {'message': f'hogeee'}