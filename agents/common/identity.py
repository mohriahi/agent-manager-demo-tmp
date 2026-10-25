"""Each agent's own identity, issued by Agent Manager: a client id and secret
for the identity provider of its environment. An agent trades them for a
signed token; the agent it calls checks that token before it does anything.
Agent Manager can revoke an identity at any time."""
import os

import httpx
import jwt

ISSUER = os.environ["IDP_URL"]
CLIENT_ID = os.environ.get("AGENT_CLIENT_ID", "")
_keys = jwt.PyJWKClient(ISSUER + "/oauth2/jwks")


class Refused(Exception):
    """A call without a valid identity."""


def token():
    """A fresh token for this agent, one per call, so a revoked identity stops at once."""
    try:
        reply = httpx.post(ISSUER + "/oauth2/token", data={"grant_type": "client_credentials"},
                           auth=(CLIENT_ID, os.environ.get("AGENT_CLIENT_SECRET", "")), timeout=10)
    except httpx.HTTPError as exc:
        raise Refused("Agent Manager's identity provider did not answer: %s" % exc)
    if reply.status_code != 200:
        raise Refused("Agent Manager gave this agent no token: its identity was revoked.")
    return reply.json()["access_token"]


def callers():
    """The agents allowed to call this one, as name:client-id pairs."""
    pairs = [pair.split(":", 1) for pair in os.environ.get("ALLOWED_CALLERS", "").split(",") if ":" in pair]
    return {client_id: name for name, client_id in pairs}


def check(authorization):
    """Who is calling: the name and client id of an agent allowed to, with a valid token."""
    if not authorization.startswith("Bearer "):
        raise Refused("No identity: only agents registered in Agent Manager may call this agent.")
    bearer = authorization[len("Bearer "):]
    try:
        claims = jwt.decode(bearer, _keys.get_signing_key_from_jwt(bearer).key, algorithms=["RS256"],
                            issuer=ISSUER, options={"verify_aud": False})
    except jwt.PyJWTError as exc:
        raise Refused("The caller's identity does not check out: %s." % exc)
    allowed = callers()
    if claims.get("client_id") not in allowed:
        raise Refused("This agent does not take requests from that caller.")
    return {"caller": allowed[claims["client_id"]], "clientId": claims["client_id"], "issuer": claims["iss"]}
