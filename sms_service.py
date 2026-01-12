import os
import re
import time
import logging
from typing import Optional

try:
    import requests
except ImportError:  # pragma: no cover - runtime environment may not have requests installed
    requests = None

logger = logging.getLogger(__name__)

MOVESMS_USERNAME = os.environ.get("MOVESMS_USERNAME")
MOVESMS_APIKEY = os.environ.get("MOVESMS_APIKEY")
MOVESMS_SENDER_ID = os.environ.get("MOVESMS_SENDER_ID", "HELPDESK")
MOVESMS_BASE_URL = os.environ.get("MOVESMS_BASE_URL", "https://sms.movesms.co.ke/api/compose")


def _normalize_phone(phone: str) -> Optional[str]:
    """Normalize common phone inputs to Kenya international format: `2547XXXXXXXX`.

    Accepts inputs like `+2547...`, `07...`, `7...`, `2547...` and strips non-digits.
    Returns the normalized string or `None` if the number is invalid.
    """
    if not phone:
        return None
    s = re.sub(r"\D", "", str(phone))

    # +2547XXXXXXXX or 2547XXXXXXXX -> keep
    if s.startswith("254") and len(s) == 12:
        candidate = s
    # 07XXXXXXXX -> 2547XXXXXXXX
    elif s.startswith("0") and len(s) == 10:
        candidate = "254" + s[1:]
    # 7XXXXXXXX (9 digits) -> 2547XXXXXXXX
    elif len(s) == 9 and s.startswith("7"):
        candidate = "254" + s
    else:
        return None

    if re.match(r"^2547\d{8}$", candidate):
        return candidate
    return None


def send_sms(
    phone_number: str,
    message: str,
    sender: Optional[str] = None,
    timeout: int = 10,
    max_retries: int = 3,
    backoff_factor: float = 0.5,
) -> bool:
    """Send SMS via MoveSMS with optional retries/backoff.

    - `phone_number` may be in several common formats; it will be normalized.
    - `sender` overrides env `MOVESMS_SENDER_ID` for this message.
    - `max_retries` controls how many attempts (including the first).
    - `backoff_factor` controls exponential backoff: sleep = backoff_factor * (2 ** (attempt-1)).
    - Returns True on (likely) success, False otherwise.
    """
    normalized = _normalize_phone(phone_number)
    if not normalized:
        logger.warning("Invalid phone number format, will not send SMS: %s", phone_number)
        return False

    if not MOVESMS_USERNAME or not MOVESMS_APIKEY:
        logger.warning("MoveSMS credentials missing (MOVESMS_USERNAME/MOVESMS_APIKEY). SMS not sent.")
        return False

    payload = {
        "username": MOVESMS_USERNAME,
        "api_key": MOVESMS_APIKEY,
        "sender": sender or MOVESMS_SENDER_ID,
        "to": normalized,
        "message": message,
    }

    if requests is None:
        logger.warning("`requests` library is not installed; SMS cannot be sent.")
        return False

    # Mask API key in logs
    masked_payload = payload.copy()
    if masked_payload.get('api_key'):
        masked_payload['api_key'] = masked_payload['api_key'][:4] + '...'  # partial mask

    logger.debug("SMS Service Config: username=%s, sender=%s, base_url=%s", MOVESMS_USERNAME, sender or MOVESMS_SENDER_ID, MOVESMS_BASE_URL)
    logger.debug("Attempting to send SMS to %s. Payload: %s", normalized, masked_payload)

    attempt = 0
    while attempt < max_retries:
        attempt += 1
        try:
            resp = requests.post(MOVESMS_BASE_URL, data=payload, timeout=timeout)
            status = getattr(resp, "status_code", None)
            # Success on 2xx
            if status and 200 <= status < 300:
                logger.info("SMS sent to %s (attempt=%d status=%s). Response: %s", normalized, attempt, status, getattr(resp, "text", ""))
                logger.debug("Response headers: %s", getattr(resp, 'headers', {}))
                return True

            # Retry on server errors (5xx)
            if status and 500 <= status < 600 and attempt < max_retries:
                sleep_for = backoff_factor * (2 ** (attempt - 1))
                logger.warning("Server error sending SMS to %s (status=%s). Retrying in %.2fs (attempt %d/%d).", normalized, status, sleep_for, attempt, max_retries)
                if sleep_for:
                    time.sleep(sleep_for)
                continue

            # Non-retryable or last attempt
            logger.warning("SMS sending failed to %s (status=%s). Response: %s", normalized, status, getattr(resp, "text", ""))
            logger.debug("Response headers: %s", getattr(resp, 'headers', {}))
            return False

        except requests.exceptions.RequestException as exc:
            if attempt < max_retries:
                sleep_for = backoff_factor * (2 ** (attempt - 1))
                logger.warning("Network error sending SMS to %s: %s. Retrying in %.2fs (attempt %d/%d).", normalized, exc, sleep_for, attempt, max_retries)
                if sleep_for:
                    time.sleep(sleep_for)
                continue
            logger.exception("SMS request error for %s on final attempt: %s", normalized, exc)
            return False
