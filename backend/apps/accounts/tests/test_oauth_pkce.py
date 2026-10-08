"""Synthetic keys and RFC example only; no Google calls."""
import json
from uuid import uuid4

from cryptography.fernet import Fernet
from django.test import SimpleTestCase, override_settings

from apps.accounts.oauth_pkce import (
    InvalidOAuthPKCE, OAuthPKCEConfigurationError, code_challenge,
    decrypt_verifier, encrypt_verifier, generate_verifier,
)


class OAuthPKCETests(SimpleTestCase):
    def setUp(self):
        self.key = Fernet.generate_key().decode("ascii")
        configured = override_settings(GMAIL_CREDENTIAL_ENCRYPTION_KEY=self.key)
        configured.enable()
        self.addCleanup(configured.disable)
        self.id = uuid4()
        self.digest = "a" * 64
        self.verifier = generate_verifier()

    def test_rfc7636_s256_example(self):
        self.assertEqual(code_challenge("dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk"),
                         "E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM")

    def test_random_format_and_roundtrip(self):
        other = generate_verifier()
        self.assertNotEqual(self.verifier, other)
        self.assertRegex(self.verifier, r"\A[A-Za-z0-9_-]{43}\Z")
        self.assertEqual(len(code_challenge(self.verifier)), 43)
        encrypted = encrypt_verifier(self.verifier, self.id, self.digest)
        self.assertLessEqual(len(encrypted), 1024)
        self.assertNotIn(self.verifier, encrypted)
        self.assertEqual(decrypt_verifier(encrypted, self.id, self.digest), self.verifier)

    def test_verifier_validation(self):
        for value in [None, {}, 1, "a" * 42, "a" * 129, "a" * 42 + "!", "é" * 43, "a" * 43 + "\n"]:
            with self.subTest(kind=type(value).__name__), self.assertRaises(InvalidOAuthPKCE):
                code_challenge(value)
        for value in ["a" * 43, "~" * 128]:
            self.assertEqual(len(code_challenge(value)), 43)

    def test_context_binding_and_types(self):
        encrypted = encrypt_verifier(self.verifier, self.id, self.digest)
        for identity, digest in [(uuid4(), self.digest), (self.id, "b" * 64),
                                 (str(self.id), self.digest), (self.id, "A" * 64), (self.id, {})]:
            with self.assertRaises(InvalidOAuthPKCE):
                decrypt_verifier(encrypted, identity, digest)

    def test_ciphertext_bounds_corruption_and_wrong_key(self):
        encrypted = encrypt_verifier(self.verifier, self.id, self.digest)
        for value in [None, {}, 1, "", "x" * 1025, "é", encrypted[:-2] + "xx"]:
            with self.assertRaises(InvalidOAuthPKCE):
                decrypt_verifier(value, self.id, self.digest)
        with override_settings(GMAIL_CREDENTIAL_ENCRYPTION_KEY=Fernet.generate_key().decode("ascii")):
            with self.assertRaises(InvalidOAuthPKCE):
                decrypt_verifier(encrypted, self.id, self.digest)

    def test_missing_or_malformed_configuration(self):
        for key in [None, "", "bad", 1, {}, "é" * 44, "!" * 44, "A" * 44]:
            with override_settings(GMAIL_CREDENTIAL_ENCRYPTION_KEY=key):
                with self.assertRaises(OAuthPKCEConfigurationError):
                    encrypt_verifier(self.verifier, self.id, self.digest)

    def test_strict_envelope_validation(self):
        valid = dict(schema_version=1, attempt_id=str(self.id), state_digest=self.digest, verifier=self.verifier)
        records = [[], None, {}, {**valid, "extra": 1}, {**valid, "schema_version": True},
                   {**valid, "schema_version": 2}, {**valid, "attempt_id": str(self.id).upper()},
                   {**valid, "state_digest": []}, {**valid, "verifier": "\ud800"},
                   {key: value for key, value in valid.items() if key != "verifier"}]
        payloads = [json.dumps(record).encode() for record in records]
        payloads += [b"{", b"\xff", b" " * 513, b"[" * 250 + b"]" * 250,
                     (json.dumps(valid)[:-1] + ',"schema_version":1}').encode()]
        for payload in payloads:
            encrypted = Fernet(self.key.encode()).encrypt(payload).decode()
            with self.subTest(size=len(payload)), self.assertRaises(InvalidOAuthPKCE) as caught:
                decrypt_verifier(encrypted, self.id, self.digest)
            self.assertNotIn(self.verifier, str(caught.exception))
