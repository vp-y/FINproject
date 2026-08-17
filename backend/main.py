from fastapi import FastAPI

app = FastAPI(
    title="finproject Platform API",
    version="1.0"
)


@app.get("/")
def home():
    return {
        "message": "finproject Platform Backend Running"
    }