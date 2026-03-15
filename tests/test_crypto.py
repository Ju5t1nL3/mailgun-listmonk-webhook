import hashlib
import hmac
import time

from app.utils.config import settings
from app.utils.crypto import verify_mailgun_signature


def test_verify_mailgun_signature_valid():
    timestamp = str(int(time.time()))
    token = "test_token_123"

    valid_signature = hmac.new(
        key=settings.MAILGUN_SIGNING_KEY.encode(),
        msg=(timestamp + token).encode(),
        digestmod=hashlib.sha256,
    ).hexdigest()

    assert verify_mailgun_signature(timestamp, token, valid_signature) is True


def test_verify_mailgun_signature_invalid():
    timestamp = str(int(time.time()))
    token = "test_token_123"

    invalid_signature = "this_signature_is_invalid"

    assert verify_mailgun_signature(timestamp, token, invalid_signature) is False
