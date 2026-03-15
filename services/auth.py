from __future__ import annotations

import json
import os
import secrets
import time
from hashlib import pbkdf2_hmac
from typing import Dict, Optional, Tuple

from config import USERS_DB_PATH

TOKEN_TTL_SECONDS = int(os.getenv("AUTH_TOKEN_TTL_SECONDS", "604800"))
PBKDF2_ITERATIONS = int(os.getenv("AUTH_PBKDF2_ITERATIONS", "200000"))

_tokens: Dict[str, Dict[str, float | str]] = {}


def _hash_password(password: str, salt_hex: str) -> str:
    return pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        bytes.fromhex(salt_hex),
        PBKDF2_ITERATIONS,
    ).hex()


def _load_users() -> Dict[str, Dict[str, str]]:
    if not USERS_DB_PATH.exists():
        USERS_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        USERS_DB_PATH.write_text("{}", encoding="utf-8")
        return {}
    try:
        raw = USERS_DB_PATH.read_text(encoding="utf-8")
        data = json.loads(raw or "{}")
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _save_users(users: Dict[str, Dict[str, str]]) -> None:
    USERS_DB_PATH.write_text(json.dumps(users, indent=2), encoding="utf-8")


def validate_credentials(username: str, password: str) -> Optional[str]:
    uname = (username or "").strip()
    pwd = password or ""
    if len(uname) < 3:
        return "username_too_short"
    if len(uname) > 40:
        return "username_too_long"
    if len(pwd) < 8:
        return "password_too_short"
    if len(pwd) > 128:
        return "password_too_long"
    return None


def create_user(username: str, password: str) -> Tuple[Optional[Dict[str, str]], Optional[str]]:
    error = validate_credentials(username, password)
    if error:
        return None, error

    uname = username.strip()
    users = _load_users()
    if uname in users:
        return None, "user_exists"

    salt_hex = secrets.token_hex(16)
    pwd_hash = _hash_password(password, salt_hex)
    users[uname] = {"salt": salt_hex, "hash": pwd_hash}
    _save_users(users)
    return {"username": uname}, None


def verify_user(username: str, password: str) -> bool:
    users = _load_users()
    record = users.get((username or "").strip())
    if not record:
        return False
    salt_hex = record.get("salt", "")
    expected = record.get("hash", "")
    if not salt_hex or not expected:
        return False
    return _hash_password(password, salt_hex) == expected


def change_password(username: str, current_password: str, new_password: str) -> Optional[str]:
    if not verify_user(username, current_password):
        return "invalid_credentials"
    error = validate_credentials(username, new_password)
    if error and error != "username_too_short" and error != "username_too_long":
        return error
    users = _load_users()
    record = users.get(username)
    if not record:
        return "invalid_credentials"
    salt_hex = secrets.token_hex(16)
    pwd_hash = _hash_password(new_password, salt_hex)
    users[username] = {"salt": salt_hex, "hash": pwd_hash}
    _save_users(users)
    return None


def issue_token(username: str) -> str:
    token = secrets.token_urlsafe(32)
    _tokens[token] = {
        "username": username,
        "expires_at": time.time() + TOKEN_TTL_SECONDS,
    }
    return token


def get_user_from_token(token: Optional[str]) -> Optional[str]:
    if not token:
        return None
    record = _tokens.get(token)
    if not record:
        return None
    expires_at = record.get("expires_at", 0)
    if expires_at and expires_at < time.time():
        _tokens.pop(token, None)
        return None
    return record.get("username")
