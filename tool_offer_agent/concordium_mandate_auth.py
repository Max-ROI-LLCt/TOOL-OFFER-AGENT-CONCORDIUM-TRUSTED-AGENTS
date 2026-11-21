"""Agent-signed mandate verification; no wallet delegation or dispatch."""
from copy import deepcopy
from hashlib import sha256
from uagents_core.identity import Identity
from .concordium_mandate import MandateError, validate, reserve
from .concordium_report_parties import AGENT

PURPOSE = b"TOOL_OFFER_AGENT_MANDATE_SIGNATURE_V1\x00"

def sign_existing_agent(identity, mandate, action, *, now):
    if identity.address != AGENT:
        raise MandateError('WRONG_EXISTING_AGENT')
    signature = identity.sign_digest(signing_digest(mandate, action, expected_buyer=AGENT, now=now))
    authenticate(mandate, action, signature, expected_buyer=AGENT, now=now)
    return signature

def signing_digest(mandate, action, *, expected_buyer, now):
    reference = validate(
        mandate, action, authenticated_buyer=expected_buyer, now=now
    )
    return sha256(PURPOSE + bytes.fromhex(reference)).digest()

def authenticate(mandate, action, signature, *, expected_buyer, now):
    """expected_buyer must come from trusted transaction context, not envelope."""
    message = signing_digest(
        mandate, action, expected_buyer=expected_buyer, now=now
    )
    if type(signature) is dict:
        from .concordium_agent_envelope import verify_envelope
        verified = verify_envelope(mandate, action, signature, expected_buyer=expected_buyer, now=now)
    elif isinstance(signature, str) and 1 <= len(signature) <= 512:
        try:
            verified = Identity.verify_digest(expected_buyer, message, signature)
        except Exception:
            raise MandateError("Mandate signature verification failed") from None
    else:
        raise MandateError("Invalid mandate signature")
    if verified is not True:
        raise MandateError("Mandate signature verification failed")
    return {
        "agent_signature_verified": True,
        "signer": expected_buyer,
        "mandate_hash": validate(
            mandate, action, authenticated_buyer=expected_buyer, now=now
        ),
        "wallet_authority": "NOT_ESTABLISHED",
        "company_identity": "NOT_ESTABLISHED",
        "dispatch_authorized": False,
    }

def reserve_signed(store, mandate, action, signature, *, expected_buyer, now):
    # Verify and reserve the same detached snapshot.
    mandate, action = deepcopy(mandate), deepcopy(action)
    authentication = authenticate(
        mandate, action, signature, expected_buyer=expected_buyer, now=now
    )
    reservation = reserve(
        store, mandate, action, authenticated_buyer=expected_buyer, now=now
    )
    return {"authentication": authentication, "reservation": reservation}
