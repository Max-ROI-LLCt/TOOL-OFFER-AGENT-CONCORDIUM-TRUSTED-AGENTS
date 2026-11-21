"""Offline mandate binding and durable reservation; no signing or dispatch."""
import re
from .concordium_json import MAX_SAFE_INTEGER, canonical, digest

class MandateError(ValueError):
    pass

FIELDS = (
    "buyer", "seller", "operation", "offer_hash", "source_hash",
    "input_hash", "acceptance_hash", "network", "asset", "recipient",
    "amount_atomic",
)
HASHES = ("offer_hash", "source_hash", "input_hash", "acceptance_hash")
SCHEMA = "TOOL_OFFER_CONCORDIUM_MANDATE_V1"

def validate(mandate, action, *, authenticated_buyer, now):
    """Caller must independently authenticate buyer; this function cannot."""
    if type(now) is not int or not 0 <= now <= MAX_SAFE_INTEGER:
        raise MandateError("Explicit integer observation time required")
    if not isinstance(mandate, dict) or not isinstance(action, dict):
        raise MandateError("Mandate and action objects required")
    try:
        canonical([mandate, action])
    except (ValueError, TypeError):
        raise MandateError("Invalid mandate serialization") from None
    expected = {"schema", "nonce", "issued_at", "expires_at", *FIELDS}
    if set(mandate) != expected or set(action) != set(FIELDS):
        raise MandateError("Unexpected or missing fields")
    if mandate["schema"] != SCHEMA:
        raise MandateError("Unsupported schema")
    if not isinstance(authenticated_buyer, str) or not authenticated_buyer:
        raise MandateError("Independently authenticated buyer required")
    if mandate["buyer"] != authenticated_buyer:
        raise MandateError("Buyer identity mismatch")
    for field in FIELDS:
        value = mandate[field]
        if not isinstance(value, str) or not value or len(value) > 512:
            raise MandateError("Invalid field: " + field)
        if value != action[field]:
            raise MandateError("Action mismatch: " + field)
    for field in HASHES:
        if not re.fullmatch(r"[0-9a-f]{64}", mandate[field]):
            raise MandateError("Invalid digest: " + field)
    if mandate["network"] != "concordium:testnet" or mandate["asset"] != "CCD":
        raise MandateError("Only explicit Concordium Testnet CCD scope supported")
    if not re.fullmatch(r"[1-9][0-9]{0,19}", mandate["amount_atomic"]):
        raise MandateError("Positive integer microCCD amount required")
    if int(mandate["amount_atomic"]) >= 2**64:
        raise MandateError("Amount exceeds uint64")
    if not isinstance(mandate["nonce"], str) or not re.fullmatch(
        r"[0-9a-f]{64}", mandate["nonce"]
    ):
        raise MandateError("Explicit 32-byte nonce required")
    issued, expires = mandate["issued_at"], mandate["expires_at"]
    if type(issued) is not int or type(expires) is not int:
        raise MandateError("Integer timestamps required")
    if not 0 <= issued <= now < expires:
        raise MandateError("Mandate is not currently valid")
    return digest(mandate)

def reserve(store, mandate, action, *, authenticated_buyer, now):
    """Reserve once; ambiguity stays reserved. No external action is performed."""
    reference = validate(
        mandate, action, authenticated_buyer=authenticated_buyer, now=now
    )
    if not callable(getattr(store, "compare_and_swap", None)):
        raise MandateError("Atomic durable store required; no save fallback")
    key = reservation_key(store, authenticated_buyer, mandate["nonce"])
    record = {
        "schema": "TOOL_OFFER_MANDATE_RESERVATION_V1",
        "mandate_hash": reference,
        "action_hash": digest(action),
        "buyer": authenticated_buyer,
        "nonce": mandate["nonce"],
        "reserved_at": now,
        "state": "RESERVED_NOT_DISPATCHED",
        "payment": "NOT_SUBMITTED",
        "authority_verification": "REQUIRED_AT_INTEGRATION",
        "fahce_enforcement": "NOT_ESTABLISHED",
    }
    if not store.compare_and_swap(key, None, record):
        raise MandateError("Nonce already reserved; reconcile without replay")
    return record


def reservation_key(store, buyer, nonce):
    return store.key("tool-offer-concordium-mandate-v1", digest([buyer, nonce]))
