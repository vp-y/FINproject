from fastapi import FastAPI

app = FastAPI(
    title="Aegis Platform API",
    version="1.0"
)


@app.get("/")
def home():
    return {
        "message": "Aegis Platform Backend Running"
    }