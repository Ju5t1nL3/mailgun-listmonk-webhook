import hashlib
import hmac
import time

from app.utils.config import settings


def verify_mailgun_signature(timestamp: str, token: str, signature: str) -> bool:
    """
    Validates the mailgun signature to ensure request authenticity.

    Checks the HMAC-SHA256 digest against the provided signature to guarantee
    that the original request came from Mailgun. It also rejects payloads older
    than 15 minutes.
    """
    try:
        if abs(time.time() - int(timestamp)) > 900:
            return False
    except ValueError:
        return False

    hmac_digest = hmac.new(
        key=settings.MAILGUN_SIGNING_KEY.encode(),
        msg=(timestamp + token).encode(),
        digestmod=hashlib.sha256,
    ).hexdigest()

    return hmac.compare_digest(str(signature), str(hmac_digest))
