import hashlib
import hmac
import os

mailgun_key = os.getenv("mailgun_signing_key")


def verify_mailgun_signature(timestamp: str, token: str, signature: str) -> bool:
    hmac_digest = hmac.new(
        key=mailgun_key, msg=(timestamp + token).encode(), digestmod=hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(str(signature), str(hmac_digest))
