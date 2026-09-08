"""
Minimal OAuth 2.1 authorization-server provider for the TheCloudMind MCP server.

Turns the MCP server into a proper OAuth-gated connector (like Claude's built-in
connectors): Claude dynamically registers a client, redirects the user to a
login page, and exchanges an authorization code (PKCE) for a bearer token.

The MCP SDK supplies all the HTTP plumbing — metadata discovery, /authorize,
/token, /register, /revoke handlers, PKCE verification, and the bearer-auth
middleware that protects /mcp. This module only provides the storage + the
single-password login gate.

Storage is in-memory: tokens/clients reset on container restart, which just
means clients re-authorize. Fine for a single-instance connector.
"""

from __future__ import annotations

import html
import secrets
import time
from typing import Optional

from mcp.server.auth.provider import (
    AccessToken,
    AuthorizationCode,
    AuthorizationParams,
    OAuthAuthorizationServerProvider,
    RefreshToken,
    construct_redirect_uri,
)
from mcp.server.auth.settings import (
    AuthSettings,
    ClientRegistrationOptions,
    RevocationOptions,
)
from mcp.shared.auth import OAuthClientInformationFull, OAuthToken

_AUTH_CODE_TTL = 600          # 10 min
_ACCESS_TOKEN_TTL = 3600      # 1 h


class TCMOAuthProvider(OAuthAuthorizationServerProvider):
    """In-memory OAuth provider gated by a single shared password."""

    def __init__(self, issuer_url: str, password: str) -> None:
        self._issuer = issuer_url.rstrip("/")
        self._password = password
        self._clients: dict[str, OAuthClientInformationFull] = {}
        self._auth_codes: dict[str, AuthorizationCode] = {}
        self._access_tokens: dict[str, AccessToken] = {}
        self._refresh_tokens: dict[str, RefreshToken] = {}
        # rid -> (client, params) parked while the user completes the login page
        self._pending: dict[str, tuple[OAuthClientInformationFull, AuthorizationParams]] = {}

    # ── Client registration (Dynamic Client Registration) ──────────────────
    async def get_client(self, client_id: str) -> Optional[OAuthClientInformationFull]:
        return self._clients.get(client_id)

    async def register_client(self, client_info: OAuthClientInformationFull) -> None:
        self._clients[client_info.client_id] = client_info

    # ── Authorization: hand off to the login page ──────────────────────────
    async def authorize(self, client: OAuthClientInformationFull, params: AuthorizationParams) -> str:
        rid = secrets.token_urlsafe(24)
        self._pending[rid] = (client, params)
        return f"{self._issuer}/login?rid={rid}"

    def complete_login(self, rid: str) -> Optional[str]:
        """Called by the /login POST handler after the password checks out.
        Mints an auth code and returns the redirect URL back to the client."""
        entry = self._pending.pop(rid, None)
        if entry is None:
            return None
        client, params = entry
        code = secrets.token_urlsafe(32)
        self._auth_codes[code] = AuthorizationCode(
            code=code,
            scopes=params.scopes or [],
            expires_at=time.time() + _AUTH_CODE_TTL,
            client_id=client.client_id,
            code_challenge=params.code_challenge,
            redirect_uri=params.redirect_uri,
            redirect_uri_provided_explicitly=params.redirect_uri_provided_explicitly,
            resource=params.resource,
            subject="owner",
        )
        redirect_params: dict[str, str] = {"code": code}
        if params.state is not None:
            redirect_params["state"] = params.state
        return construct_redirect_uri(str(params.redirect_uri), **redirect_params)

    def check_password(self, password: str) -> bool:
        return secrets.compare_digest(password or "", self._password)

    # ── Authorization code → tokens ─────────────────────────────────────────
    async def load_authorization_code(
        self, client: OAuthClientInformationFull, authorization_code: str
    ) -> Optional[AuthorizationCode]:
        ac = self._auth_codes.get(authorization_code)
        if ac is None or ac.client_id != client.client_id:
            return None
        if ac.expires_at < time.time():
            self._auth_codes.pop(authorization_code, None)
            return None
        return ac

    async def exchange_authorization_code(
        self, client: OAuthClientInformationFull, authorization_code: AuthorizationCode
    ) -> OAuthToken:
        self._auth_codes.pop(authorization_code.code, None)  # one-time use
        return self._issue_tokens(client.client_id, authorization_code.scopes, authorization_code.resource)

    # ── Refresh ──────────────────────────────────────────────────────────────
    async def load_refresh_token(
        self, client: OAuthClientInformationFull, refresh_token: str
    ) -> Optional[RefreshToken]:
        rt = self._refresh_tokens.get(refresh_token)
        if rt is None or rt.client_id != client.client_id:
            return None
        return rt

    async def exchange_refresh_token(
        self,
        client: OAuthClientInformationFull,
        refresh_token: RefreshToken,
        scopes: list[str],
    ) -> OAuthToken:
        # Rotate: drop the old refresh token, issue a fresh pair.
        self._refresh_tokens.pop(refresh_token.token, None)
        granted = scopes or refresh_token.scopes
        return self._issue_tokens(client.client_id, granted, refresh_token.resource)

    # ── Access token validation (used by the bearer middleware on /mcp) ─────
    async def load_access_token(self, token: str) -> Optional[AccessToken]:
        at = self._access_tokens.get(token)
        if at is None:
            return None
        if at.expires_at is not None and at.expires_at < time.time():
            self._access_tokens.pop(token, None)
            return None
        return at

    async def revoke_token(self, token) -> None:
        value = getattr(token, "token", None)
        if value:
            self._access_tokens.pop(value, None)
            self._refresh_tokens.pop(value, None)

    # ── helpers ──────────────────────────────────────────────────────────────
    def _issue_tokens(self, client_id: str, scopes: list[str], resource) -> OAuthToken:
        access = secrets.token_urlsafe(32)
        refresh = secrets.token_urlsafe(32)
        now = time.time()
        self._access_tokens[access] = AccessToken(
            token=access,
            client_id=client_id,
            scopes=scopes,
            expires_at=int(now + _ACCESS_TOKEN_TTL),
            resource=resource,
        )
        self._refresh_tokens[refresh] = RefreshToken(
            token=refresh,
            client_id=client_id,
            scopes=scopes,
            expires_at=None,
            resource=resource,
        )
        return OAuthToken(
            access_token=access,
            token_type="Bearer",
            expires_in=_ACCESS_TOKEN_TTL,
            refresh_token=refresh,
            scope=" ".join(scopes) if scopes else None,
        )


def build_auth_settings(issuer_url: str) -> AuthSettings:
    return AuthSettings(
        issuer_url=issuer_url,
        resource_server_url=f"{issuer_url.rstrip('/')}/mcp",
        client_registration_options=ClientRegistrationOptions(enabled=True),
        revocation_options=RevocationOptions(enabled=True),
        required_scopes=[],
        # Our provider stores tokens itself and doesn't do per-resource audience
        # checks; disable the SDK's resource-audience enforcement.
        validate_token_resource=False,
    )


# ── Login page ───────────────────────────────────────────────────────────────
_LOGIN_HTML = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Connect to TheCloudMind</title>
<style>
  body{{font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;background:#0f172a;
    color:#e2e8f0;display:flex;min-height:100vh;align-items:center;justify-content:center;margin:0}}
  .card{{background:#1e293b;padding:2rem 2.25rem;border-radius:16px;width:320px;
    box-shadow:0 10px 40px rgba(0,0,0,.4)}}
  h1{{font-size:1.15rem;margin:0 0 .35rem}} p{{color:#94a3b8;font-size:.85rem;margin:0 0 1.25rem}}
  label{{font-size:.8rem;color:#cbd5e1}} input{{width:100%;box-sizing:border-box;margin-top:.35rem;
    padding:.6rem .7rem;border-radius:9px;border:1px solid #334155;background:#0f172a;color:#e2e8f0;font-size:.95rem}}
  button{{width:100%;margin-top:1.1rem;padding:.65rem;border:0;border-radius:9px;background:#6366f1;
    color:#fff;font-weight:600;font-size:.95rem;cursor:pointer}} button:hover{{background:#4f46e5}}
  .err{{color:#f87171;font-size:.8rem;margin-top:.75rem;{err_display}}}
</style></head><body>
<form class="card" method="post" action="/login">
  <h1>Connect to TheCloudMind</h1>
  <p>Authorize Claude to access TheCloudMind.ai news &amp; jobs (read-only).</p>
  <input type="hidden" name="rid" value="{rid}">
  <label>Access password</label>
  <input type="password" name="password" autofocus required>
  <div class="err">Incorrect password. Try again.</div>
  <button type="submit">Authorize</button>
</form></body></html>"""


def render_login(rid: str, error: bool = False) -> str:
    return _LOGIN_HTML.format(
        rid=html.escape(rid),
        err_display="" if error else "display:none",
    )
