"""Each agent's own identity, issued by Agent Manager: a client id and secret
for the identity provider of its environment. Agent Manager hands them to the
agents it runs; the agents that run elsewhere get them from ./run.sh, under
the same names. An agent trades them for a signed token; the agent it calls
checks that token before it does anything."""
import os

import httpx
import jwt

TOKEN_URL = os.environ["AMP_AGENTID_TOKEN_ENDPOINT"]
CLIENT_ID = os.environ.get("AMP_AGENTID_CLIENT_ID", "")
_keys = jwt.PyJWKClient(TOKEN_URL.replace("/oauth2/token", "/oauth2/jwks"))


class Refused(Exception):
    """A call without a valid identity."""


def token():
    """A fresh token for this agent, one per call, so a revoked identity stops at once."""
    try:
        reply = httpx.post(TOKEN_URL, data={"grant_type": "client_credentials"},
                           auth=(CLIENT_ID, os.environ.get("AMP_AGENTID_CLIENT_SECRET", "")), timeout=10)
    except httpx.HTTPError as exc:
        raise Refused("Agent Manager's identity provider did not answer: %s" % exc)
    if reply.status_code != 200:
        raise Refused("Agent Manager gave this agent no token: its identity was revoked.")
    return reply.json()["access_token"]


def callers():
    """The agents allowed to call this one, as name:client-id pairs. None in a
    test environment, where Agent Manager's own key check is enough."""
    pairs = [pair.split(":", 1) for pair in os.environ.get("ALLOWED_CALLERS", "").split(",") if ":" in pair]
    return {client_id: name for name, client_id in pairs}


def check(authorization):
    """Who is calling: the name and client id of an agent allowed to, with a valid token."""
    allowed = callers()
    if not allowed:
        return {"caller": "a tester"}
    if not authorization.startswith("Bearer "):
        raise Refused("No identity: only agents registered in Agent Manager may call this agent.")
    bearer = authorization[len("Bearer "):]
    try:
        claims = jwt.decode(bearer, _keys.get_signing_key_from_jwt(bearer).key, algorithms=["RS256"],
                            options={"verify_aud": False})
    except jwt.PyJWTError as exc:
        raise Refused("The caller's identity does not check out: %s." % exc)
    if claims.get("client_id") not in allowed:
        raise Refused("This agent does not take requests from that caller.")
    return {"caller": allowed[claims["client_id"]], "clientId": claims["client_id"], "issuer": claims["iss"]}
