from fastapi import FastAPI, HTTPException

from app.schemas import MailgunPayload
from app.services import forward_bounce
from app.utils.crypto import verify_mailgun_signature

app = FastAPI()


@app.post("/webhook")
async def receive_webhook(payload: MailgunPayload) -> dict[str, str]:
    payload_signature = payload.signature
    if not verify_mailgun_signature(
        payload_signature.timestamp,
        payload_signature.token,
        payload_signature.signature,
    ):
        raise HTTPException(status_code=401, detail="Invalid Mailgun Signature")

    return await forward_bounce(payload.event_data)
