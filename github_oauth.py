# Copyright (C) 2026 Collabora Limited
# Author: Denys Fedoryshchenko <denys.f@collabora.com>
# SPDX-License-Identifier: LGPL-2.1-or-later

"""
GitHub OAuth login flow helpers.

Access is restricted to members of a GitHub team (by default the
"staging" team of the "kernelci" org, overridable via the
[github_oauth] section in staging.toml).
"""

import secrets
from typing import Optional
from urllib.parse import urlencode

import httpx

from config import (
    GITHUB_OAUTH_CLIENT_ID,
    GITHUB_OAUTH_CLIENT_SECRET,
    GITHUB_OAUTH_ORG,
    GITHUB_OAUTH_TEAM,
)

GITHUB_AUTHORIZE_URL = "https://github.com/login/oauth/authorize"
GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"
GITHUB_API_URL = "https://api.github.com"

# read:org is required to verify team membership with the user's token
OAUTH_SCOPES = "read:user user:email read:org"

OAUTH_STATE_COOKIE = "oauth_state"


def generate_state() -> str:
    return secrets.token_urlsafe(32)


def validate_state(state: Optional[str], cookie_state: Optional[str]) -> bool:
    if not state or not cookie_state:
        return False
    return secrets.compare_digest(state, cookie_state)


def build_authorize_url(state: str) -> str:
    params = urlencode(
        {
            "client_id": GITHUB_OAUTH_CLIENT_ID,
            "scope": OAUTH_SCOPES,
            "state": state,
        }
    )
    return f"{GITHUB_AUTHORIZE_URL}?{params}"


async def exchange_code(code: str) -> Optional[str]:
    """Exchange the OAuth authorization code for a user access token"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            GITHUB_TOKEN_URL,
            data={
                "client_id": GITHUB_OAUTH_CLIENT_ID,
                "client_secret": GITHUB_OAUTH_CLIENT_SECRET,
                "code": code,
            },
            headers={"Accept": "application/json"},
        )
    if response.status_code != 200:
        return None
    return response.json().get("access_token")


def _auth_headers(token: str) -> dict:
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
    }


async def fetch_github_user(token: str) -> Optional[dict]:
    """Fetch the authenticated GitHub user profile"""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{GITHUB_API_URL}/user", headers=_auth_headers(token)
        )
    if response.status_code != 200:
        return None
    return response.json()


async def fetch_primary_email(token: str) -> Optional[str]:
    """Fetch the user's primary email (the profile email may be private)"""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{GITHUB_API_URL}/user/emails", headers=_auth_headers(token)
        )
    if response.status_code != 200:
        return None
    for entry in response.json():
        if entry.get("primary"):
            return entry.get("email")
    return None


async def is_team_member(token: str, login: str) -> bool:
    """
    Check that the user is an active member of the configured org team.

    Uses the user's own token: team members are allowed to query their
    own membership, non-members get a 404.
    """
    url = (
        f"{GITHUB_API_URL}/orgs/{GITHUB_OAUTH_ORG}"
        f"/teams/{GITHUB_OAUTH_TEAM}/memberships/{login}"
    )
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=_auth_headers(token))
    if response.status_code != 200:
        return False
    return response.json().get("state") == "active"
