"""Who is asking: the signed-in user, read from a Cognito access token.

The page signs in on Cognito's login page and sends the access token with every
request as `Authorization: Bearer <token>`. This module checks the token, then
hands the routes two things:

    user.id     the `sub` claim: Cognito's permanent id for the person. It is the
                Memory actor id, the S3 folder name and the document label.
    user.token  the raw token, which the chat route forwards to the agent.
                Runtime checks it again itself (its inbound JWT authorizer).

What "checks the token" means, in order (docs/course/, lesson 31):
    1. signature: signed by one of the user pool's public keys (fetched from
       its JWKS URL, cached by PyJWT)
    2. expiry: `exp` is in the future
    3. issuer: `iss` is our user pool, not some other pool
    4. kind: `token_use` is "access" (the id token has the same signer)
    5. app client: `client_id` is our app client, so a token minted for
       another app on the same pool is refused
https://docs.aws.amazon.com/cognito/latest/developerguide/amazon-cognito-user-pools-using-tokens-verifying-a-jwt.html
"""

import logging
from dataclasses import dataclass
from functools import lru_cache
from typing import Annotated

import jwt
from fastapi import Depends, Header, HTTPException, status
from jwt import PyJWKClient, PyJWKClientConnectionError

from app.settings import Settings, get_settings

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class User:
    id: str
    token: str


@lru_cache
def jwks_client(jwks_url: str) -> PyJWKClient:
    # One fetcher per key URL, shared by every request. It caches the keys and
    # refetches when a token names a key id it has not seen (Cognito rotates keys).
    # https://pyjwt.readthedocs.io/en/stable/usage.html#retrieve-rsa-signing-keys-from-a-jwks-endpoint
    return PyJWKClient(jwks_url, cache_keys=True)


def verify_access_token(token: str, settings: Settings) -> str:
    """The user id inside a valid access token. Raises 401 for anything else."""
    try:
        key = jwks_client(settings.cognito_jwks_url).get_signing_key_from_jwt(token)
        claims = jwt.decode(
            token,
            key.key,
            algorithms=["RS256"],
            issuer=settings.cognito_issuer,
            options={"require": ["exp", "iat", "sub", "token_use", "client_id"]},
        )
    except PyJWKClientConnectionError as err:
        # Cognito's key endpoint did not answer: our problem, not the caller's.
        logger.warning("could not fetch Cognito keys error=%s", type(err).__name__)
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE, "Sign-in check unavailable. Try again."
        ) from err
    except jwt.PyJWTError as err:
        raise unauthorized(type(err).__name__) from err
    if claims["token_use"] != "access":  # noqa: S105 (a claim name, not a password)
        raise unauthorized("not an access token")
    if claims["client_id"] != settings.cognito_client_id:
        raise unauthorized("token for another app client")
    return str(claims["sub"])


def unauthorized(reason: str) -> HTTPException:
    # The reason goes to the log only. The caller learns just "sign in again".
    logger.info("request refused reason=%s", reason)
    return HTTPException(
        status.HTTP_401_UNAUTHORIZED,
        "Sign in to continue.",
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_user(
    settings: Annotated[Settings, Depends(get_settings)],
    authorization: Annotated[str | None, Header()] = None,
) -> User:
    # The parameter name `authorization` is read from the "Authorization" header.
    # https://fastapi.tiangolo.com/tutorial/header-params/
    scheme, _, token = (authorization or "").partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise unauthorized("no bearer token")
    return User(id=verify_access_token(token, settings), token=token)


def get_user_id(user: Annotated[User, Depends(get_user)]) -> str:
    return user.id
