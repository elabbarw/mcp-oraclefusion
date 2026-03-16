"""
Entra ID authentication module.

ValidatedUser is used as the session type throughout the tool handlers.
EntraAuthenticator is only needed for the HTTP/OAuth server mode.
"""

import base64
import json
import logging
import time
from typing import Optional, Dict, Any, List
from jose import jwt
import httpx

from ..config.settings import get_settings

logger = logging.getLogger(__name__)


class TokenExpiredException(Exception):
    """Exception raised when a token has expired"""
    def __init__(self, exp_timestamp: int):
        self.exp_timestamp = exp_timestamp
        super().__init__(f"Token has expired at: {exp_timestamp}")


class ValidatedUser:
    """Validated user information from an identity token or STDIO credentials."""

    def __init__(self, **data):
        self.sub: str = data.get('sub') or data.get('oid', '')
        self.email: str = data.get('mail') or data.get('email') or data.get('preferred_username') or data.get('upn', '')
        self.name: str = data.get('name') or self._build_name(data)
        self.upn: Optional[str] = data.get('upn') or data.get('preferred_username')
        self.groups: List[str] = data.get('groups', [])
        self.iat: int = data.get('iat', 0)
        self.exp: int = data.get('exp', 0)

    def _build_name(self, data: Dict[str, Any]) -> str:
        """Build name from available claims"""
        if data.get('given_name') and data.get('family_name'):
            return f"{data['given_name']} {data['family_name']}"
        return data.get('preferred_username') or data.get('email', '')

    def has_permission(self, required_groups: List[str]) -> bool:
        """Check if user has any of the required groups"""
        if not required_groups:
            return True
        return any(group in self.groups for group in required_groups)

    def is_admin(self) -> bool:
        """Any authenticated user with a valid token is authorized."""
        return True

    def is_oracle_user(self) -> bool:
        """Any authenticated user is an Oracle user."""
        return True


class EntraAuthenticator:
    """Entra ID token validator. Only needed for the HTTP/OAuth server mode."""

    JWKS_CACHE_TTL = 86400  # 24 hours

    def __init__(self):
        self.settings = get_settings()
        self._jwks_cache: Optional[Dict[str, Any]] = None
        self._jwks_fetched_at: float = 0

    async def validate_token(self, token: str) -> Optional[ValidatedUser]:
        """Validate an Entra ID Bearer token."""
        try:
            if not token or not token.strip():
                logger.error("Empty or undefined token provided")
                return None

            parts = token.split('.')
            if len(parts) != 3:
                logger.error(f"Invalid JWT token format - expected 3 parts, got: {len(parts)}")
                return None

            tenant_id = self.settings.AZURE_AD_TENANT_ID
            v2_issuer = f"https://login.microsoftonline.com/{tenant_id}/v2.0"
            v1_issuer = f"https://sts.windows.net/{tenant_id}/"

            jwks = await self.get_jwks()
            if jwks:
                try:
                    payload = jwt.decode(
                        token,
                        jwks,
                        algorithms=["RS256"],
                        options={
                            "require_exp": True,
                            "require_sub": False,
                            "verify_aud": False,
                            "verify_iss": False,
                        },
                    )
                    user = self._validate_payload(payload, tenant_id, v1_issuer, v2_issuer)
                    if user:
                        logger.info(f"Token validated via JWKS for: {user.email}")
                        return user
                    return None
                except jwt.ExpiredSignatureError:
                    raw = self._decode_jwt_payload(parts[1]) or {}
                    raise TokenExpiredException(raw.get("exp", 0))
                except jwt.JWTError:
                    logger.debug("JWKS signature verification failed, trying userinfo")

            payload = await self._validate_via_userinfo(token, parts[1], tenant_id, v1_issuer, v2_issuer)
            return payload

        except TokenExpiredException:
            raise
        except Exception as e:
            logger.error(f"JWT token validation error: {e}")
            return None

    def _validate_payload(
        self, payload: Dict[str, Any], tenant_id: str,
        v1_issuer: str, v2_issuer: str,
    ) -> Optional[ValidatedUser]:
        token_issuer = payload.get("iss", "")
        valid_issuers = [v2_issuer, v1_issuer]
        if self.settings.ENTRA_ISSUER:
            valid_issuers.append(self.settings.ENTRA_ISSUER)

        if token_issuer not in valid_issuers:
            logger.error(f"Token issuer '{token_issuer}' not from tenant {tenant_id}.")
            return None

        if not payload.get("sub") and not payload.get("oid"):
            logger.error("Token missing required subject claim (sub or oid)")
            return None

        return ValidatedUser(**payload)

    async def _validate_via_userinfo(
        self, token: str, payload_part: str, tenant_id: str,
        v1_issuer: str, v2_issuer: str,
    ) -> Optional[ValidatedUser]:
        raw = self._decode_jwt_payload(payload_part)
        if not raw:
            logger.error("Failed to decode token payload")
            return None

        exp = raw.get("exp", 0)
        if exp and time.time() > exp:
            raise TokenExpiredException(exp)

        token_issuer = raw.get("iss", "")
        valid_issuers = [v2_issuer, v1_issuer]
        if self.settings.ENTRA_ISSUER:
            valid_issuers.append(self.settings.ENTRA_ISSUER)
        if token_issuer not in valid_issuers:
            logger.error(f"Token issuer '{token_issuer}' not from tenant {tenant_id}.")
            return None

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    "https://graph.microsoft.com/oidc/userinfo",
                    headers={"Authorization": f"Bearer {token}"},
                )
                if resp.status_code != 200:
                    logger.error(f"Userinfo validation failed: HTTP {resp.status_code}")
                    return None
                userinfo = resp.json()
        except Exception as e:
            logger.error(f"Userinfo request failed: {e}")
            return None

        merged = {**raw, **userinfo}
        if not merged.get("sub") and not merged.get("oid"):
            logger.error("Token missing subject claim (sub or oid)")
            return None

        return ValidatedUser(**merged)

    def _decode_jwt_payload(self, payload_part: str) -> Optional[Dict[str, Any]]:
        try:
            base64_payload = payload_part.replace('-', '+').replace('_', '/')
            padding_needed = (4 - len(base64_payload) % 4) % 4
            padded = base64_payload + '=' * padding_needed
            decoded = base64.b64decode(padded).decode('utf-8')
            return json.loads(decoded)
        except Exception:
            return None

    async def get_jwks(self) -> Optional[Dict[str, Any]]:
        """Fetch Entra ID JWKS with TTL-based caching."""
        now = time.time()
        if self._jwks_cache and (now - self._jwks_fetched_at) < self.JWKS_CACHE_TTL:
            return self._jwks_cache

        try:
            tenant_id = self.settings.AZURE_AD_TENANT_ID
            jwks_urls = [
                f"https://login.microsoftonline.com/{tenant_id}/discovery/v2.0/keys",
                "https://login.microsoftonline.com/common/discovery/v2.0/keys",
            ]

            all_keys = []
            async with httpx.AsyncClient() as client:
                for url in jwks_urls:
                    try:
                        response = await client.get(url)
                        response.raise_for_status()
                        keys = response.json().get("keys", [])
                        all_keys.extend(keys)
                    except Exception as e:
                        logger.warning(f"Failed to fetch JWKS from {url}: {e}")

            if not all_keys:
                raise Exception("No keys fetched from any JWKS endpoint")

            seen_kids = set()
            unique_keys = []
            for key in all_keys:
                kid = key.get("kid")
                if kid and kid not in seen_kids:
                    seen_kids.add(kid)
                    unique_keys.append(key)

            self._jwks_cache = {"keys": unique_keys}
            self._jwks_fetched_at = now
            return self._jwks_cache

        except Exception as e:
            logger.error(f"Failed to fetch JWKS: {e}")
            if self._jwks_cache:
                return self._jwks_cache
            return None


_authenticator = None


def get_authenticator() -> EntraAuthenticator:
    """Get global authenticator instance"""
    global _authenticator
    if _authenticator is None:
        _authenticator = EntraAuthenticator()
    return _authenticator
