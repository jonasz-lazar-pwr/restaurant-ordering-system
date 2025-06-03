from fastapi import FastAPI
from api.routes import notify

app = FastAPI(title="Notification Service")

app.include_router(notify.router, prefix="/api", tags=["Notification"])

@app.get("/health")
def health():
    return {"status": "ok"}
