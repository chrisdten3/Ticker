from fastapi import FastAPI
from pipeline import run_pipeline


app = FastAPI()
@app.get("/get_labels")
def get_labels():
    return run_pipeline()




