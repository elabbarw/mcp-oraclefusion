"""
Oracle Fusion JWT token signing for API Authentication.

Generates short-lived JWTs signed with an RSA private key. Oracle validates
the signature against the public certificate registered in Security Console ->
API Authentication, then maps the ``prn`` claim to an Oracle user.

JWT structure Oracle expects:
  Header:  {"alg": "RS256", "typ": "JWT", "x5t": "<SHA-1 thumbprint>"}
  Payload: {"iss": "<trusted issuer>", "prn": "<oracle username>", "iat": ..., "exp": ...}

Used in both HTTP server mode (Entra JWT flow) and STDIO mode when
ORACLE_JWT_* env vars are configured.
"""

import base64
import hashlib
import logging
import time
from functools import lru_cache
from typing import Optional

from cryptography import x509
from cryptography.hazmat.primitives import serialization
from jose import jwt

from ..config.settings import get_settings

logger = logging.getLogger(__name__)


class OracleJWTSigner:
    """Signs Oracle-compatible JWTs using an RSA private key."""

    def __init__(
        self,
        private_key_pem: str,
        x5t_thumbprint: str,
        issuer: str,
    ):
        self._private_key_pem = private_key_pem
        self._x5t = x5t_thumbprint
        self._issuer = issuer

    def sign(self, oracle_username: str, lifetime_seconds: int = 300) -> str:
        """Create a signed JWT for the given Oracle user."""
        now = int(time.time())
        payload = {
            "iss": self._issuer,
            "prn": oracle_username,
            "iat": now,
            "exp": now + lifetime_seconds,
        }
        headers = {
            "alg": "RS256",
            "typ": "JWT",
            "x5t": self._x5t,
        }
        token = jwt.encode(
            payload,
            self._private_key_pem,
            algorithm="RS256",
            headers=headers,
        )
        return token


def _normalize_pem(raw: str) -> str:
    """Normalize a PEM private key from various env var delivery formats."""
    if "\n" in raw and raw.strip().startswith("-----BEGIN"):
        try:
            serialization.load_pem_private_key(raw.encode(), password=None)
            return raw
        except Exception:
            pass

    normalized = raw.replace("\\n", "\n")

    try:
        serialization.load_pem_private_key(normalized.encode(), password=None)
        return normalized
    except Exception:
        pass

    lines = normalized.replace("\r", "").split("\n")
    header = lines[0].strip() if lines else ""
    footer = lines[-1].strip() if lines else ""
    if not header.startswith("-----BEGIN"):
        header = "-----BEGIN PRIVATE KEY-----"
    if not footer.startswith("-----END"):
        footer = "-----END PRIVATE KEY-----"
    b64 = "".join(
        line.strip() for line in lines
        if line.strip() and not line.strip().startswith("-----")
    )
    rewrapped = header + "\n"
    for i in range(0, len(b64), 64):
        rewrapped += b64[i:i + 64] + "\n"
    rewrapped += footer + "\n"
    return rewrapped


def _compute_x5t(cert_pem: bytes) -> str:
    """Compute the base64-encoded SHA-1 thumbprint of an X.509 certificate."""
    cert = x509.load_pem_x509_certificate(cert_pem)
    sha1 = hashlib.sha1(cert.public_bytes(serialization.Encoding.DER)).digest()
    return base64.b64encode(sha1).decode("ascii")


@lru_cache()
def get_oracle_jwt_signer() -> Optional[OracleJWTSigner]:
    """Load the Oracle JWT signer from settings. Returns None if not configured."""
    settings = get_settings()
    inline_key = getattr(settings, "ORACLE_JWT_PRIVATE_KEY", None)
    key_path = getattr(settings, "ORACLE_JWT_PRIVATE_KEY_PATH", None)
    cert_path = getattr(settings, "ORACLE_JWT_CERT_PATH", None)
    issuer = getattr(settings, "ORACLE_JWT_ISSUER", None)

    if not (inline_key or key_path) or not cert_path or not issuer:
        logger.info("Oracle JWT auth not configured. Using Basic Auth fallback.")
        return None

    try:
        if inline_key:
            private_key_pem = _normalize_pem(inline_key)
        else:
            with open(key_path, "rb") as f:
                private_key_pem = f.read().decode("utf-8")

        private_key_obj = serialization.load_pem_private_key(
            private_key_pem.encode(), password=None,
        )

        with open(cert_path, "rb") as f:
            cert_pem = f.read()

        cert = x509.load_pem_x509_certificate(cert_pem)
        pub_from_key = private_key_obj.public_key().public_bytes(
            serialization.Encoding.PEM,
            serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        pub_from_cert = cert.public_key().public_bytes(
            serialization.Encoding.PEM,
            serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        if pub_from_key != pub_from_cert:
            logger.error("Oracle JWT key pair mismatch: private key does not match certificate.")
            return None

        x5t = _compute_x5t(cert_pem)
        return OracleJWTSigner(private_key_pem, x5t, issuer)

    except FileNotFoundError as e:
        logger.error("Oracle JWT cert file not found: %s", e)
        return None
    except Exception as e:
        logger.error("Failed to load Oracle JWT signer: %s", e, exc_info=True)
        return None
