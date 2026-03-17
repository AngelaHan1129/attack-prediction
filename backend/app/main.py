from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database.session import engine, Base
from app.routers import auth, users
from app.models import user

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Attack Prediction API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(users.router)

@app.get("/")
def root():
    return {"message": "FastAPI 架構就緒！"}
