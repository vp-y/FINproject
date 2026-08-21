from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api import portfolio
from api import market
from api import risk
from api import rag
from api import data_pipeline
from api import agents
from api import websocket


app = FastAPI(
    title="Aegis Platform API",
    version="1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(
    portfolio.router
)
app.include_router(
    market.router
)
app.include_router(
    risk.router
)
app.include_router(
    rag.router
)
app.include_router(
    data_pipeline.router
)
app.include_router(
    agents.router
)
app.include_router(
    websocket.router
)


@app.get("/")
def home():
    return {
        "message": "Aegis Platform Backend Running"
    }