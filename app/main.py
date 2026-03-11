from fastapi import FastAPI
from app.models import MailgunPayload

app = FastAPI()


@app.post("/webhook")
async def receive_webhook(payload: MailgunPayload):
    return {"message": "Hello World"}
