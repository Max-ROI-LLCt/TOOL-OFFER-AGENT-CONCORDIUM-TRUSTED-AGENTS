from copy import deepcopy
from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from uagents_core.identity import Identity
from tool_offer_agent.commerce import digest
from tool_offer_agent.storage import StateStore
from tool_offer_agent.concordium_mandate import MandateError
from tool_offer_agent.concordium_mandate_auth import (
    signing_digest, authenticate, reserve_signed,
)
from tests.test_concordium_mandate import MandateTests as Fixtures

class MandateSignatureTests(TestCase):
    def setUp(self):
        from tests.test_concordium_mandate import MandateTests as Fixtures
        fixture = Fixtures()
        fixture.setUp()
        self.buyer = Identity.generate()
        self.other = Identity.generate()
        self.action = dict(fixture.action, buyer=self.buyer.address)
        self.mandate = dict(fixture.mandate, buyer=self.buyer.address)
        self.signature = self.buyer.sign_digest(signing_digest(
            self.mandate, self.action, expected_buyer=self.buyer.address, now=150
        ))

    def auth(self, mandate=None, action=None, signature=None, buyer=None, now=150):
        return authenticate(
            self.mandate if mandate is None else mandate,
            self.action if action is None else action,
            self.signature if signature is None else signature,
            expected_buyer=self.buyer.address if buyer is None else buyer,
            now=now,
        )

    def test_valid_signature_is_not_wallet_or_company_authority(self):
        result = self.auth()
        self.assertTrue(result["agent_signature_verified"])
        self.assertFalse(result["dispatch_authorized"])
        self.assertEqual(result["wallet_authority"], "NOT_ESTABLISHED")
        self.assertEqual(result["company_identity"], "NOT_ESTABLISHED")

    def test_wrong_signer_and_malformed_signature_denied(self):
        wrong = self.other.sign_digest(signing_digest(
            self.mandate, self.action, expected_buyer=self.buyer.address, now=150
        ))
        for signature in (wrong, "invalid", "", "x"*513):
            with self.assertRaises(MandateError):
                self.auth(signature=signature)

    def test_changed_mandate_with_matching_changed_action_denied(self):
        for field, value in (
            ("amount_atomic", "2000000"), ("recipient", "other-recipient"),
            ("offer_hash", "f"*64), ("acceptance_hash", "f"*64),
        ):
            mandate, action = deepcopy(self.mandate), dict(self.action)
            mandate[field] = action[field] = value
            with self.assertRaises(MandateError):
                self.auth(mandate, action)

    def test_wrong_buyer_expiry_and_nonce_change_denied(self):
        with self.assertRaises(MandateError):
            self.auth(buyer=self.other.address)
        with self.assertRaises(MandateError):
            self.auth(now=200)
        with self.assertRaises(MandateError):
            self.auth(mandate=dict(self.mandate, nonce="f"*64))

    def test_plain_hash_signature_cannot_replace_mandate_signature(self):
        unrelated = self.buyer.sign_digest(bytes.fromhex(digest(self.mandate)))
        with self.assertRaises(MandateError):
            self.auth(signature=unrelated)

    def test_invalid_signature_does_not_consume_nonce_and_restart_blocks_reuse(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "state.sqlite3"
            with self.assertRaises(MandateError):
                reserve_signed(StateStore(path), self.mandate, self.action,
                               "invalid", expected_buyer=self.buyer.address, now=150)
            result = reserve_signed(
                StateStore(path), self.mandate, self.action, self.signature,
                expected_buyer=self.buyer.address, now=150,
            )
            self.assertEqual(result["reservation"]["payment"], "NOT_SUBMITTED")
            with self.assertRaises(MandateError):
                reserve_signed(StateStore(path), self.mandate, self.action,
                               self.signature, expected_buyer=self.buyer.address,
                               now=151)

# Fixture class is imported only for sample construction, not test discovery.
del Fixtures
