# main.py
from fastapi import FastAPI
from src.routers import people

app = FastAPI(
    title="Person Management API",
    description="RESTful API for managing person records with Mayo Clinic integration",
    version="1.0.0"
)

# Include routers
app.include_router(people.router)

@app.get("/")
def read_root():
    return {"Hello": "World"}
