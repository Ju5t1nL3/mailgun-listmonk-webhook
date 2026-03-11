import hashlib
import hmac

from app.utils.config import settings


def verify_mailgun_signature(timestamp: str, token: str, signature: str) -> bool:
    hmac_digest = hmac.new(
        key=settings.MAILGUN_SIGNING_KEY.encode(),
        msg=(timestamp + token).encode(),
        digestmod=hashlib.sha256,
    ).hexdigest()

    return hmac.compare_digest(str(signature), str(hmac_digest))
