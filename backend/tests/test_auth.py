"""Tests for the login check (app/auth.py).

Tokens are minted here with a throwaway RSA key, and the key fetcher is told
about that key instead of asking Cognito. So every check runs offline: the
signature, the expiry, the issuer, the token kind, and the app client.
"""

import time
from typing import Any

import jwt
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi import HTTPException
from jwt import PyJWK, PyJWKClient

from app import auth
from app.auth import get_user, verify_access_token
from tests.conftest import TEST_SETTINGS

KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)
OTHER_KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)
PUBLIC_JWK = PyJWK(jwt.algorithms.RSAAlgorithm.to_jwk(KEY.public_key(), as_dict=True), "RS256")


def pem(key: rsa.RSAPrivateKey) -> bytes:
    return key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    )


def token(key: rsa.RSAPrivateKey = KEY, **changes: Any) -> str:
    """An access token like Cognito's, with any claim overridden."""
    claims: dict[str, Any] = {
        "sub": "user-a",
        "iss": TEST_SETTINGS.cognito_issuer,
        "client_id": TEST_SETTINGS.cognito_client_id,
        "token_use": "access",
        "iat": int(time.time()),
        "exp": int(time.time()) + 3600,
    }
    claims.update(changes)
    return jwt.encode(claims, pem(key), algorithm="RS256", headers={"kid": "test-key"})


@pytest.fixture(autouse=True)
def _offline_keys(monkeypatch: pytest.MonkeyPatch) -> None:
    # The fetcher would call Cognito's JWKS URL. Hand it our public key instead.
    auth.jwks_client.cache_clear()
    monkeypatch.setattr(PyJWKClient, "get_signing_key_from_jwt", lambda self, tok: PUBLIC_JWK)


def test_valid_token_gives_the_user_id() -> None:
    assert verify_access_token(token(), TEST_SETTINGS) == "user-a"


def test_get_user_reads_the_bearer_header() -> None:
    minted = token()

    user = get_user(TEST_SETTINGS, authorization=f"Bearer {minted}")

    assert user.id == "user-a"
    assert user.token == minted  # forwarded to the Harness as is


@pytest.mark.parametrize(
    "bad",
    [
        pytest.param(token(exp=int(time.time()) - 10), id="expired"),
        pytest.param(token(iss=f"{TEST_SETTINGS.cognito_issuer}X"), id="other pool"),
        pytest.param(token(token_use="id"), id="id token, not access"),  # noqa: S106
        pytest.param(token(client_id="someoneelse"), id="another app client"),
        pytest.param(token(key=OTHER_KEY), id="signed by another key"),
        pytest.param("not.a.jwt", id="garbage"),
    ],
)
def test_bad_tokens_are_401(bad: str) -> None:
    with pytest.raises(HTTPException) as refused:
        verify_access_token(bad, TEST_SETTINGS)

    assert refused.value.status_code == 401
    assert refused.value.headers == {"WWW-Authenticate": "Bearer"}
    # The reason stays in the log; the caller only hears "sign in".
    assert refused.value.detail == "Sign in to continue."


@pytest.mark.parametrize("header", [None, "", "Bearer", "Basic abc", "Token x"])
def test_missing_or_wrong_scheme_is_401(header: str | None) -> None:
    with pytest.raises(HTTPException) as refused:
        get_user(TEST_SETTINGS, authorization=header)

    assert refused.value.status_code == 401
