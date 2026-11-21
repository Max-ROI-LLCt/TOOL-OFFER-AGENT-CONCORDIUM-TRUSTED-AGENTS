"""Exact-mandate envelopes for the existing hosted identity; never wallet signing."""

import base64
from hashlib import sha256
from uuid import uuid4

from uagents_core.envelope import Envelope

from .concordium_json import canonical
from .concordium_mandate import MandateError, validate


SCHEMA = 'TOOL_OFFER_AGENT_MANDATE_ENVELOPE_V1'
TARGET = 'tool-offer:concordium:testnet:exact-mandate'
MODEL = 'model:' + sha256(SCHEMA.encode()).hexdigest()
FIELDS = {'version', 'sender', 'target', 'session', 'schema_digest', 'protocol_digest',
          'payload', 'expires', 'nonce', 'signature'}


def payload(mandate, action, *, expected_buyer, now):
    reference = validate(mandate, action, authenticated_buyer=expected_buyer, now=now)
    value = {'schema': SCHEMA, 'mandate_sha256': reference,
             'purpose': 'EXACT_ACTION_REQUEST_NOT_PAYMENT', 'native_transaction_signing': 'NOT_GRANTED'}
    return base64.b64encode(canonical(value).encode()).decode()


def unsigned_envelope(mandate, action, *, expected_buyer, now):
    return {'version': 1, 'sender': expected_buyer, 'target': TARGET, 'session': str(uuid4()),
            'schema_digest': MODEL, 'protocol_digest': None,
            'payload': payload(mandate, action, expected_buyer=expected_buyer, now=now),
            'expires': mandate['expires_at'], 'nonce': None, 'signature': None}


def verify_envelope(mandate, action, artifact, *, expected_buyer, now):
    try:
        if type(artifact) is not dict or set(artifact) != {'schema', 'envelope'} or artifact['schema'] != SCHEMA:
            raise ValueError()
        value = artifact['envelope']
        expected_payload = payload(mandate, action, expected_buyer=expected_buyer, now=now)
        if (type(value) is not dict or set(value) != FIELDS or len(canonical(value).encode()) > 8192
                or type(value['version']) is not int or value['version'] != 1
                or value['sender'] != expected_buyer or value['target'] != TARGET or value['schema_digest'] != MODEL
                or value['payload'] != expected_payload or type(value['expires']) is not int
                or value['expires'] != mandate['expires_at'] or value['protocol_digest'] is not None
                or value['nonce'] is not None or not isinstance(value['signature'], str)
                or not 1 <= len(value['signature']) <= 512):
            raise ValueError()
        envelope = Envelope.model_validate(value)
        if envelope.verify() is not True:
            raise ValueError()
    except Exception:
        raise MandateError('Hosted agent envelope verification failed') from None
    return True
