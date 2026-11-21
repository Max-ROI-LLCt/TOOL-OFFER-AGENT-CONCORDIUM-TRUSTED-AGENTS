import tempfile
from copy import deepcopy
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest import TestCase
from tool_offer_agent.storage import StateStore
from tool_offer_agent.concordium_mandate import (
    FIELDS, SCHEMA, MandateError, validate, reserve,
)

class MandateTests(TestCase):
    def setUp(self):
        self.action = dict(
            buyer="synthetic-buyer", seller="synthetic-supplier",
            operation="synthetic-service",
            offer_hash="a"*64, source_hash="b"*64,
            input_hash="c"*64, acceptance_hash="d"*64,
            network="concordium:testnet", asset="CCD",
            recipient="synthetic-recipient", amount_atomic="1000000",
        )
        self.mandate = dict(
            self.action, schema=SCHEMA, nonce="e"*64,
            issued_at=100, expires_at=200,
        )

    def check(self, mandate=None, action=None, now=150, buyer="synthetic-buyer"):
        return validate(
            self.mandate if mandate is None else mandate,
            self.action if action is None else action,
            authenticated_buyer=buyer, now=now,
        )

    def test_exact_binding(self):
        self.assertEqual(len(self.check()), 64)

    def test_every_changed_action_field_is_denied(self):
        for field in FIELDS:
            with self.subTest(field=field):
                action = dict(self.action)
                action[field] += "-changed"
                with self.assertRaises(MandateError):
                    self.check(action=action)

    def test_expiry_future_and_wrong_buyer(self):
        for now in (99, 200, 201):
            with self.assertRaises(MandateError):
                self.check(now=now)
        with self.assertRaises(MandateError):
            self.check(buyer="other")

    def test_invalid_scope_and_amount_even_when_action_matches(self):
        for field, value in (
            ("network", "concordium:mainnet"),
            ("asset", "USDC"), ("amount_atomic", "1.5"),
            ("amount_atomic", "0"), ("amount_atomic", str(2**64)),
            ("offer_hash", "not-a-digest"),
        ):
            mandate, action = deepcopy(self.mandate), dict(self.action)
            mandate[field] = action[field] = value
            with self.assertRaises(MandateError):
                self.check(mandate, action)

    def test_missing_extra_and_boolean_time(self):
        for mandate in (
            {k:v for k,v in self.mandate.items() if k != "nonce"},
            dict(self.mandate, extra="unapproved"),
            dict(self.mandate, issued_at=True),
        ):
            with self.assertRaises(MandateError):
                self.check(mandate)

    def test_store_without_atomic_reservation_denied(self):
        with self.assertRaises(MandateError):
            reserve(object(), self.mandate, self.action,
                    authenticated_buyer="synthetic-buyer", now=150)

    def test_concurrent_and_restart_reservation_no_replay(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "state.sqlite3"
            StateStore(path)
            def attempt(_):
                try:
                    reserve(StateStore(path), self.mandate, self.action,
                            authenticated_buyer="synthetic-buyer", now=150)
                    return True
                except MandateError:
                    return False
            with ThreadPoolExecutor(max_workers=2) as pool:
                self.assertEqual(sum(pool.map(attempt, range(2))), 1)
            self.assertFalse(attempt(3))
            changed = dict(self.mandate, amount_atomic="2000000")
            action = dict(self.action, amount_atomic="2000000")
            with self.assertRaises(MandateError):
                reserve(StateStore(path), changed, action,
                        authenticated_buyer="synthetic-buyer", now=151)
